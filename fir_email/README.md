# Email helpers module

## Configure FIR to send emails

Follow the Django docs: [Django email backend](https://docs.djangoproject.com/en/1.9/topics/email/).

In addition, you have to configure two settings:

```python
# From address (required, string)
EMAIL_FROM = 'fir@example.com'
# Reply to address (optional, string)
REPLY_TO = None
```

## Adding CC and BCC recipients (for `fir_alerting` and `fir_abuse`)

You can force FIR to add CC and BCC recipients by configuring these settings:

```python
EMAIL_CC = ['cc@example.com',]
EMAIL_BCC = ['bcc@example.com',]
```

## Using S/MIME

To send signed/encrypted emails with S/MIME to users, install and configure [django-djembe](https://github.com/cabincode/django-djembe) and add it in your *installed_apps.txt*.

The following configuration example from the Djembe Readme can help you:

### Install

```bash
(fir-env)$ pip install -r fir_email/requirements_smime.txt
(fir-env)$ python manage.py migrate djembe
```

In *$FIR_HOME/fir/config/installed_app.txt*, add:

```
djembe
```

Change your email backend in your settings:

```python
EMAIL_BACKEND = 'djembe.backends.EncryptingSMTPBackend'
```

### Ciphers

To use a cipher other than the default AES-256, specify it in your settings `DJEMBE_CIPHER`:


```python
DJEMBE_CIPHER = 'des_ede3_cbc'  # triple DES
```
The intersection of M2Crypto's ciphers and RFC 3851 are:

* `des_ede3_cbc` (required by the RFC)
* `aes_128_cbc` (recommended, not required, by the RFC)
* `aes_192_cbc` (recommended, not required, by the RFC)
* `aes_256_cbc` (recommended, not required, by the RFC)
* `rc2_40_cbc` (RFC requires support, but it's weak -- don't use it)

RFC 5751 requires AES-128, and indicates that higher key lengths are of
course the future. It marks tripleDES with "SHOULD-", meaning it's on its
way out.

### Signed email

To create signed email, in the admin site (*Djembe > Identities*), supply both a certificate and a private key which must not have a passphrase, with an `Address` that is the same as your setting `EMAIL_FROM`. Any mail sent *from* this Identity's address will be signed with the private key.

### User certificates (email encryption)

User certificates will be added from the user profile in FIR (*Set S/MIME certificate*).
