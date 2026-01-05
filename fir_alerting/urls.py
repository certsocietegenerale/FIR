from django.urls import re_path

from fir_alerting import views, api

app_name = "fir_alerting"

urlpatterns = [
    re_path(r"^emailform/$", views.emailform, name="emailform"),
]

api_urls = [("alerting", api.AlertingViewSet)]
