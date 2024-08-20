from django.apps import apps
from django.urls import include, re_path

import fir.urls as fir_urls

fir_urls.urlpatterns.append(re_path(r"^oidc/", include("mozilla_django_oidc.urls")))

urlpatterns = []
