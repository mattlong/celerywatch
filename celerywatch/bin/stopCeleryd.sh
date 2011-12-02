#!/bin/sh

PROCESS_GREP=$1

if [ -x "/etc/init.d/celeryd" ]; then
  echo "Stopping celeryd with daemon script..."
  /etc/init.d/celeryd stop
else
  echo "Daemon script not found; killing celeryd processes with '${PROCESS_GREP}'..."
  ps ax | grep -m 1 "l\+.*celeryd .*${PROCESS_GREP}" | awk '{print $1}' | xargs kill
fi
