from django.conf.urls import url

from incidents import views

app_name='events'

urlpatterns = [
    url(r'^new/$', views.new_event, name='new'),
    url(r'^$', views.event_index, name='index'),
    url(r'^all/$', views.events_all, name='all'),
    url(r'^(?P<incident_id>\d+)/$', views.details, name='details'),
]
