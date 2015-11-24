from django.conf.urls import patterns, include, url
from rest_framework import routers, serializers, viewsets

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib.auth.models import User

# requirements for api
from rest_framework import routers
from rest_framework.authtoken import views as token_views
from fir.api import views

# automatic URL routing for API
# include login URLs for the browsable API.
router = routers.DefaultRouter()
router.register(r'api/users', views.UserViewSet)
router.register(r'api/groups', views.GroupViewSet)
router.register(r'api/incidents', views.IncidentViewSet)
router.register(r'api/artifacts', views.ArtifactViewSet)

# urls for core FIR components
urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^api/token/', token_views.obtain_auth_token),
	url(r'^tools/', include('incidents.custom_urls.tools', namespace='tools')),
    url(r'^incidents/', include('incidents.urls', namespace='incidents')),
    url(r'^search/$', 'incidents.views.search', name='search'),
    url(r'^events/', include('incidents.custom_urls.events', namespace='events')),
    url(r'^login/', 'incidents.views.user_login', name='login'),            # have a "main module"
    url(r'^logout/', 'incidents.views.user_logout', name='logout'),         # main module
    url(r'^artifacts/', include('incidents.custom_urls.artifacts', namespace='artifacts')),
    url(r'^stats/', include('incidents.custom_urls.stats', namespace='stats')),
    url(r'^ajax/', include('incidents.custom_urls.ajax', namespace='ajax')),
    url(r'^user/', include('incidents.custom_urls.user', namespace='user')),
    url(r'^dashboard/', include('incidents.custom_urls.dashboard', namespace='dashboard')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'incidents.views.index'),

    # alerting
    url(r'^alerting/', include('fir_alerting.urls', namespace='alerting')),

    # todos
    url(r'^todos/', include('fir_todos.urls', namespace='todos')),

    # nuggets
    url(r'^nuggets/', include('fir_nuggets.urls', namespace='nuggets')),
)
admin.autodiscover()
