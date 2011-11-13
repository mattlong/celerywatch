from optparse import make_option

from django.core.management.base import BaseCommand

from celerywatch import watcher

class Command(BaseCommand):
    """Run a daemon that monitors the celery daemon and stops it if it starts to fail too many tasks."""
    help = 'Runs a celeryd watcher daemon that will shutdown celeryd if it fails too many tasks.'
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
    make_option('-g', '--procgrep', action='store', type='string', dest='proc_grep', default=None, help='TODO'),
    make_option('-t', '--stopthreshold', action='store', type='float', dest='stop_threshold', default=0.5, help='TODO'),
    make_option('-m', '--mintasks', action='store', type='int', dest='min_tasks', default=10, help='TODO'),
    )

    def handle(self, *args, **options):
        watcher.evdump(
                stop_threshold=options['stop_threshold'],
                min_tasks=options['min_tasks'],
                process_grep=options['proc_grep'],
        )
