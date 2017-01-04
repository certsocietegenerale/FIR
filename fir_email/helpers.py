import markdown2
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from fir_plugins.links import registry


def _combine_with_settings(values, setting):
    values = [value for value in values.split(';') if value.strip()]
    if hasattr(settings, setting):
        values = list(set(values + getattr(settings, setting)))

    return values


def send(request, to, subject, body, behalf=None, cc='', bcc=''):
    reply_to = {}

    if hasattr(settings, 'REPLY_TO'):
        reply_to = {'Reply-To': settings.REPLY_TO, 'Return-Path': settings.REPLY_TO}

    if behalf is None and hasattr(settings, 'EMAIL_FROM'):
        behalf = settings.EMAIL_FROM

    cc = _combine_with_settings(cc, 'EMAIL_CC')
    bcc = _combine_with_settings(bcc, 'EMAIL_BCC')

    e = EmailMultiAlternatives(
        subject=subject,
        from_email=behalf,
        to=to.split(';'),
        cc=cc,
        bcc=bcc,
        headers=reply_to
    )
    e.attach_alternative(markdown2.markdown(
            body,
            extras=["link-patterns", "tables", "code-friendly"],
            link_patterns=registry.link_patterns(request),
            safe_mode=True
        ),
        'text/html')
    e.content_subtype = 'html'
    e.send()
