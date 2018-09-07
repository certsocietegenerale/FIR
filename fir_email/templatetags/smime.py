from django import template

from fir_email.utils import check_smime_status
from fir_email.forms import SMIMECertificateForm

register = template.Library()


@register.inclusion_tag('fir_email/smime_profile_action.html', takes_context=True)
def smime_profile_action(context):
    if check_smime_status() and context.request.user.email:
        form = SMIMECertificateForm(user=context.request.user)
        return {'form': form, 'smime_status': True}
    return {'form': None, 'smime_status': False}