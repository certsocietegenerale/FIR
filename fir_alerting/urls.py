from django.urls import re_path

from fir_alerting import views

app_name='fir_alerting'

urlpatterns = [
    re_path(r'^(?P<incident_id>\d+)/get_template/(?P<template_type>[\w-]+)/$', views.get_template, name='get_template'),
    re_path(r'^(?P<incident_id>\d+)/get_template/(?P<template_type>[\w-]+)/(?P<bl>[\d]+)/$', views.get_template, name='get_template'),
    re_path(r'^emailform/$', views.emailform, name='emailform'),
    re_path(r'^send_email/$', views.send_email, name='send_email'),
]
