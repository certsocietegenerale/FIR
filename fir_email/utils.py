from django.conf import settings


def check_smime_status():
    if 'djembe' in settings.INSTALLED_APPS \
            and settings.EMAIL_BACKEND == 'djembe.backends.EncryptingSMTPBackend':
        return True
    return False
