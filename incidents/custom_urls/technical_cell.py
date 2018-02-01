from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^$', views.dashboard_technical_main, name='main'),
    url(r'^all/$', views.technical_cell_incidents, name='all')
]