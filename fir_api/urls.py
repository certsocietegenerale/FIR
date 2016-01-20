from django.conf.urls import patterns, include, url

# requirements for api
from rest_framework import routers
from rest_framework.authtoken import views as token_views
from fir_api.views import *

# automatic URL routing for API
# include login URLs for the browsable API.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'incidents', IncidentViewSet)
router.register(r'artifacts', ArtifactViewSet)

# urls for core FIR components
urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^token/', token_views.obtain_auth_token),
)
