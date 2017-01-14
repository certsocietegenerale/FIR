# Notifications plugin for FIR

## Features

This plugins allows you to launch asynchronous tasks with Celery and send notifications to users.

## Installation

In your FIR virtualenv, launch:

```bash
(fir_env)$ pip install -r fir_notifications/requirements.txt
```

In *$FIR_HOME/fir/config/installed_app.txt*, add:

```
fir_notifications
```

In your *$FIR_HOME*, launch:

```bash
(your_env)$ ./manage.py migrate fir_notifications
(your_env)$ ./manage.py collectstatic -y
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

To send signed/encrypted email notifications with S/MIME to users, install and configure [django-djembe](https://github.com/cabincode/django-djembe) and add it in your *installed_apps.txt*.

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

You have to create notification templates in the Django admin site.

To render notifications, each notification method can use the fields `subject`, `description` or `short_description`:

- Email uses `subject` and `description`.
- XMPP uses `subject` and `short_description`.

## Hacking

### Adding notification method

You have to create a subclass of `NotificationMethod` from `fir_notifications.methods` and implement at least the `send` method. You can then register your method with `fir_notification.registry.registry.register_method`.

If your configuration method needs some additional user defined settings, you have to list them in the class property `options`. See `EmailMethod` and `XmppMethod` for details. 

### Adding notification event

Use the `@notification_event` decorator defined in `fir_notifications.decorators` to decorate a classic Django signal handler function. This handler must return a tuple with an instance of the notification model and a queryset of the concerned business lines.



