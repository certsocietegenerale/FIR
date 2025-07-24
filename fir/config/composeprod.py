# This is the production settings !
# All settings that do not change across environments should be in 'fir.settings.base'
from fir.config.base import *

from environs import Env

env = Env()
env.read_env(env.str("ENV_PATH", ".env"), recurse=False)

################################################################
##### Change these values
################################################################

# Configure ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = ["http://" + h for h in ALLOWED_HOSTS] + [
    "https://" + h for h in ALLOWED_HOSTS
]

# Configure SECRET KEY
SECRET_KEY = env("SECRET_KEY", "I 4m tH3 d3f4u17 s3cr37")


# DATABASES SETTINGS

# If you have to deal with special characters in your password, use urlencode:
# https://django-environ.readthedocs.io/en/latest/#using-unsafe-characters-in-urls
DATABASES = {
    # reads var DATABASE_URL. If not set defaults to sqlite
    # To use mysql backend, you can set the following env for example
    # DATABASE_URL=mysql://fir:fir@fir_db:3306/fir
    "default": env.dj_db_url("DATABASE_URL", default="sqlite:////tmp/fir.sqlite")
}

# SMTP SETTINGS
EMAIL_HOST = env("EMAIL_HOST", "SMTP.DOMAIN.COM")
EMAIL_PORT = env.int("EMAIL_PORT", 25)

# Uncomment this line to set a different reply-to address when sending alerts
# REPLY_TO = env.str('REPLY_TO', 'to@domain')
EMAIL_FROM = env.str("EMAIL_FROM", '"NAME" <from@ndomain>')

# Uncomment these lines if you want additional CC or BCC for all sent emails
# EMAIL_CC = env.list('EMAIL_CC', ['cc@domain'])
# EMAIL_BCC = env.list('EMAIL_BCC', ['bcc@domain'])


# REDIS SETTINGS
# Uncomment the following lines if you want to run celery tasks
REDIS_HOST = env.str("REDIS_HOST", "fir_redis")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_DB = env.int("REDIS_DB", 0)

STATIC_ROOT = "/var/www/static"

################################################################

# False if not in os.environ
DEBUG = env.bool("DEBUG", default=False)

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# List of callables that know how to import templates from various sources.
# In production, we want to cache templates in memory
TEMPLATES[0]["OPTIONS"]["loaders"] = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)


# TEMPLATES[0]['OPTIONS']['loaders'] = (
#     ('django.template.loaders.cached.Loader', (
#         'django.template.loaders.filesystem.Loader',
#         'django.template.loaders.app_directories.Loader',
#     )),
# )

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose_celery": {
            "format": "%(asctime)s: [%(levelname)s/%(processName)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "console_celery": {
            "class": "logging.StreamHandler",
            "formatter": "verbose_celery",
        },
    },
    "loggers": {
        "celery": {
            # Logs of the celery worker
            "handlers": ["console_celery"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            # Logs related to python errors
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.server": {
            # Logs related to HTTP requests
            # when using python manage.py runserver
            # (This setting is not used when using uwsgi)
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "FIR": {
            # Logs related to applicative actions
            # (Incident created, etc)
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
            "formatter": "verbose",
        },
        "axes": {
            # Logs related to login/logout
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
            "formatter": "verbose",
        },
    },
}

# External URL of your FIR application (used in fir_notification to render full URIs in templates)
# EXTERNAL_URL = 'http://fir.example.com'

# Show incident IDs in views?
INCIDENT_SHOW_ID = env.bool("INCIDENT_SHOW_ID", default=False)

# Incident ID prefix in views and links
INCIDENT_ID_PREFIX = env("INCIDENT_ID_PREFIX", "FIR-")
