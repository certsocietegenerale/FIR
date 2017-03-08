import markdown2
from django.conf import settings

import xmpp
from django import forms

from fir_notifications.methods import NotificationMethod
from fir_notifications.methods.utils import request
from fir_plugins.links import registry as link_registry
from django.utils.translation import ugettext_lazy as _


class Client(xmpp.Client):
    def __init__(self, *args, **kwargs):
        kwargs['debug'] = []
        xmpp.Client.__init__(self, *args, **kwargs)

    def DisconnectHandler(self):
        pass


class XmppMethod(NotificationMethod):
    use_subject = True
    use_short_description = True
    name = 'xmpp'
    verbose_name = 'XMPP'
    options = {
        'jid': forms.CharField(max_length=100, label=_('Jabber ID'))
    }

    def __init__(self):
        super(NotificationMethod, self).__init__()
        self.messages = []
        self.jid = getattr(settings, 'NOTIFICATIONS_XMPP_JID', None)
        self.password = getattr(settings, 'NOTIFICATIONS_XMPP_PASSWORD', None)
        if self.jid is None or self.password is None:
            self.server_configured = False
            return
        self.server = getattr(settings, 'NOTIFICATIONS_XMPP_SERVER', None)
        self.port = getattr(settings, 'NOTIFICATIONS_XMPP_SERVER_PORT', 5222)
        self.connection_tuple = None
        self.use_srv = True
        self.jid = xmpp.JID(self.jid)
        if self.server is not None:
            self.connection_tuple = (self.server, self.port)
            self.use_srv = False
        self.client = Client(self.jid.getDomain())
        if self.client.connect(server=self.connection_tuple, use_srv=self.use_srv):
            self.client.auth(self.jid.getNode(), self.password, resource=self.jid.getResource())
            self.client.disconnected()
        self.server_configured = True

    def _ensure_connection(self):
        if not hasattr(self.client, 'Dispatcher'):
            if self.client.connect(server=self.connection_tuple, use_srv=self.use_srv):
                if self.client.auth(self.jid.getNode(), self.password, resource=self.jid.getResource()):
                    return True
            return False
        return self.client.reconnectAndReauth()

    def send(self, event, users, instance, paths):
        if not self._ensure_connection():
            print("Cannot contact the XMPP server")
            return
        for user, templates in users.items():
            jid = self._get_jid(user)
            if not self.enabled(event, user, paths) or jid is None:
                continue
            template = self._get_template(templates)
            if template is None:
                continue
            params = self.prepare(template, instance)
            message = xmpp.protocol.Message(jid, body=params['short_description'].encode('utf-8'),
                                            subject=params['subject'].encode('utf-8'), typ='chat')
            html = xmpp.Node('html', {'xmlns': 'http://jabber.org/protocol/xhtml-im'})
            text = u"<body xmlns='http://www.w3.org/1999/xhtml'>" + markdown2.markdown(params['short_description'],
                                                                                       extras=["link-patterns"],
                                                                                       link_patterns=link_registry.link_patterns(
                                                                                           request),
                                                                                       safe_mode=True) + u"</body>"
            html.addChild(node=xmpp.simplexml.XML2Node(text.encode('utf-8')))
            message.addChild(node=html)

            self.client.send(message)
        self.client.disconnected()

    def _get_jid(self, user):
        config = self._get_configuration(user)
        if 'jid' in config:
            return xmpp.JID(config['jid'])
        return None

    def configured(self, user):
        return super(XmppMethod, self).configured(user) and self._get_jid(user) is not None
