from django.urls import re_path

from fir_relations import api

app_name = "fir_relations"

urlpatterns = []

api_urls = [
    ("relations", api.RelationViewSet),
]
