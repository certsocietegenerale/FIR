from django.conf.urls import url

from fir_threatintel import views

urlpatterns = [
    url(r'^update_api', views.update_api, name='update_api'),
]
