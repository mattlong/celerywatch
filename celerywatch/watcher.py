import os, sys, subprocess, signal
from pkg_resources import resource_filename
from optparse import make_option

from celery.app import app_or_default
from celery.datastructures import LRUCache

from celerywatch.daemon import Daemon

DEBUG = False

def run_command(cmds):
    proc = subprocess.Popen(cmds,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, error = proc.communicate()
    return (proc.returncode, output, error)

class CeleryWatcher(Daemon):

    def __init__(self, app=None):
        super(CeleryWatcher, self).__init__(None)

        self.app = app or app_or_default(None)

    def reset(self):
        self.task_count = 0
        self.error_rate = 0.0
        self.TASK_HISTORY = LRUCache(limit=10)

    def execute_with_options(self, *args, **kwargs):
        self.options = kwargs
        self.conn = self.app.broker_connection()
        self.recv = self.app.events.Receiver(self.conn, handlers={
            'task-succeeded': self.on_task_succeeded,
            'task-failed': self.on_task_failed,
        })

        if self.options['daemonize']:
            self.pidfile = self.options['pidfile']
            self.stdout = '/tmp/celerywatch.log'
            self.start()
        else:
            self.pidfile = self.options['pidfile'] #even if we don't daemonize, must set it to a non-None value
            self.run()

    def run(self):
        def handler(signum, frame):
            self.stop()
        signal.signal(signal.SIGTERM, handler)

        try:
            self.reset()
            print 'Monitoring celeryd for %.0f%% error rate...' % (self.options['stop_threshold']*100, )
            sys.stdout.flush()
            self.recv.capture()
        except (KeyboardInterrupt, SystemExit):
            self.cleanup()

    def cleanup(self):
        self.conn and self.conn.close()

    def get_options(self):
        return (
            make_option('--daemonize', action='store_true', dest='daemonize', default=False, help='TODO'),
            make_option('--pidfile', action='store', type='string', dest='pidfile', default='/tmp/celerywatch.pid', help='TODO'),
            make_option('--procgrep', action='store', type='string', dest='process_grep', default=None, help='TODO'),
            make_option('--stopthreshold', action='store', type='float', dest='stop_threshold', default=0.5, help='TODO'),
            make_option('--mintasks', action='store', type='int', dest='min_tasks', default=10, help='TODO'),
            make_option('--poststopscript', action='store', type='string', dest='post_stop_script', default=None, help='TODO'),
            make_option('--override', action='store_true', dest='override_stop_script', default=False, help='TODO'),
        )

    def kill_celery(self, non_daemon=False):
        if not self.options['override_stop_script']:
            print 'stopping celeryd...'
            sys.stdout.flush()
            stop_script = resource_filename(__name__, 'bin/stopCeleryd.sh')
            cmds = ['sh', stop_script, self.options['process_grep'] or '']
            (returncode, output, error) = run_command(cmds)
            if returncode != 0:
                print 'error stopping celeryd:'
                print output.strip(), '\n', error.strip()
                sys.stdout.flush()
                self.reset()
            else:
                print output.strip()
                print 'done'
                sys.stdout.flush()

        post_stop_script = self.options['post_stop_script']
        if post_stop_script and os.path.isfile(post_stop_script):
            print 'running post-stop script %s' % (post_stop_script,)
            sys.stdout.flush()
            cmds = [post_stop_script]
            (returncode, output, error) = run_command(cmds)
            if returncode != 0:
                print 'error running post-stop script:'
                print output.strip()
                print error.strip()
                sys.stdout.flush()
            else:
                print output.strip()
                print 'done'
                sys.stdout.flush()
        self.reset()

    #task-failed event fields (unicode): exception, traceback, uuid, clock, timestamp, hostname, type
    def on_task_failed(self, event):
        self.task_count += 1
        self.TASK_HISTORY[event['uuid']] = 'fail'
        fails = filter(lambda pair: pair[1] == 'fail', self.TASK_HISTORY.items())
        if self.task_count >= self.options['min_tasks']:
            recent_task_count = len(self.TASK_HISTORY.keys())
            self.error_rate = len(fails)/float(recent_task_count)
            if self.error_rate > self.options['stop_threshold']:
                print 'Error rate of %.0f%% over last %d tasks; after %d lifetime tasks' % (
                        self.error_rate*100, recent_task_count, self.task_count,)
                sys.stdout.flush()
                self.kill_celery()

    #task-success event fields (unicode): runtime, uuid, clock, timestamp, hostname, type, result
    def on_task_succeeded(self, event):
        self.task_count += 1
        self.TASK_HISTORY[event['uuid']] = 'success'

#if __name__ == "__main__":
#    pass #run(*sys.argv)
