from django.conf.urls import url

from incidents import views

app_name='user'

urlpatterns = [
    url(r'^profile$', views.user_self_service, name='profile'),
    url(r'^password/change$', views.user_change_password, name='change_password'),
    url(r'^toggleclosed/$', views.toggle_closed, name='toggle_closed'),
]
