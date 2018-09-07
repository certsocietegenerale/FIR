import markdown2
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from fir_plugins.links import registry


def _combine_with_settings(values, setting):
    values = [value for value in values.split(';') if value.strip()]
    if hasattr(settings, setting):
        values = list(set(values + getattr(settings, setting)))

    return values


def prepare_email_message(to, subject, body, behalf=None, cc=None, bcc=None, request=None):
    reply_to = {}

    if hasattr(settings, 'REPLY_TO'):
        reply_to = {'Reply-To': settings.REPLY_TO, 'Return-Path': settings.REPLY_TO}

    if behalf is None and hasattr(settings, 'EMAIL_FROM'):
        behalf = settings.EMAIL_FROM

    if not isinstance(to, (tuple, list)):
        to = to.split(';')

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=behalf,
        to=to,
        cc=cc,
        bcc=bcc,
        headers=reply_to
    )
    email_message.attach_alternative(markdown2.markdown(
        body,
        extras=["link-patterns", "tables", "code-friendly"],
        link_patterns=registry.link_patterns(request),
        safe_mode=True
    ),
        'text/html')

    return email_message


def send(request, to, subject, body, behalf=None, cc='', bcc=''):

    cc = _combine_with_settings(cc, 'EMAIL_CC')
    bcc = _combine_with_settings(bcc, 'EMAIL_BCC')

    email_message = prepare_email_message(to, subject, body, behalf=behalf, cc=cc, bcc=bcc, request=request)
    email_message.send()
