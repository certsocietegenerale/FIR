import os
from celery import Celery
from celery.signals import setup_logging
from django.conf import settings
from logging.config import dictConfig

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fir.settings")


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(settings.LOGGING)


celery_app = Celery(
    "celeryconf",
    broker="redis://%s:%d/%d"
    % (settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB),
    backend="redis://%s:%d/%d"
    % (settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB),
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == "__main__":
    celery_app.start()
