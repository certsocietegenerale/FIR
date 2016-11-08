from django.conf.urls import url

from incidents import views
from django.views.static import serve
from django.conf import settings

from incidents.views import XMLlist



urlpatterns = [
#    url(r'^found/$', views.found_event, name='found'),
#    url(r'^new/$', views.new_event, name='new'),
    url(r'^$', views.nmap_index, name='nmap_index'),
    url(r'^upload/$',views.xml_upload, name='xml_upload'),
    url(r'^xmlfilelist/$',XMLlist.as_view(), name = 'xmllist'),
#    url(r'^all/$', views.events_all, name='all'),
#    url(r'^parser/$', views.xml_parser, name='xml_parser'),
#    url(r'^static/upload/xml/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT})
]