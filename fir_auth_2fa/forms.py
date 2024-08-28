from two_factor.forms import AuthenticationTokenForm


class CustomAuthenticationTokenForm(AuthenticationTokenForm):
    def __init__(self, user, initial_device, **kwargs):
        super(CustomAuthenticationTokenForm, self).__init__(
            user, initial_device, **kwargs
        )
        self.fields["otp_token"].widget.attrs.update({"class": "form-control"})
