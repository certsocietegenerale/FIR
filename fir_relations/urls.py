from django.conf.urls import url

from fir_relations import views

app_name='fir_relations'

urlpatterns = [
    url(r'^(?P<content_type>\d+)/object/(?P<object_id>\d+)/$', views.relations, name='list'),
    url(r'^(?P<relation_id>\d+)/remove/$', views.remove_relation, name='remove')
]
