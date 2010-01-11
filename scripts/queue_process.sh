#!/bin/bash
# This script will call adhocracy to run batch jobs. Run it from cron 
# or another command scheduler. 
# 
# Here's an example crontab entry:
# * * * * * nobody $ADHOCRACY_HOME/scripts/queue_process.sh
#

if [ $# -ne 1 ]; then
  echo "Usage: queue_process.sh {url}";
  echo "Example: queue_process.sh localhost:5000";
  exit $E_BADARGS;
fi;

E_BADARGS=65

type -P curl &>/dev/null || { 
    echo "Please install curl." >&2; 
    exit 1; 
}

curl -s -o /dev/null "http://$1/_queue_process"
exit $?