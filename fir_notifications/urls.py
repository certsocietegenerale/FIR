from django.conf.urls import url

from fir_notifications import views


urlpatterns = [
    url(r'^preferences$', views.preferences, name='preferences'),
    url(r'^preferences/(?P<method>[a-zA-Z0-9_]+)$', views.method_configuration, name='method_configuration'),
]