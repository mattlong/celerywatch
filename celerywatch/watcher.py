import os, sys, subprocess
from pkg_resources import resource_filename

from celery.app import app_or_default
from celery.datastructures import LRUCache

DEBUG = False

TASK_HISTORY = LRUCache(limit=10)

def run_command(cmds):
    proc = subprocess.Popen(cmds,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, error = proc.communicate()
    return (proc.returncode, output, error)
    if proc.returncode != 0:
        print 'error'
        print output
        print error
        sys.exit(1)
    else:
        print output.strip()
        print 'done'
        sys.exit(0)

class PDFWorkerMonitor(object):

    def __init__(self,
            stop_threshold=0.1,
            min_tasks=1,
            process_grep=None,
            post_stop_script=None,
            override_stop_script=False,
        ):
        self.MIN_TASKS = min_tasks
        self.STOP_THRESHOLD = stop_threshold
        self.PROCESS_GREP = process_grep
        self.POST_STOP_SCRIPT=post_stop_script
        self.OVERRIDE_STOP_SCRIPT=override_stop_script

        if DEBUG:
            for k,v in filter(lambda (k,v): k.upper() == k, vars(self).iteritems()):
                print k, v

        self.task_count = 0
        self.error_rate = 0.0

    def kill_celery(self, non_daemon=False):
        if not self.OVERRIDE_STOP_SCRIPT:
            print 'stopping celeryd...'
            stop_script = resource_filename(__name__, 'bin/stopCeleryd.sh')
            cmds = ['sh', stop_script, self.PROCESS_GREP or '']
            (returncode, output, error) = run_command(cmds)
            if returncode != 0:
                print 'error stopping celeryd:'
                print output.strip()
                print error.strip()
                sys.exit(1)
            else:
                print output.strip()
                print 'done'

        if self.POST_STOP_SCRIPT and os.path.isfile(self.POST_STOP_SCRIPT):
            print 'running post-stop script %s' % (self.POST_STOP_SCRIPT,)
            cmds = [self.POST_STOP_SCRIP]
            (returncode, output, error) = run_command(cmds)
            if returncode != 0:
                print 'error running post-stop script:'
                print output.strip()
                print error.strip()
            else:
                print output.strip()
                print 'done'
        sys.exit(0)
            

    def on_task_failed(self, event):
        #task-failed event fields (unicode): exception, traceback, uuid, clock, timestamp, hostname, type
        self.task_count += 1
        TASK_HISTORY[event['uuid']] = 'fail'
        fails = filter(lambda pair: pair[1] == 'fail', TASK_HISTORY.items())
        if self.task_count >= self.MIN_TASKS:
            recent_task_count = len(TASK_HISTORY.keys())
            self.error_rate = len(fails)/float(recent_task_count)
            if self.error_rate > self.STOP_THRESHOLD:
                print 'Error rate of %.0f%% over last %d tasks; after %d lifetime tasks' % (self.error_rate*100, recent_task_count, self.task_count,)
                self.kill_celery()

    def on_task_succeeded(self, event):
        #task-success event fields (unicode): runtime, uuid, clock, timestamp, hostname, type, result
        self.task_count += 1
        TASK_HISTORY[event['uuid']] = 'success'

#def evdump(stop_threshold=0.5, min_tasks=10, process_grep=None):
def evdump(*args, **kwargs):
    stop_threshold = kwargs.get('stop_threshold', 0.5)
    min_tasks = kwargs.get('min_tasks', 10)
    process_grep = kwargs.get('process_grep', None)
    post_stop_script = kwargs.get('post_stop_script', None)
    override_stop_script = kwargs.get('override_stop_script', False)
    app = app_or_default(None)
    monitor = PDFWorkerMonitor(
            stop_threshold=stop_threshold,
            min_tasks=min_tasks,
            process_grep=process_grep,
            post_stop_script=post_stop_script,
            override_stop_script=override_stop_script,
    )
    conn = app.broker_connection()
    #recv = app.events.Receiver(conn, handlers={"*": dumper.on_event})
    recv = app.events.Receiver(conn, handlers={'task-succeeded': monitor.on_task_succeeded, 'task-failed': monitor.on_task_failed})
    print 'Monitoring celeryd for %.0f%% error rate...' % (monitor.STOP_THRESHOLD*100, )
    try:
        recv.capture()
    except (KeyboardInterrupt, SystemExit):
        conn and conn.close()

if __name__ == "__main__":
    evdump(*sys.argv)
