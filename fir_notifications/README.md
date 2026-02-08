# Notifications plugin for FIR

## Features

This plugins allows you to send notifications to users.

## Installation

This plugin need `fir_celery` to work.

Please install `fir_celery` and `fir_notifications` using the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

## Usage

Users can subscribe to notifications via their profile page.

Core FIR notifications:
* 'event:created': new event
* 'event:updated': update of an event
* 'incident:created': new incident
* 'incident:updated': update of an incident
* 'event:commented': new comment added to an event
* 'incident:commented': new comment added to an incident
* 'event:status_changed': event status changed
* 'incident:status_changed': incident status changed

## Configuration

### Events

You can disable notification events in the settings using the key `NOTIFICATIONS_DISABLED_EVENTS`:

```python
NOTIFICATIONS_DISABLED_EVENTS = ("event:created", "incident:created")
```

If you don't want to send different notification events for Incidents and Events, you should enable this setting:

```python
# Send 'incident:*' notification events for both Event and Incident if True
NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS = True
```

### Celery

`fir_notifications` uses the FIR plugin `fir_celery`.

### Full URL in notification links

To generate correct URL in notification, `fir_notifications` needs to know the external URL of the FIR site:

``` python
EXTERNAL_URL = 'https://fir.example.com'
```

### Methods

You can enable or disable notification methods the settings using the key `NOTIFICATION_ENABLED_METHODS`:

```python
NOTIFICATIONS_ENABLED_METHODS = ("email", "xmpp")
```

In additon, custom notifications methods can be developped in the folder `methods`.

### Email notifications

Follow the `fir_email` [README](../fir_email/README.md).

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

These fields will accept Markdown formatted text and Django template language markups. The Django template context will contain an `instance` object, the instance of the object that fired the notification event.

The Email `description` will generate a multipart message: a plain text part in Markdown and a HTML part rendered from this Markdown. The XMPP `short_description` will be rendered as HTML from Markdown.

The template used to send the notification to the user will be chosen from the templates available to this user:
- For a user with global permissions (permission from a Django group), global templates (templates with no nusiness line attached to it) will be preferred. 
- For a user with no global permission, the nearest business line template will be preferred, global templates will be used as a fallback.


### Adding notification method

You have to create a subclass of `NotificationMethod` from `fir_notifications.methods` and implement at least the `send` method. All methods defined in the `method` folder will be automatically registered.

If your configuration method needs some additional user defined settings, you have to list them in the class property `options`. See `EmailMethod` and `XmppMethod` for details. 

### Adding notification event

Use the `@notification_event` decorator defined in `fir_notifications.decorators` to decorate a classic Django signal handler function. This handler must return a tuple with an instance of the notification model and a queryset of the concerned business lines.
