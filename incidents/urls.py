from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^$', views.index, {'is_incident': True}, name='index'),
    url(r'^all/$', views.incidents_all, name='all'),
    url(r'^(?P<incident_id>\d+)/$', views.details, name='details'),
    url(r'^(?P<incident_id>\d+)/followup/$', views.followup, name='followup'),
    url(r'^(?P<incident_id>\d+)/comment/$', views.comment, name='comment'),
    url(r'^(?P<incident_id>\d+)/comment/(?P<comment_id>\d+)/delete/$', views.delete_comment, name='delete_comment'),
    url(r'^(?P<incident_id>\d+)/edit/$', views.edit_incident, name='edit'),
    url(r'^(?P<incident_id>\d+)/delete/$', views.delete_incident, name='delete'),
    url(r'^(?P<incident_id>\d+)/status/(?P<status>[OBC])$', views.change_status, name='change_status'),
    url(r'^(?P<incident_id>\d+)/attribute$', views.add_attribute, name='add_attribute'),
    url(r'^(?P<incident_id>\d+)/attribute/(?P<attribute_id>\d+)/delete/$', views.delete_attribute, name='delete_attribute'),
]
