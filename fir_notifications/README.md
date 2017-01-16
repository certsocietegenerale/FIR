# Notifications plugin for FIR

## Features

This plugins allows you to launch asynchronous tasks with Celery and send notifications to users.

## Installation

In your FIR virtualenv, launch:

```bash
(fir-env)$ pip install -r fir_notifications/requirements.txt
```

In *$FIR_HOME/fir/config/installed_app.txt*, add:

```
fir_notifications
```

In your *$FIR_HOME*, launch:

```bash
(fir-env)$ ./manage.py migrate fir_notifications
```

You should configure fir_celery (broker and result backend).

## Usage

Users can subscribe to notifications via their profile page.

Core FIR notifications:
* 'event:created': new event
* 'event:updated': update of an event
* 'incident:created': new incident
* 'incident:updated': update of an incident

## Configuration

### Celery

`fir_notifications` uses the FIR plugin `fir_celery`.

### Full URL in notification links

To generate correct URL in notification, `fir_notifications` needs to know the external URL of the FIR site:

``` python
EXTERNAL_URL = 'https://fir.example.com'
```

### Email notifications

You have to configure [Django email backend](https://docs.djangoproject.com/en/1.9/topics/email/).

In addition, `fir_notifications` uses two settings:

``` python
# From address (required)
NOTIFICATIONS_EMAIL_FROM = 'fir@example.com'
# Reply to address (optional)
NOTIFICATIONS_EMAIL_REPLY_TO = None
```

#### S/MIME

To send signed/encrypted email notifications with S/MIME to users, install and configure [django-djembe](https://github.com/cabincode/django-djembe) and add it in your *installed_apps.txt*.

The following configuration example from the Djembe Readme can help you:

``` bash
(fir-env)$ pip install -r fir_notifications/requirements_smime.txt
(fir-env)$ python manage.py migrate djembe
```

In *$FIR_HOME/fir/config/installed_app.txt*, add:

```
djembe
```

Change your email backend in your settings:

``` python
EMAIL_BACKEND = 'djembe.backends.EncryptingSMTPBackend'
```

To use a cipher other than the default AES-256, specify it in your settings `DJEMBE_CIPHER`:


``` python
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

To create signed notifications, in the admin site (*Djembe > Identities*), supply both a certificate and a private key which must not have a passphrase, with an `Address` that is the same as your setting `NOTIFICATIONS_EMAIL_FROM`. Any mail sent *from* this Identity's address will be signed with the private key.

User certificates will be added from the user profile in FIR (*Configure Email*).

### Jabber (XMPP) notifications

Configure `fir_notifications`:

``` python
# FIR user JID 
NOTIFICATIONS_XMPP_JID = 'fir@example.com'
# Password for fir@example.com JID
NOTIFICATIONS_XMPP_PASSWORD = 'my secret password'
# XMPP server
NOTIFICATIONS_XMPP_SERVER = 'localhost'
# XMPP server port
NOTIFICATIONS_XMPP_PORT = 5222
```

### Notification templates

You have to create at least onenotification template per notification event in the Django admin site.

To render notifications, each notification method can use the fields `subject`, `description` or `short_description`:

- Email uses `subject` and `description`.
- XMPP uses `subject` and `short_description`.

These fields will accept Markdown formatted text and Django template language markups. The Django template context will contain an `instance`object, the instance of the object that fired the notification event.

The Email `description` will generate a multipart message: a plain text part in Markdown and a HTML part rendered from this Markdown. The XMPP `short_description` will be rendered as HTML from Markdown.

The template used to send the notification to the user will be chosen from the templates available to this user:
- For a user with global permissions (permission from a Django group), global templates (templates with no nusiness line attached to it) will be preferred. 
- For a user with no global permission, the nearest business line template will be preferred, global templates will be used as a fallback.
## Hacking

### Adding notification method

You have to create a subclass of `NotificationMethod` from `fir_notifications.methods` and implement at least the `send` method. You can then register your method with `fir_notification.registry.registry.register_method`.

If your configuration method needs some additional user defined settings, you have to list them in the class property `options`. See `EmailMethod` and `XmppMethod` for details. 

### Adding notification event

Use the `@notification_event` decorator defined in `fir_notifications.decorators` to decorate a classic Django signal handler function. This handler must return a tuple with an instance of the notification model and a queryset of the concerned business lines.



