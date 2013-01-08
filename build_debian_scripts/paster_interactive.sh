#!/bin/sh

set -e

cd "$(dirname $(readlink -f $0))/../../"
. bin/activate

cp etc/adhocracy.ini etc/adhocracy-interactive.ini

# Comment out the following line to restrict access to local only
sed 's#host = .*#host = 0.0.0.0#' -i etc/adhocracy-interactive.ini

exec bin/paster serve --reload etc/adhocracy-interactive.ini
