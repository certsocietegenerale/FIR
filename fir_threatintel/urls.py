from django.urls import re_path

from fir_threatintel import views

app_name='fir_threatintel'

urlpatterns = [
    re_path(r'^update_api', views.update_api, name='update_api'),
    re_path(r'^query_yeti_artifacts', views.query_yeti_artifacts, name='query_yeti_artifacts'),
    re_path(r'^send_yeti_artifacts', views.send_yeti_artifacts, name='send_yeti_artifacts'),
]
