import importlib
from django.apps import apps
from django.urls import include, re_path
from rest_framework import routers
from rest_framework.authtoken import views as token_views
from django.utils.translation import gettext_lazy as _

from fir_api import views
from fir.config.base import INSTALLED_APPS

app_name = "fir_api"

# automatic URL routing for API
# include login URLs for the browsable API.
router = routers.DefaultRouter(trailing_slash=False)
router.get_api_root_view().cls.__doc__ = _("FIR API endpoints")

router.register(r"users", views.UserViewSet, basename="users")
router.register(r"incidents", views.IncidentViewSet, basename="incidents")
router.register(r"artifacts", views.ArtifactViewSet, basename="artifacts")
router.register(r"files", views.FileViewSet, basename="files")
router.register(r"comments", views.CommentViewSet, basename="comments")
router.register(r"labels", views.LabelViewSet, basename="labels")
router.register(r"attributes", views.AttributeViewSet, basename="attributes")
router.register(
    r"validattributes", views.ValidAttributeViewSet, basename="validattributes"
)
router.register(r"businesslines", views.BusinessLinesViewSet, basename="businesslines")
router.register(
    r"incident_categories",
    views.IncidentCategoriesViewSet,
    basename="incident_categories",
)
router.register(r"stats", views.StatsViewSet, basename="stats")

# Load plugin API URLs
for app in INSTALLED_APPS:
    if app.startswith("fir_"):
        try:
            plugin_api = importlib.import_module(f"{app}.urls")
        except ImportError:
            pass
        else:
            if hasattr(plugin_api, "api_urls"):
                for route in plugin_api.api_urls:
                    router.register(route[0], route[1], basename=route[0])

# urls for core FIR components
urlpatterns = [
    re_path(r"^", include(router.urls)),
    re_path(r"^token/", token_views.obtain_auth_token),
]
