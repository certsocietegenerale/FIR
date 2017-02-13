from django import forms
from django.utils.translation import ugettext_lazy as _

from fir_email.utils import check_smime_status


class SMIMECertificateForm(forms.Form):
    certificate = forms.CharField(required=False, label=_('Certificate'),
                                  widget=forms.Textarea(attrs={'cols': 60, 'rows': 15}),
                                  help_text=_('Encryption certificate in PEM format.'))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        if self.user is not None and self.user.email and 'initial' not in kwargs:
            kwargs['initial'] = self._get_certificate()
        super(SMIMECertificateForm, self).__init__(*args, **kwargs)

    def _get_certificate(self):
        data = {}
        try:
            from djembe.models import Identity
        except ImportError:
            return data
        try:
            identity = Identity.objects.get(address=self.user.email)
        except Identity.DoesNotExist:
            return data
        except Identity.MultipleObjectsReturned:
            identity = Identity.objects.filter(address=self.user.email).first()
        data = {'certificate': identity.certificate}
        return data

    def clean_certificate(self):
        if not check_smime_status():
            raise forms.ValidationError(_('Improperly configured S/MIME: Email backend is incompatible'))
        try:
            from M2Crypto import X509
            certificate = self.cleaned_data['certificate']
            X509.load_cert_string(str(certificate))
        except ImportError:
            raise forms.ValidationError(_('Improperly configured S/MIME: missing dependencies'))
        except X509.X509Error:
            raise forms.ValidationError(_('Invalid certificate: unknown format'))
        return certificate

    def save(self, *args, **kwargs):
        if self.user is None or not self.user.email:
            return None
        try:
            from djembe.models import Identity
        except ImportError:
            return None
        config, created = Identity.objects.update_or_create(address=self.user.email, defaults=self.cleaned_data)
        return config