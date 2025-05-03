from django.urls import re_path

from fir_artifacts import views

app_name = "fir_artifacts"

urlpatterns = [
    re_path(
        r"^(?P<artifact_id>\d+)/detach/(?P<relation_name>\w+)/(?P<relation_id>\d+)/$",
        views.detach_artifact,
        name="detach",
    ),
    re_path(
        r"^(?P<artifact_id>\d+)/correlations/$",
        views.artifacts_correlations,
        name="correlations",
    ),
]
