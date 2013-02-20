#!/bin/sh

# Test adhocracy in a chroot, on a debian(-ish) system
SUPERVISOR_PORTS="5005 5006 5010"

set -e

if [ "$#" -eq 0 ]; then
	chroot_path=./adhocracy-test-chroot
elif [ "$#" -ne 1 ]; then
	chroot_path=$1
	echo "Usage: $0 chroot_path"
	exit 21
fi

if [ "$(id -u)" -ne 0 ]; then
	echo 'You need to be root to run this script.'
	exit 32
fi

apt-get install -yqq debootstrap

if [ '!' -d $chroot_path/proc ]; then
	# Use HHU mirror if available
	MIRROR=
	if wget -q http://mirror.cs.uni-duesseldorf.de/debian/ -O /dev/null; then
		MIRROR=http://mirror.cs.uni-duesseldorf.de/debian
	fi
	debootstrap squeeze $chroot_path $MIRROR
fi

echo adhocracy-chroot > $chroot_path/etc/debian_chroot

# sudo complains if it can't resolve the hostname, suppress that
if ! grep -P -q "\s$(hostname)(?:\s|$)" $chroot_path/etc/hosts; then
	echo 127.0.0.1 $(hostname) >> $chroot_path/etc/hosts
fi


cat >$chroot_path/adhocracy-runtests.sh <<EOF
#!/bin/sh
# This is the test script, run by the user adhocracy

set -e

cd /home/adhocracy/adhocracy_buildout
. bin/activate

# Run nosetest
bin/test

bin/supervisorctl shutdown>/dev/null
python ./adhocracy.buildout/etc/check_port_free.py -g 10 --kill-pid 5001 $SUPERVISOR_PORTS
bin/supervisord
python ./adhocracy.buildout/etc/check_port_free.py -o -g 30 $SUPERVISOR_PORTS # Wait for supervisord to start

# Fail if not all services are marked as running
if bin/supervisorctl status | grep -vq RUNNING; then
	echo "Failed to start all services."
	bin/supervisorctl status
	exit 31
fi

pasterOutput=\$(bin/paster setup-app etc/adhocracy.ini --name=content)
if echo "\$pasterOutput" | grep -q ERROR; then
       echo "\$pasterOutput"
       echo 'Error in paster setup'
       exit 32
fi

bin/paster serve etc/adhocracy.ini &
paster_pid="\$!"

python ./adhocracy.buildout/etc/check_port_free.py -o -g 10 5001

wget -nv -O /dev/null http://adhocracy.lan:5001/

kill "\$paster_pid"
bin/supervisorctl shutdown
EOF
chmod a+x $chroot_path/adhocracy-runtests.sh

cat >$chroot_path/test_in_chroot.sh <<EOF
#!/bin/sh
# Setup this chroot and execute the tests

set -e

if ! mountpoint -q /proc; then
	mount -t proc proc /proc
fi
if ! id -u adhocracy >/dev/null 2>&1; then
	useradd adhocracy --create-home
fi

echo '
Defaults        env_reset
Defaults        mail_badpass
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

root    ALL=(ALL:ALL) ALL

adhocracy ALL=(ALL:ALL) NOPASSWD:ALL
' > /etc/sudoers
chmod 0440 /etc/sudoers

# Configure initial packages for the system
apt-get update -qq
if [ ! -d /usr/lib/locale ]; then
	echo 'locales locales/locales_to_be_generated string de_DE.UTF-8 UTF-8, en_US.UTF-8 UTF-8' | LC_ALL=C debconf-set-selections
	echo 'locales locales/default_environment_locale string en_US' | LC_ALL=C debconf-set-selections
	LC_ALL=C apt-get install -yqq locales
	dpkg-reconfigure --default-priority locales
fi
apt-get install -yqq make sudo ca-certificates
apt-get install -yqq curl

cd /home/adhocracy
su adhocracy -c 'curl -sS https://raw.github.com/liqd/adhocracy.buildout/develop/build.sh -o build.sh && sh build.sh -A -S'

rm -f /etc/sudoers

rev=\$(cd /home/adhocracy/adhocracy_buildout/src/adhocracy/ && git rev-parse HEAD)

if su adhocracy -c '/adhocracy-runtests.sh'; then
	echo "(\$rev) TESTS PASSED, leaving chroot ..."
	rescode=0
else
	rescode=\$?
	echo "(\$rev) TESTS FAILED."
fi

umount /proc
exit "\$rescode"

EOF

chroot $chroot_path sh /test_in_chroot.sh

