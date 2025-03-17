from django.urls import re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

app_name = "fir_openapi"


urlpatterns = [
    re_path(r"^schema/$", SpectacularAPIView.as_view(), name="schema"),
    re_path(
        r"^schema/swagger-ui/$",
        SpectacularSwaggerView.as_view(url_name="fir_openapi:schema"),
    ),
    re_path(
        r"^schema/redoc/$",
        SpectacularRedocView.as_view(url_name="fir_openapi:schema"),
    ),
]
