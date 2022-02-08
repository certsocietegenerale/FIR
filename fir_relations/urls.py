from django.urls import re_path

from fir_relations import views

app_name='fir_relations'

urlpatterns = [
    re_path(r'^(?P<content_type>\d+)/object/(?P<object_id>\d+)/$', views.relations, name='list'),
    re_path(r'^(?P<relation_id>\d+)/remove/$', views.remove_relation, name='remove')
]
