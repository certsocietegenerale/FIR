from django.conf.urls import url

from fir_abuse import views

urlpatterns = [
    url(r'^emailform/$', views.emailform, name='emailform'),
    url(r'^send_email/$', views.send_email, name='send_email'),
]
