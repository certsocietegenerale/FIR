from django.urls import re_path

from incidents import views

app_name='dashboard'

urlpatterns = [
    re_path(r'^$', views.dashboard_main, name='main'),
    re_path(r'^starred/$', views.dashboard_starred, name='starred'),
    re_path(r'^open/$', views.dashboard_open, name='open'),
    re_path(r'^blocked/$', views.dashboard_blocked, name='blocked'),
    re_path(r'^old/$', views.dashboard_old, name='old'),
]
