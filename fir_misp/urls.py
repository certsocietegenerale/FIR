from django.urls import re_path

from fir_misp import views

app_name='fir_misp'

urlpatterns = [
    re_path(r'^update_api', views.update_api, name='update_api'),
    re_path(r'^query_misp_artifacts', views.query_misp_artifacts, name='query_misp_artifacts'),
    re_path(r'^send_misp_artifacts', views.send_misp_artifacts, name='send_misp_artifacts'),
]
