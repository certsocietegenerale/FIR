from django.urls import re_path

from fir_notifications import views

app_name='fir_notifications'

urlpatterns = [
    re_path(r'^subscriptions$', views.subscriptions, name='subscriptions'),
    re_path(r'^subscriptions/(?P<object_id>\d+)$', views.edit_subscription, name='edit-subscription'),
    re_path(r'^subscriptions/subscribe$', views.edit_subscription, name='subscribe'),
    re_path(r'^subscriptions/(?P<object_id>\d+)/unsubscribe$', views.unsubscribe, name='unsubscribe'),
    re_path(r'^method/(?P<method>[a-zA-Z0-9_]+)$', views.method_configuration, name='method_configuration'),
]
