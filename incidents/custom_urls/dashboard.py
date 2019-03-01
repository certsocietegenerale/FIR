from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^$', views.dashboard_main, name='main'),
    url(r'^starred/$', views.dashboard_starred, name='starred'),
    url(r'^open/$', views.dashboard_open, name='open'),
    url(r'^blocked/$', views.dashboard_blocked, name='blocked'),
    url(r'^old/$', views.dashboard_old, name='old'),
]
