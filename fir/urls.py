from pkgutil import find_loader
from django.conf.urls import include, url
from django.contrib import admin

from fir.config.base import INSTALLED_APPS
from incidents import views

from django.views.static import serve
from django.conf import settings

# urls for core FIR components
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
    url(r'^nmap/', include('incidents.custom_urls.nmap', namespace='nmap')),
    url(r'^uploads/xml/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^nessus/', include('incidents.custom_urls.nessus', namespace='nessus')),
    url(r'^uploads/nessus/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^awvs/', include('incidents.custom_urls.awvs', namespace='awvs')),
    url(r'^uploads/awvs/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}),
]

for app in INSTALLED_APPS:
    if app.startswith('fir_'):
        app_name = app[4:]
        app_urls = '{}.urls'.format(app)
        if find_loader(app_urls):
            urlpatterns.append(url('^{}/'.format(app_name), include(app_urls, namespace=app_name)))
