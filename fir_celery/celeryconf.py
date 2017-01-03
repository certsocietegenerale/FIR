from __future__ import absolute_import, unicode_literals

import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', 'redis')

REDIS_PORT = 6379
REDIS_DB = 0

celery_app = Celery('celeryconf',
        broker='redis://%s:%d/%d' % (REDIS_HOST, REDIS_PORT, REDIS_DB),
        backend='redis://%s:%d/%d' % (REDIS_HOST, REDIS_PORT, REDIS_DB),
        include=['fir_celery.whois', 'fir_celery.network_whois']
        )


if __name__ == '__main__':
    celery_app.start()
