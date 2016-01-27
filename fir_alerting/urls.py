from django.conf.urls import url

from fir_alerting import views

urlpatterns = [
    url(r'^(?P<incident_id>\d+)/get_template/(?P<template_type>[\w-]+)/$', views.get_template, name='get_template'),
    url(r'^(?P<incident_id>\d+)/get_template/(?P<template_type>[\w-]+)/(?P<bl>[\d]+)/$', views.get_template, name='get_template'),
    url(r'^emailform/$', views.emailform, name='emailform'),
    url(r'^send_email/$', views.send_email, name='send_email'),
]
