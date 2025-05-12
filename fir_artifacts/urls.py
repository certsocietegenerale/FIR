from django.urls import re_path

from fir_artifacts import api

app_name = "fir_artifacts"

urlpatterns = []

api_urls = [
    ("artifacts", api.ArtifactViewSet),
    ("files", api.FileViewSet),
]
