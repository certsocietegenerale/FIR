from django.urls import re_path

from incidents import views

app_name='user'

urlpatterns = [
    re_path(r'^profile$', views.user_self_service, name='profile'),
    re_path(r'^password/change$', views.user_change_password, name='change_password'),
    re_path(r'^toggleclosed/$', views.toggle_closed, name='toggle_closed'),
]
