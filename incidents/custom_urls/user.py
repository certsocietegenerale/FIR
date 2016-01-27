from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^toggleclosed/$', views.toggle_closed, name='toggle_closed'),
]
