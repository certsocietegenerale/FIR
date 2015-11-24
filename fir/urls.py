from pkgutil import find_loader
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from rest_framework.authtoken import views as token_views

from fir.config.base import INSTALLED_APPS
from incidents import views
from fir.api import apiviews

# automatic URL routing for API
# include login URLs for the browsable API.
router = routers.DefaultRouter()

router.register(r'users', apiviews.UserViewSet)
router.register(r'groups', apiviews.GroupViewSet)
router.register(r'incidents', apiviews.IncidentViewSet)
router.register(r'artifacts', apiviews.ArtifactViewSet)

# urls for core FIR components
urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/token/', token_views.obtain_auth_token),
    url(r'^tools/', include('incidents.custom_urls.tools', namespace='tools')),
    url(r'^incidents/', include('incidents.urls', namespace='incidents')),
    url(r'^search/$', views.search, name='search'),
    url(r'^events/', include('incidents.custom_urls.events', namespace='events')),
    url(r'^login/', views.user_login, name='login'),            # have a "main module"
    url(r'^logout/', views.user_logout, name='logout'),         # main module
    url(r'^stats/', include('incidents.custom_urls.stats', namespace='stats')),
    url(r'^ajax/', include('incidents.custom_urls.ajax', namespace='ajax')),
    url(r'^user/', include('incidents.custom_urls.user', namespace='user')),
    url(r'^dashboard/', include('incidents.custom_urls.dashboard', namespace='dashboard')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.dashboard_main),
]

for app in INSTALLED_APPS:
    if app.startswith('fir_'):
        app_name = app[4:]
        app_urls = '{}.urls'.format(app)
        if find_loader(app_urls):
            urlpatterns.append(url('^{}/'.format(app_name), include(app_urls, namespace=app_name)))
