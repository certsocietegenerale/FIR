from django.conf.urls import url

from incidents import views
from django.views.static import serve
from django.conf import settings

from incidents.views import AWVSlist



urlpatterns = [
#    url(r'^found/$', views.found_event, name='found'),
#    url(r'^new/$', views.new_event, name='new'),
    url(r'^$', views.awvs_index, name='awvs_index'),
    url(r'^upload/$',views.awvs_upload, name='awvs_upload'),
    url(r'^awvsfilelist/$',AWVSlist.as_view(), name = 'awvslist'),
#    url(r'^all/$', views.events_all, name='all'),
#    url(r'^parser/$', views.xml_parser, name='xml_parser'),
#    url(r'^static/upload/xml/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT})
]