from django.conf.urls import patterns, url

from incidents import views

urlpatterns = patterns('',
	url(r'^toggleclosed/$', views.toggle_closed, name='toggle_closed'),
)
