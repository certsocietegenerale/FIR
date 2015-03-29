from django.conf.urls import patterns, url
from incidents import views


urlpatterns = patterns('',
    url(r'^mce/config.js$', views.mce_config, name='mce_config'),
)
