from django.conf.urls import url

from fir_abuse import views

urlpatterns = [
    url(r'^(?P<incident_id>\d+)/get_template/(?P<artifact_id>\d+)/$', views.get_template, name='get_template'),
    url(r'^emailform/$', views.emailform, name='emailform'),
    url(r'^send_email/$', views.send_email, name='send_email'),
    url(r'^task/(?P<task_id>\d+)/$', views.task_state, name='task_state'),
]
