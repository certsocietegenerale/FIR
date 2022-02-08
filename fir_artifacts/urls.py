from django.urls import re_path

from fir_artifacts import views

app_name='fir_artifacts'

urlpatterns = [
    re_path(r'^(?P<artifact_id>\d+)/detach/(?P<relation_name>\w+)/(?P<relation_id>\d+)/$', views.detach_artifact, name='detach'),
    re_path(r'^(?P<artifact_id>\d+)/correlations/$', views.artifacts_correlations, name='correlations'),
    re_path(r'^files/(?P<content_type>\d+)/upload/(?P<object_id>\d+)/$', views.upload_file, name='upload_file'),
    re_path(r'^files/(?P<content_type>\d+)/archive/(?P<object_id>\d+)/$', views.download_archive, name='download_archive'),
    re_path(r'^files/(?P<file_id>\d+)/remove/$', views.remove_file, name='remove_file'),
    re_path(r'^files/(?P<file_id>\d+)/download/$', views.download, name='download_file'),
]
