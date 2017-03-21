from django.conf.urls import patterns, url

from fir_threatintel import views

urlpatterns = patterns('',
    url(r'^update_api', views.update_api, name='update_api'),
)
