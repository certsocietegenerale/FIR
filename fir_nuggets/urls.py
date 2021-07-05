from django.conf.urls import url

from fir_nuggets import views

app_name='fir_nuggets'

urlpatterns = [
    url(r'^(?P<event_id>\d+)/list', views.list, name='list'),
    url(r'^(?P<event_id>\d+)/new', views.new, name='new'),
    url(r'^edit/(?P<nugget_id>\d+)', views.edit, name='edit'),
    url(r'^delete/(?P<nugget_id>\d+)', views.delete, name='delete'),
]
