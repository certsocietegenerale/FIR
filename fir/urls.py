from pkgutil import find_loader
from django.conf.urls import include, url
from django.contrib import admin

from fir.config.base import INSTALLED_APPS
from incidents import views


urlpatterns = [
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
	# api URLs
	url(r'^api/', include('fir_api.urls')),
]

for app in INSTALLED_APPS:
    if app.startswith('fir_'):
        app_name = app[4:]
        app_urls = '{}.urls'.format(app)
        if find_loader(app_urls):
        	urlpatterns.append(url('^{}/'.format(app_name), include(app_urls, namespace=app_name)))
