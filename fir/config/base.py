from __future__ import absolute_import, unicode_literals

import os
from pkgutil import find_loader
from importlib import import_module

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Django settings for fir project.


ENFORCE_2FA = False

tf_error_message = """Django two factor is not installed and ENFORCE_2FA is set to True.
Either set ENFORCE_2FA to False or pip install django-two-factor-auth
"""

try:
    import two_factor
    TF_INSTALLED = True
except ImportError:
    if ENFORCE_2FA:
        raise RuntimeWarning(tf_error_message)
    TF_INSTALLED = False


if TF_INSTALLED:
    LOGIN_URL = 'two_factor:login'
    LOGIN_REDIRECT_URL = 'two_factor:profile'
else:
    LOGIN_URL = "/login/"
    LOGOUT_URL = "/logout/"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/files/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware'
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

if TF_INSTALLED:
    TF_MIDDLEWARE = ('django_otp.middleware.OTPMiddleware',)
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + TF_MIDDLEWARE


# Authentication and authorization backends
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'incidents.authorization.ObjectPermissionBackend',
)

# Absolute filesystem path to the directory that will hold user-uploaded files
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

ROOT_URLCONF = 'fir.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'fir.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'rest_framework',
    'rest_framework.authtoken',
    'fir_plugins',
    'incidents',
    'fir_artifacts',
    'treebeard',
    'fir_email'
)

if TF_INSTALLED:
    TF_APPS = (
        'django_otp',
        'django_otp.plugins.otp_static',
        'django_otp.plugins.otp_totp',
        'two_factor'
    )
    INSTALLED_APPS = INSTALLED_APPS + TF_APPS
    try:
        import otp_yubikey
        INSTALLED_APPS = INSTALLED_APPS + ('otp_yubikey',)
    except ImportError:
        pass

apps_file = os.path.join(BASE_DIR, 'fir', 'config', 'installed_apps.txt')
if os.path.exists(apps_file):
    apps = list(INSTALLED_APPS)
    with open(apps_file) as f:
        for line in f.readlines():
            line = line.strip()
            if line != "":
                apps.append(line)
                settings = '{}.settings'.format(line)
                if find_loader(settings):
                    globals().update(import_module(settings).__dict__)

    INSTALLED_APPS = tuple(apps)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages"
            )
        }
    }
]

# Show incident IDs in views?
INCIDENT_SHOW_ID = False

# Incident ID prefix in views and links
INCIDENT_ID_PREFIX = "FID:"

# Permission added to the incident created by user, None for no permission
INCIDENT_CREATOR_PERMISSION = 'incidents.view_incidents'

# If you can see an event/incident, you can comment it!
INCIDENT_VIEWER_CAN_COMMENT = True


# Escape HTML when displaying markdown
MARKDOWN_SAFE_MODE = True

ALLOWED_HOSTS = ["127.0.0.1", "10.0.0.194"]


# Allowed HTML tags in Markdown output (requires MARKDOWN_SAFE_MODE to be True)
MARKDOWN_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
    'p',
    'h1', 'h2', 'h3', 'h4',
    'table', 'thead', 'th', 'tbody', 'tr', 'td',
    'br',
    'hr',
    'pre'
]

# User self-service features
USER_SELF_SERVICE = {
    # User can change his own email address
    'CHANGE_EMAIL': True,
    # User can change his first and last name
    'CHANGE_NAMES': True,
    # User can change his profile values (number of incidents per page, hide closed incidents)
    'CHANGE_PROFILE': True,
    # User can change his password
    'CHANGE_PASSWORD': True
}

# Put notification events you don't want in this tuple
# Example: NOTIFICATIONS_DISABLED_EVENTS = ('event:created', 'incident:created')
NOTIFICATIONS_DISABLED_EVENTS = ()

# Send 'incident:*' notification events for both Event and Incident if True
NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS = False
