#!/bin/sh

BUILDOUT_URL=https://github.com/liqd/adhocracy.buildout
SERVICE_TEMPLATE=build_debian_scripts/init.d__adhocracy_services.sh.template
SERVICE_TEMPLATE_URL=https://raw.github.com/liqd/adhocracy.buildout/master/$SERVICE_TEMPLATE
TEST_PORT_FREE_URL=https://raw.github.com/liqd/adhocracy.buildout/master/build_debian_scripts/test-port-free.py
SUPERVISOR_PORTS="5005 5006 5010"
ADHOCRACY_PORT=5001

set -e

usage()
{
cat << EOF
usage: $0 [options]

Install adhocracy on debian.

OPTIONS:
   -h      Show this message
   -D      Install a DNS server to answer *.adhocracy.lan
   -p      Install a postgresSQL server
   -m      Install a MySQL server
   -M      Install MySQL client libraries
   -c file Use the given buildout config file
   -A      Do not start now
   -S      Do not configure system services
   -s      Install only non-superuser parts
   -u      Install only superuser parts
   -U	   Set the username adhocracy should run as
   -b      Branch to check out
EOF
}

use_postgres=false
use_mysql=false
install_geo=false
buildout_cfg_file=
modify_dns=false
autostart=true
setup_services=true
not_use_sudo_commands=false
not_use_user_commands=false
adhoc_user=$USER
install_mysql_client=false
branch=develop

if [ -n "$SUDO_USER" ]; then
	adhoc_user=$SUDO_USER
fi

while getopts DpMmASsuc:U:b: name
do
    case $name in
    D)    modify_dns=true;;
    p)    use_postgres=true;;
    m)    use_mysql=true;;
    M)    install_mysql_client=true;;
    A)    autostart=false;;
    S)    setup_services=false;;
    s)    not_use_sudo_commands=true;;
    u)    not_use_user_commands=true;;
    U)	  adhoc_user=$OPTARG;;
    c)    buildout_cfg_file=$OPTARG;;
    b)    branch=$OPTARG;;
    ?)    usage
          exit 2;;
    esac
done


if $use_postgres && $use_mysql; then
	echo 'Cannot use Postgres AND MySQL.'
	exit 3
fi

if [ "${PWD#*/adhocracy_buildout}" != "$PWD" ]; then
	echo "You should not run build_debian.sh from the adhocracy_buildout directory. Instead, run it from the directory which contains adhocracy_buildout."
	exit 34
fi


if [ -n "$buildout_cfg_file" ]; then
	if $use_postgres || $use_mysql; then
		echo "Buildout config file precludes the -p and -m option"
		exit 33
	fi
	buildout_cfg_file=$(readlink -f "$buildout_cfg_file")
elif $use_postgres; then
	buildout_cfg_file=buildout_development_postgres.cfg
elif $use_mysql; then
	buildout_cfg_file=buildout_development_mysql.cfg
	MYSQL_ROOTPW="sqlrootpw"
else
	buildout_cfg_file=buildout_development.cfg
fi


if ! $not_use_sudo_commands; then
	SUDO_CMD=sudo
	if [ "$(id -u)" -eq 0 ]; then
		SUDO_CMD=
	fi
	if ! $SUDO_CMD true ; then
		echo 'sudo failed. Is it installed and configured?'
		exit 20
	fi

	$SUDO_CMD apt-get install -yqq libpng-dev libjpeg-dev gcc make build-essential bin86 unzip libpcre3-dev zlib1g-dev git mercurial python python-virtualenv python-dev libsqlite3-dev openjdk-6-jre erlang-dev erlang-mnesia erlang-os-mon xsltproc libapache2-mod-proxy-html libpq-dev
	# Not strictly required, but needed to push to github via ssh
	$SUDO_CMD apt-get install -yqq openssh-client

	if $use_postgres; then
		$SUDO_CMD apt-get install -yqq postgresql postgresql-server-dev-all
		if $install_geo; then
			$SUDO_CMD apt-get install -yqq postgis
		fi
	fi
	if $install_mysql_client; then
        $SUDO_CMD apt-get install -yqq libmysqlclient-dev
	fi
	if $use_mysql; then
		echo "mysql mysql-server/root_password string ${MYSQL_ROOTPW}" | $SUDO_CMD debconf-set-selections
		echo "mysql mysql-server/root_password_again string ${MYSQL_ROOTPW}" | $SUDO_CMD debconf-set-selections
		$SUDO_CMD apt-get install -yqq mysql-server libmysqld-dev python-mysqldb
		$SUDO_CMD sed -i "s%^bind-address.*%\#bind-address = 127.0.0.1\nskip-networking%" /etc/mysql/my.cnf
		$SUDO_CMD /etc/init.d/mysql restart
	fi
	$SUDO_CMD a2enmod proxy proxy_http proxy_html >/dev/null

	if $use_postgres; then
		# Set up postgreSQL
		# Since we're using postgreSQL 8.4 which doesn't have CREATE USER IF NOT EXISTS, we're using the following hack ...
		echo "DROP ROLE IF EXISTS adhocracy; CREATE USER adhocracy PASSWORD 'adhoc';" | $SUDO_CMD su postgres -c 'psql'
		$SUDO_CMD su postgres -c 'createdb adhocracy --owner adhocracy;' || true
		if $install_geo; then
			$SUDO_CMD su postgres -c '
				createlang plpgsql adhocracy;
				psql -d adhocracy -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql  >/dev/null 2>&1;
				psql -d adhocracy -f /usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql  >/dev/null 2>&1;
				psql -d adhocracy -f /usr/share/postgresql/8.4/contrib/postgis_comments.sql >/dev/null 2>&1;'
		fi
	fi

	# This is only executed when sudo-commands are enabled since mysql will only
	# install with sudo-commands.
	if $use_mysql; then
	echo "CREATE DATABASE IF NOT EXISTS adhocracy; \
              GRANT ALL PRIVILEGES ON adhocracy . * TO 'adhocracy'@'localhost' IDENTIFIED BY 'adhoc'; \
              FLUSH PRIVILEGES;" \
          | mysql --user root --password=${MYSQL_ROOTPW}

	fi

	# Set up DNS names
	if $modify_dns; then
		$SUDO_CMD apt-get install -qqy dnsmasq
		/bin/echo -e 'address=/.adhocracy.lan/127.0.0.1\nresolv-file=/etc/dnsmasq.resolv.conf' | $SUDO_CMD tee /etc/dnsmasq.d/adhocracy.lan.conf >/dev/null
		/bin/echo -e 'nameserver 8.8.8.8\nnameserver 8.8.4.4\n' | $SUDO_CMD tee /etc/dnsmasq.resolv.conf >/dev/null
		$SUDO_CMD sed -i 's/^#IGNORE_RESOLVCONF=yes$/IGNORE_RESOLVCONF=yes/' /etc/default/dnsmasq >/dev/null
		# This is hack-ish, but it works no matter how exotic the configuration is
		if $SUDO_CMD test -w /etc/resolv.conf; then
			echo 'nameserver 127.0.0.1' | $SUDO_CMD tee /etc/resolv.conf >/dev/null
			$SUDO_CMD chattr +i /etc/resolv.conf
		fi
		$SUDO_CMD /etc/init.d/dnsmasq restart
	else
		if ! grep -q adhocracy.lan /etc/hosts; then
			$SUDO_CMD sh -c 'echo 127.0.0.1 adhocracy.lan test.adhocracy.lan >> /etc/hosts'
		fi
	fi

	if $setup_services; then
		if [ "$adhoc_user" = "root" ]; then
			echo "You are root. Please use the -U flag to set the user adhocracy should be running as"
			exit 35
		fi

        if [ -r "adhocracy_buildout/adhocracy.buildout/${SERVICE_TEMPLATE}" ]; then
            stmpl=$(cat "adhocracy_buildout/adhocracy.buildout/${SERVICE_TEMPLATE}")
        else
            stmpl=$(wget $SERVICE_TEMPLATE_URL -O- -nv)
        fi
		echo "$stmpl" | \
			sed -e "s#%%USER%%#$adhoc_user#" -e "s#%%DIR%%#$(readlink -f .)/adhocracy_buildout#" | \
			$SUDO_CMD tee /etc/init.d/adhocracy_services >/dev/null

		$SUDO_CMD chmod a+x /etc/init.d/adhocracy_services
		$SUDO_CMD update-rc.d adhocracy_services defaults >/dev/null
	fi
fi


if $not_use_user_commands; then
	exit 0
fi


if [ "$(id -u)" -eq 0 ]; then
	echo "You should not install adhocracy as a root user"
	exit 33
fi

# Create buildout directory
if ! mkdir -p adhocracy_buildout; then
	echo 'Cannot create adhocracy_buildout directory. Please change to a directory where you can create files.'
	exit 21
fi

# Directory buildout was not created
if [ '!' -w adhocracy_buildout ]; then
	echo 'Cannot write to adhocracy_buildout directory. Change to another directory, remove adhocracy_buildout, or run as another user'
	exit 22
fi
if [ -x adhocracy_buildout/bin/supervisorctl ]; then
	adhocracy_buildout/bin/supervisorctl shutdown >/dev/null || true
fi

test_port_free_tmp=$(mktemp)
if [ '!' -e ./test-port-free.py ]; then
	if ! wget -q $TEST_PORT_FREE_URL -O $test_port_free_tmp; then
        ex=$?
        echo "Download failed. Are you connected to the Internet?"
        exit $ex
    fi
fi
python $test_port_free_tmp -g 10 --kill-pid $ADHOCRACY_PORT $SUPERVISOR_PORTS
rm -f $test_port_free_tmp


virtualenv --distribute --no-site-packages adhocracy_buildout
ORIGINAL_PWD=$(pwd)
cd adhocracy_buildout
if [ -e adhocracy.buildout ]; then
	(cd adhocracy.buildout && git pull --quiet)
else
	git clone --quiet $BUILDOUT_URL adhocracy.buildout
fi
(cd adhocracy.buildout && git checkout $branch > /dev/null)



for f in adhocracy.buildout/*; do ln -sf $f; done
if echo $buildout_cfg_file | grep "^/" -q; then
	tmp_file=$(mktemp --tmpdir=.)
	cp $buildout_cfg_file $tmp_file
	buildout_cfg_file=$tmp_file
fi

. bin/activate

pip install -U distribute >/dev/null

# TODO write buildout file with configurations (sysv_init:user ...) and use that

bin/python bootstrap.py -c ${buildout_cfg_file}
bin/buildout -Nc ${buildout_cfg_file}

if [ -n "$tmp_file" ]; then
	rm "$tmp_file"
fi

ln -sf adhocracy_buildout/adhocracy.buildout/build_debian_scripts/paster_interactive.sh "$ORIGINAL_PWD"


if $autostart; then
	bin/supervisord
	echo "Use adhocracy_buildout/bin/supervisorctl to control running services."

	python adhocracy.buildout/etc/test-port-free.py -o -g 10 ${SUPERVISOR_PORTS}
	if bin/supervisorctl status | grep -vq RUNNING; then
		echo 'Failed to start all services:'
		bin/supervisorctl status
		exit 31
	fi

	pasterOutput=$(bin/paster setup-app etc/adhocracy.ini --name=content)
	if echo "$pasterOutput" | grep -q ERROR; then
		echo "$pasterOutput"
		echo 'Error in paster setup'
		exit 32
	fi

	echo
	echo
	echo "Type  ./paster_interactive.sh  to run the interactive paster daemon."
	echo "Then, navigate to  http://adhocracy.lan:${ADHOCRACY_PORT}/  to see adhocracy!"
	echo "Use the username \"admin\" and password \"password\" to login."
fi
