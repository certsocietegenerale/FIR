from django.urls import re_path
from fir_email.utils import check_smime_status
from fir_email import views


urlpatterns = []

if check_smime_status():
    urlpatterns.append(re_path(r'^user/certificate/$', views.smime_configuration, name='user-certificate'))
