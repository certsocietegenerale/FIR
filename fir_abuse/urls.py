from django.urls import re_path

from fir_abuse import views

app_name='fir_abuse'

urlpatterns = [
    re_path(r'^(?P<incident_id>\d+)/get_template/(?P<artifact_id>\d+)/$', views.get_template, name='get_template'),
    re_path(r'^emailform/$', views.emailform, name='emailform'),
    re_path(r'^send_email/$', views.send_email, name='send_email'),
    re_path(r'^task/(?P<task_id>\d+)/$', views.task_state, name='task_state'),
]
