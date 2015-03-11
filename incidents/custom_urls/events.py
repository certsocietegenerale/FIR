from django.conf.urls import patterns, url

from incidents import views

urlpatterns = patterns('',
	url(r'^new/$', views.new_event, name='new'),
	url(r'^$', views.event_index, name='index'),
	url(r'^all/$', views.events_all, name='all'),
	url(r'^(?P<incident_id>\d+)/$', views.details, name='details'),
)
