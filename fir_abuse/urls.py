from django.urls import re_path

from fir_abuse import views, api

app_name = "fir_abuse"

urlpatterns = [
    re_path(r"^emailform/$", views.emailform, name="emailform"),
]

api_urls = [("abuse", api.AbuseViewSet)]
