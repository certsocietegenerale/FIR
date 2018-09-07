from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

from django.conf import settings


celery_app = Celery(
    'celeryconf',
    broker='redis://%s:%d/%d' % (settings.REDIS_HOST, settings.REDIS_PORT,
        settings.REDIS_DB),
    backend='redis://%s:%d/%d' % (settings.REDIS_HOST, settings.REDIS_PORT,
        settings.REDIS_DB)
    )

celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


if __name__ == '__main__':
    celery_app.start()
