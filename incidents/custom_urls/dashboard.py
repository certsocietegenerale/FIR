from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^$', views.dashboard_main, name='main'),
    url(r'^starred/$', views.dashboard_starred, name='starred'),
    url(r'^open/$', views.dashboard_open, name='open'),
    url(r'^qualification_in_progress/$', views.dashboard_qualification_in_progress, name='qualification_in_progress'),
    url(r'^qualified/$', views.dashboard_qualified, name='qualified'),
    url(r'^ap_defined/$', views.dashboard_ap_defined, name='ap_defined'),
    url(r'^ap_validated/$', views.dashboard_ap_validated, name='ap_validated'),
    url(r'^in_progress/$', views.dashboard_in_progress, name='in_progress'),
    url(r'^closed/$', views.dashboard_closed, name='closed'),
    url(r'^old/$', views.dashboard_old, name='old'),
    url(r'^assigned/$', views.dashboard_assigned, name="assigned")
]
