from django.urls import re_path

from fir_misp import views, api

app_name = "fir_misp"

urlpatterns = [
    re_path(r"^update_api", views.update_api, name="update_api"),
]

api_urls = [
    ("misp", api.MISPViewSet),
]
