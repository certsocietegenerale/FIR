from django.conf.urls import url
from incidents import views


urlpatterns = [
    url(r'^comment/(?P<comment_id>\d+)$', views.update_comment, name='update_comment'),
    url(r'^incident/(?P<incident_id>\d+)/toggle_star/$', views.toggle_star, name='toggle_star'),
]
