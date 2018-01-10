from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^$', views.management_index, name='index'),
    url(r'^all/$', views.management_incidents, name='all'),
    # url(r'^(?P<incident_id>\d+)/$', views.details, name='details'),
]
