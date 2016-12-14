from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', 'redis')
REDIS_PORT = 6379
REDIS_DB = 0

app = Celery('fir',
        broker='redis://%s:%d/%d' % (REDIS_HOST, REDIS_PORT, REDIS_DB),
        backend='redis://%s:%d/%d' % (REDIS_HOST, REDIS_PORT, REDIS_DB)
        )

# load task module from all registered plugin
app.autodiscover_tasks()
imports = ('fir.whois', 'fir.network_whois')

if __name__ == '__main__':
    app.start()
