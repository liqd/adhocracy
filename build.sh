#!/bin/sh

DEFAULT_BRANCH=develop
GIT_URL=https://github.com/liqd/adhocracy
SERVICE_TEMPLATE=etc/sysv-init.in
SERVICE_TEMPLATE_URL=https://raw.github.com/liqd/adhocracy/$DEFAULT_BRANCH/$SERVICE_TEMPLATE
CHECK_PORT_FREE_URL=https://raw.github.com/liqd/adhocracy/$DEFAULT_BRANCH/scripts/check_port_free.py
SUPERVISOR_PORTS="5005 5006 5010"
ADHOCRACY_PORT=5001

set -e

usage() {
cat << EOF
usage: $0 [options]

Install adhocracy on debian.

OPTIONS:
   -h      Show this message
   -M      Install MySQL client libraries
   -c file Use the given buildout config file
   -A      Do not start now
   -S      Do not configure system services
   -s      Install/Reinstall only non-superuser parts
   -u      Install only superuser parts
   -U      Set the username adhocracy should run as
   -b      Branch to check out
EOF
}

buildout_cfg_file=
autostart=true
setup_services=true
not_use_sudo_commands=false
not_use_user_commands=false
adhoc_user=$USER
install_mysql_client=false
arch_install=false
branch=$DEFAULT_BRANCH

if [ -n "$SUDO_USER" ]; then
    adhoc_user=$SUDO_USER
fi

PKGS_TO_INSTALL=''
PKG_INSTALL_CMD=''

while getopts DpMmASsuc:U:b:R:o name
do
    case $name in
    M)    install_mysql_client=true;;
    A)    autostart=false;;
    S)    setup_services=false;;
    s)    not_use_sudo_commands=true;;
    u)    not_use_user_commands=true;;
    U)    adhoc_user=$OPTARG;;
    c)    buildout_cfg_file=$OPTARG;;
    b)    branch=$OPTARG;;
    ?)    usage
          exit 2;;
    *)    echo "Invalid option $name!"
          usage
          exit 3;;
    esac
done

distro=''

if which apt-get >/dev/null 2>&1 ; then
    distro='debian'
    PYTHON_CMD='python'
    PKG_INSTALL_CMD='apt-get install -yqq'
elif which pacman >/dev/null 2>&1 ; then
    distro='arch'
    PYTHON_CMD='python2'
    PKG_INSTALL_CMD='pacman -S --needed --noconfirm'
elif which yum >/dev/null 2>&1 ; then
    distro='fedora'
    PYTHON_CMD='python'
    PKG_INSTALL_CMD='yum install --assumeyes --quiet'
fi
if [ -z "$distro" ] ; then
    echo "Your OS is currently not supported! Aborting"
    exit 35
fi

ROOTDIR_FROM_CALLER="adhocracy_buildout/"
if [ "$(basename $PWD)" = 'adhocracy_buildout' ]; then
    cd "$(dirname $PWD)"
    ROOTDIR_FROM_CALLER=""
fi

# Abort if we're running from somewhere else inside adhocracy_buildout
if [ "${PWD#*/adhocracy_buildout}" != "$PWD" ]; then
    echo "You should not run build.sh from the adhocracy_buildout directory. Instead, run it from the directory which contains adhocracy_buildout."
    exit 34
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

    if [ '!' -e adhocracy_buildout/bin/adhocracy_interactive.sh ]; then
        # Installation has never completed
        case "$distro" in
        debian)
            $SUDO_CMD apt-get update
            ;;
        esac
    fi
fi

# Prefer curl because wget < 1.14 fails on https://raw.github.com/ because 
# it doesn't support x509v3 alternative names.
if which curl > /dev/null ; then
    downloader_program=curl
else
    if ! $not_use_sudo_commands ; then
        $SUDO_CMD $PKG_INSTALL_CMD curl
        downloader_program=curl
    else
        # Fall back to wget
        wget_version=$(wget --version | head -n 1 | sed 's#[^0-9]*\([0-9][0-9.]*\).*#\1#' || true)
        if test "$wget_version" = "1.12"; then
            echo "WARNING: Old version of wget detected. Downloads from raw.github.com will fail. Install curl!"
        fi
        downloader_program=wget
    fi
fi

# Usage: download URL filename
download() {
case "$downloader_program" in
    curl )
        curl -fsS "$1" -o "$2"
        ;;
    wget )
        wget -nv "$1" -O "$2"
        ;;
    *)
        echo "Invalid downloader"
        exit 1
        ;;
esac
}

if [ "$buildout_cfg_file" = "hhu" ]; then
    buildout_cfg_file=buildouts/hhu.cfg
elif [ -n "$buildout_cfg_file" ]; then
    buildout_cfg_file=$(readlink -f "$buildout_cfg_file")
else
    buildout_cfg_file=buildout.cfg
fi

if ! $not_use_sudo_commands; then
    case $distro in
    debian )
        PKGS_TO_INSTALL=$PKGS_TO_INSTALL' gcc make build-essential bin86 unzip libpcre3-dev git mercurial python libssl-dev libbz2-dev pkg-config libsqlite3-dev openjdk-7-jre libpq-dev'
        PKGS_TO_INSTALL=$PKGS_TO_INSTALL' openssh-client mutt'
        PKGS_TO_INSTALL=$PKGS_TO_INSTALL' ruby ruby-dev'

        # rubygems is included on modern debians
        if dpkg -p rubygems >/dev/null 2>&1 ; then
            PKGS_TO_INSTALL=$PKGS_TO_INSTALL' rubygems'
        fi

        if $install_mysql_client; then
            PKGS_TO_INSTALL=$PKGS_TO_INSTALL' libmysqlclient-dev'
        fi
        ;;
    arch )
        PKGS_TO_INSTALL=$PKGS_TO_INSTALL' gcc make base-devel bin86 unzip git mercurial python2 pkg-config sqlite jre7-openjdk postgresql-libs openssh mutt ruby'

        if $install_mysql_client; then
            PKGS_TO_INSTALL=$PKGS_TO_INSTALL' libmysqlclient'
        fi
        ;;
    fedora )
        $SUDO_CMD yum groupinstall --assumeyes development-tools
        PKGS_TO_INSTALL=$PKGS_TO_INSTALL' gcc dev86 unzip git mercurial sqlite sqlite-devel java-1.7.0-openjdk postgresql openssh mutt ruby openssl-devel bzip2-devel'
        ;;
    esac
    # Install all Packages
    echo $PKG_INSTALL $PKGS_TO_INSTALL
    $SUDO_CMD $PKG_INSTALL_CMD $PKGS_TO_INSTALL

    if $setup_services; then
        if [ "$adhoc_user" = "root" ]; then
            echo "You are root. Please use the -U flag to set the user adhocracy should be running as"
            exit 35
        fi

        if [ -r "adhocracy_buildout/${SERVICE_TEMPLATE}" ]; then
            stmpl=$(cat "adhocracy_buildout/${SERVICE_TEMPLATE}")
        else
            stmpl=$(download $SERVICE_TEMPLATE_URL -)
        fi
        case $distro in 
            debian )
            SERVICE_CMD='update-rc.d'
            SERVICE_CMD_SUFFIX=' defaults'
            INIT_FILE='/etc/init.d/adhocracy_services'
            ;;
            arch )
            SERVICE_CMD='systemctl enable'
            INIT_FILE='/etc/rc.d/adhocracy_services'
            ;;
            fedora )
            SERVICE_CMD='systemctl enable'
            INIT_FILE='/etc/rc.d/adhocracy_services'
            SERVICE_CMD_SUFFIX='.service'
            ;;
        esac
        if [ "$distro" = "fedora" -o "$distro" = "arch" ] ; then
        echo "
[Unit]
Description=Adhocracy Daemon

[Service]
Type=forking
ExecStart=/bin/sh /etc/rc.d/adhocracy_services start
ExecStop=/bin/sh /etc/rc.d/adhocracy_services stop
ExecStatus=/bin/sh /etc/rc.d/adhocracy_services status

[Install]
WantedBy=multi-user.target
" | $SUDO_CMD tee >/dev/null /etc/systemd/system/adhocracy_services.service
        fi

        echo "$stmpl" | \
            sed -e "s#\${[^}]*:[^}]*user}#$adhoc_user#" \
                -e "s#\${buildout:directory}#$(readlink -f .)/adhocracy_buildout#" \
                -e "s#\${domains:main}#supervisord#" | \
                $SUDO_CMD tee "$INIT_FILE" >/dev/null
        $SUDO_CMD chmod a+x "$INIT_FILE"
        $SUDO_CMD $SERVICE_CMD adhocracy_services${SERVICE_CMD_SUFFIX}
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

if [ '!' -w adhocracy_buildout ]; then
    echo 'Cannot write to adhocracy_buildout directory. Change to another directory, remove adhocracy_buildout, or run as another user'
    exit 22
fi
if [ -x adhocracy_buildout/bin/supervisorctl ]; then
    adhocracy_buildout/bin/supervisorctl shutdown >/dev/null 2>/dev/null || true
fi

check_port_free=adhocracy_buildout/scripts/check_port_free.py
if [ '!' -e "$check_port_free" ]; then
    check_port_free_tmp=$(mktemp)
    check_port_free="$check_port_free_tmp"
    if ! download "$CHECK_PORT_FREE_URL" "$check_port_free_tmp"; then
        ex=$?
        echo "Download failed. Are you connected to the Internet?"
        exit $ex
    fi
fi
$PYTHON_CMD $check_port_free -g 10 --kill-pid $ADHOCRACY_PORT $SUPERVISOR_PORTS
if [ -n "$check_port_free_tmp" ]; then
    rm -f $check_port_free_tmp
fi

if [ '!' -e adhocracy_buildout/.git ]; then
    git clone "$GIT_URL" adhocracy_buildout
    (cd adhocracy_buildout && git checkout -q "$branch")
fi

cd adhocracy_buildout

if [ '!' -e python/buildout.python/src ]; then
    git submodule init
    git submodule update
fi

# Install local python if necessary
if [ '!' -x bin/python ]; then
    if [ '!' -f python/bin/buildout ]; then
        (cd python && python bootstrap.py)
    fi
    (cd python && bin/buildout)
fi

# Workaround: the custom Pillow in our custom Python brings in a custom libjpeg
# However, during runtime, the custom libjpeg is not in ld's path.
if ! bin/python -c 'from PIL import Image' 2>/dev/null ; then
    ${SUDO_CMD} cp ./python/parts/opt/lib/libjpeg.so.8 /usr/lib/
    bin/python -c 'from PIL import Image'
fi


# Fix until https://github.com/collective/buildout.python/pull/31 is accepted
find python/buildout.python/ -name *pyc -delete
# Fix until https://github.com/collective/buildout.python/pull/32 is accepted
if [ "$(strings bin/python | grep '^PyUnicodeUCS._DecodeLatin1$')" '!=' "$(strings eggs/lxml-*.egg/lxml/etree.so 2>/dev/null | grep '^PyUnicodeUCS._DecodeLatin1$')" ]; then
    rm -rf -- eggs/lxml-*.egg
fi

# Set up adhocracy configuration
ln -s -f "${buildout_cfg_file}" ./buildout_current.cfg

# bootstrap our buildout if it is outdated or not available
HAVE_BUILDOUT_VERSION=$(bin/buildout --version 2>&1 | cut -d ' ' -f 3)
WANT_BUILDOUT_VERSION=$(sed -n 's#zc\.buildout = ##p' versions.cfg)
if test "$HAVE_BUILDOUT_VERSION" "!=" "$WANT_BUILDOUT_VERSION"; then
    # Workaround for https://github.com/liqd/adhocracy/issues/479
    if test "$(bin/python -c 'import setuptools;print setuptools.__version__' || true)" = "0.6"; then
        python/python-2.7/bin/easy_install -U distribute
    fi

    bin/python bootstrap.py -c buildout_current.cfg
fi

# Install adhocracy
bin/buildout -c buildout_current.cfg

# Install adhocracy interactive script
echo '#!/bin/sh
set -e
cd "$(dirname $(dirname $(readlink -f $0)))"

# Remove caches (workaround: cache fails when switching adhocracy.client_location)
rm -rf var/data/templates

cp etc/adhocracy.ini etc/adhocracy-interactive.ini

# Comment out the following line to restrict access to local only
sed "s#host = .*#host = 0.0.0.0#" -i etc/adhocracy-interactive.ini
exec bin/paster serve --reload etc/adhocracy-interactive.ini
' > "bin/adhocracy_interactive.sh"
chmod a+x "bin/adhocracy_interactive.sh"

# Autostart adhocracy 
if $autostart; then
    bin/supervisord
    echo "Use ${ROOTDIR_FROM_CALLER}bin/supervisorctl to control running services."
    python scripts/check_port_free.py -o -g 20 ${SUPERVISOR_PORTS}
    if bin/supervisorctl status | grep -vq RUNNING; then
        sleep 2 # Wait for supervisord to register that everything's running
        if bin/supervisorctl status | grep -vq RUNNING; then
            echo 'Failed to start all services:'
            bin/supervisorctl status
            exit 31
        fi
    fi

    pasterOutput=$(bin/paster setup-app etc/adhocracy.ini --name=content)
    if echo "$pasterOutput" | grep -q ERROR; then
        echo "$pasterOutput"
        echo 'Error in paster setup'
        exit 32
    fi

    echo
    echo
    echo "Type  ${ROOTDIR_FROM_CALLER}bin/adhocracy_interactive.sh  to run the interactive paster daemon."
    echo "Then, navigate to  http://127.0.0.1:${ADHOCRACY_PORT}/  to see adhocracy!"
    echo "Use the email \"admin@adhocracy.lan\" and password \"password\" to login."
fi
