from __future__ import absolute_import, unicode_literals

import os
from pkgutil import find_loader
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

from django.conf import settings


includes = []
for app in settings.INSTALLED_APPS:
    if app.startswith('fir_'):
        module_name = "{}.tasks".format(app)
        if find_loader(module_name):
            includes.append(module_name)

celery_app = Celery(
    'celeryconf',
    broker='redis://%s:%d/%d' % (settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB),
    backend='redis://%s:%d/%d' % (settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB),
    include=includes
)


if __name__ == '__main__':
    celery_app.start()
