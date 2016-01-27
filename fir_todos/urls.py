from django.conf.urls import url

from fir_todos import views

urlpatterns = [
    url(r'^(?P<incident_id>\d+)/list/$', views.list, name='list'),
    url(r'^(?P<incident_id>\d+)/create/$', views.create, name='create'),
    url(r'^(?P<todo_id>\d+)/delete/$', views.delete, name='delete'),
    url(r'^(?P<todo_id>\d+)/toggle_status/$', views.toggle_status, name='toggle_status'),
    url(r'^tasks/$', views.dashboard, name='dashboard'),
]
