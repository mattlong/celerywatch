#from django.core.management.base import BaseCommand

from djcelery.app import app
from djcelery.management.base import CeleryCommand

from celerywatch import watcher

worker = watcher.CeleryWatcher(app=app)

class Command(CeleryCommand):
    """Run the celery watcher daemon"""
    help = 'Runs a celeryd watcher daemon that will shutdown celeryd if it fails too many tasks.'
    requires_model_validation = False
    options = (CeleryCommand.options
            + worker.get_options()
            #+ worker.preload_options
    )

    def handle(self, *args, **options):
        worker.execute_with_options(*args, **options)

#class Command(BaseCommand):
#    """Run a daemon that monitors the celery daemon and stops it if it starts to fail too many tasks."""
#    help = 'Runs a celeryd watcher daemon that will shutdown celeryd if it fails too many tasks.'
#    requires_model_validation = False
#    option_list = BaseCommand.option_list + watcher.get_options()
#
#    def handle(self, *args, **options):
#        watcher.run(*args, **options)
