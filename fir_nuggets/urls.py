from django.urls import re_path

from fir_nuggets import views

app_name = "fir_nuggets"

urlpatterns = [
    re_path(r"^(?P<event_id>\d+)/list", views.list, name="list"),
    re_path(r"^(?P<event_id>\d+)/new", views.new, name="new"),
    re_path(r"^edit/(?P<nugget_id>\d+)", views.edit, name="edit"),
    re_path(r"^delete/(?P<nugget_id>\d+)", views.delete, name="delete"),
]

try:
    from fir_nuggets import api
except ModuleNotFoundError:
    pass
else:
    api_urls = [
        (r"nuggets", api.NuggetViewSet),
    ]
