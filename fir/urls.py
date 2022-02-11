from pkgutil import find_loader
from django.urls import include, re_path
from django.contrib import admin

from fir.config.base import INSTALLED_APPS, TF_INSTALLED
from incidents import views


# urls for core FIR components
urlpatterns = [
    re_path(r'^logout/', views.user_logout, name='logout'),
    re_path(r'^incidents/', include(('incidents.urls', 'incidents'), namespace='incidents')),
    re_path(r'^search/$', views.search, name='search'),
    re_path(r'^events/', include(('incidents.custom_urls.events', 'url_events'), namespace='events')),
    re_path(r'^stats/', include(('incidents.custom_urls.stats', 'stats'), namespace='stats')),
    re_path(r'^ajax/', include(('incidents.custom_urls.ajax', 'ajax'), namespace='ajax')),
    re_path(r'^user/', include(('incidents.custom_urls.user', 'user'), namespace='user')),
    re_path(r'^dashboard/', include(('incidents.custom_urls.dashboard', 'dashboard'), namespace='dashboard')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', views.dashboard_main),
]

if TF_INSTALLED:
    from two_factor.views import LoginView
    from two_factor.urls import urlpatterns as tf_urls
    custom_urls = []
    for tf_url in tf_urls[0]:
        if tf_url.name != "login":
            custom_urls.append(tf_url)
    custom_urls.append(re_path(r'^account/login/$',
                           view=views.CustomLoginView.as_view(),
                           name='login',))
    urlpatterns.append(re_path(r'', include((custom_urls, 'two_factor'))))
else:
    urlpatterns.append(re_path(r'^login/', views.user_login, name='login'))


for app in INSTALLED_APPS:
    if app.startswith('fir_'):
        app_name = app[4:]
        app_urls = '{}.urls'.format(app)
        if find_loader(app_urls):
            urlpatterns.append(re_path('^{}/'.format(app_name), include((app_urls, app), namespace=app_name)))
