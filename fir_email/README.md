This module is part of fhe FIR. It allows FIR to send emails.
This module is always enabled (even if not included in `enabled_apps.txt`). It however need to be configured before being able to send emails.

## Configure FIR to send emails

Follow the Django docs: [Django email backend](https://docs.djangoproject.com/en/5.0/topics/email/).

You at least need to configure the following settings:

```python
# SMTP server (required, string)
EMAIL_HOST = "smtp.server.com"
# SMTP server (required, int)
EMAIL_PORT = 25
# Sender (required, string)
EMAIL_FROM = '"NAME" <name@domain>'
```

## Adding CC and BCC recipients (for `fir_alerting` and `fir_abuse`)

You can force FIR to add CC and BCC recipients by configuring these settings:

```python
EMAIL_CC = ['cc@example.com',]
EMAIL_BCC = ['bcc@example.com',]
```
