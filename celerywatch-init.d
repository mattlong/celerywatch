#!/bin/bash -e

### BEGIN INIT INFO
# Provides:          celerywatch
# Required-Start:    $network $local_fs $remote_fs
# Required-Stop:     $network $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: celery worker watcher daemon
### END INIT INFO

set -e

DEFAULT_PID_FILE="/var/run/celerywatch.pid"
DEFAULT_LOG_FILE="/var/log/celerywatch.log"
DEFAULT_CELERYWATCH="celeryd_watch"
DEFAULT_LOG_LEVEL="INFO"
DEFAULT_NODES="celery"

# /etc/init.d/celeryd: start and stop the celery task worker daemon.

if test -f /etc/default/celerywatcher; then
    . /etc/default/celerywatcher
fi

. /lib/lsb/init-functions

CELERYWATCH_PID_FILE=${CELERYWATCH_PID_FILE:-${CELERYWATCH_PID_FILE:-$DEFAULT_PID_FILE}}
CELERYWATCH_LOG_FILE=${CELERYWATCH_LOG_FILE:-${CELERYWATCH_LOG_FILE:-$DEFAULT_LOG_FILE}}
CELERYWATCH_LOG_LEVEL=${CELERYWATCH_LOG_LEVEL:-${CELERYWATCH_LOGLEVEL:-$DEFAULT_LOG_LEVEL}}
CELERYWATCH=${CELERYWATCH:-$DEFAULT_CELERYWATCH}
CELERYCTL=${CELERYCTL:-"celeryctl"}

export CELERY_LOADER

CELERYWATCH_OPTS="--daemonize --pidfile=$CELERYWATCH_PID_FILE $CELERYWATCH_OPTS"

if [ -n "$2" ]; then
    CELERYWATCH_OPTS="$CELERYWATCH_OPTS $2"
fi

# Extra start-stop-daemon options, like user/group.
if [ -n "$CELERYWATCH_USER" ]; then
    DAEMON_OPTS="$DAEMON_OPTS --uid=$CELERYWATCH_USER"
fi
if [ -n "$CELERYWATCH_GROUP" ]; then
    DAEMON_OPTS="$DAEMON_OPTS --gid=$CELERYWATCH_GROUP"
fi

if [ -n "$CELERYWATCH_CHDIR" ]; then
    DAEMON_OPTS="$DAEMON_OPTS --workdir=\"$CELERYWATCH_CHDIR\""
fi

check_dev_null() {
    if [ ! -c /dev/null ]; then
        echo "/dev/null is not a character device!"
        exit 1
    fi
}

export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"

check_celery_script () {
    if [ ! -f "$CELERY_SCRIPT" ]; then
        echo "WARNING: $CELERY_SCRIPT does not exist, not doing anything"
        exit 1
    fi
}

stop_watcher () {
    start-stop-daemon --stop --pidfile "$CELERYWATCH_PID_FILE" \
        --exec $CELERYWATCH || true

    while [ -f "$CELERYWATCH_PID_FILE" ]; do
        sleep 0.1
    done
}

start_watcher () {
    source /home/ubuntu/.virtualenvs/crocodoc/bin/activate
    start-stop-daemon --start --pidfile "$CELERYWATCH_PID_FILE" \
        --chdir "$CELERYWATCH_CHDIR" --exec $CELERYWATCH -- $CELERYWATCH_OPTS || true
}

restart_watcher () {
    stop_watcher
    start_watcher
}

case "$1" in
    start)
        check_dev_null
        check_celery_script
        start_watcher
    ;;

    stop)
        check_dev_null
        check_celery_script
        stop_watcher
    ;;

    status)
        #$CELERYCTL status
		status_of_proc -p $CELERYWATCH_PID_FILE "$CELERYWATCH" celerydwatch && exit 0 || exit $?
    ;;

    restart)
        check_dev_null
        check_celery_script
        restart_watcher
    ;;

    *)
        echo "Usage: /etc/init.d/celerywatch {start|stop|restart|status}"
        exit 1
    ;;
esac

exit 0
