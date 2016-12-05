from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

app = Celery('fir',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
        )

# load task module from all registered plugin
#app.autodiscover_tasks(['fir.whois', 'fir_artifacts'])
imports = ('fir.whois')

if __name__ == '__main__':
    app.start()
