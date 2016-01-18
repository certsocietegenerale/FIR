from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^(?P<artifact_id>\d+)/$', views.artifacts_incidents, name='incidents'),
    url(r'^related-incidents/(?P<incident_id>\d+)/$', views.related_incidents, name='related_incidents'),
    url(r'^(?P<artifact_id>\d+)/detach/(?P<incident_id>\d+)/$', views.detach_artifact, name='detach'),
]
