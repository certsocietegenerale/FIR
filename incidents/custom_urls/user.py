from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^profile$', views.user_profile, name='profile'),
    url(r'^toggleclosed/$', views.toggle_closed, name='toggle_closed'),
]
