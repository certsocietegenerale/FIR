from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.authtoken import views as token_views

from fir_api import views

# automatic URL routing for API
# include login URLs for the browsable API.
router = routers.DefaultRouter(trailing_slash=False)

router.register(r'users', views.UserViewSet)
router.register(r'incidents', views.IncidentViewSet)
router.register(r'artifacts', views.ArtifactViewSet)
router.register(r'files', views.FileViewSet)

# urls for core FIR components
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^token/', token_views.obtain_auth_token),
]
