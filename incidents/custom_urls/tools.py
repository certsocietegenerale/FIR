from django.conf.urls import url
from incidents import views


urlpatterns = [
    url(r'^mce/config.js$', views.mce_config, name='mce_config'),
]
