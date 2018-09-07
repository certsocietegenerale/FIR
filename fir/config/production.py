# -*- coding: utf-8 -*-

# This is the production settings !
# All settings that do not change across environments should be in 'fir.settings.base'
from fir.config.base import *

################################################################
##### Change these values
################################################################

ALLOWED_HOSTS = ['wooxu.com','127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'softkrates_FIR',
        'USER': 'softkrates_fir',
        'PASSWORD': '25000-Peladillas',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}




# SMTP SETTINGS
EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 25

# Uncomment this line to set a different reply-to address when sending alerts
# REPLY_TO = other@address.com
EMAIL_FROM = '"FIR root@wooxu.com" <root@wooxu.com>'

# Uncomment these lines if you want additional CC or BCC for all sent emails
EMAIL_CC = ['richardssen@icloud.com']
# EMAIL_BCC = ['address@email']

# SECRET KEY
SECRET_KEY = 'asdfdfñl345,g83kdfsñ3459dfgk4569045kdfgñg893456t_PLEASE'


################################################################

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# List of callables that know how to import templates from various sources.
# In production, we want to cache templates in memory
TEMPLATES[0]['OPTIONS']['loaders'] = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s: %(module)s %(filename)s:%(lineno)d(%(funcName)s)\n%(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# External URL of your FIR application (used in fir_notification to render full URIs in templates)
EXTERNAL_URL = 'http://wooxu.com'
