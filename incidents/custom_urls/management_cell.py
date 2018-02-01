from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^$', views.dashboard_management_main, name='main'),
    url(r'^all/$', views.management_cell_incidents, name='all')
]