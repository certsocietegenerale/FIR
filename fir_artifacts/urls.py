from django.conf.urls import url

from fir_artifacts import views

urlpatterns = [
    url(r'^(?P<artifact_id>\d+)/detach/(?P<relation_name>\w+)/(?P<relation_id>\d+)/$', views.detach_artifact, name='detach'),
    url(r'^(?P<artifact_id>\d+)/correlations/$', views.artifacts_correlations, name='correlations'),
    url(r'^files/(?P<content_type>\d+)/upload/(?P<object_id>\d+)/$', views.upload_file, name='upload_file'),
    url(r'^files/(?P<content_type>\d+)/archive/(?P<object_id>\d+)/$', views.download_archive, name='download_archive'),
    url(r'^files/(?P<file_id>\d+)/remove/$', views.remove_file, name='remove_file'),
    url(r'^files/(?P<file_id>\d+)/download/$', views.download, name='download_file'),
]
