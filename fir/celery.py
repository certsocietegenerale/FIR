from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

app = Celery('celery',
        broker='redis://localhost:6379/0',
        backend='',
        include=[])

if __name__ == '__main__':
    app.start()
