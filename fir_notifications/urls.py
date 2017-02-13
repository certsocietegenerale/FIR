from django.conf.urls import url

from fir_notifications import views


urlpatterns = [
    url(r'^subscriptions$', views.subscriptions, name='subscriptions'),
    url(r'^subscriptions/(?P<object_id>\d+)$', views.edit_subscription, name='edit-subscription'),
    url(r'^subscriptions/subscribe$', views.edit_subscription, name='subscribe'),
    url(r'^subscriptions/(?P<object_id>\d+)/unsubscribe$', views.unsubscribe, name='unsubscribe'),
    url(r'^method/(?P<method>[a-zA-Z0-9_]+)$', views.method_configuration, name='method_configuration'),
]