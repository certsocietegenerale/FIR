from django.urls import re_path

from fir_todos import views, api

app_name = "fir_todos"

urlpatterns = [
    re_path(r"^(?P<incident_id>\d+)/list/$", views.list, name="list"),
    re_path(r"^(?P<incident_id>\d+)/create/$", views.create, name="create"),
    re_path(r"^(?P<todo_id>\d+)/delete/$", views.delete, name="delete"),
    re_path(
        r"^(?P<todo_id>\d+)/toggle_status/$", views.toggle_status, name="toggle_status"
    ),
    re_path(r"^tasks/$", views.dashboard, name="dashboard"),
]


try:
    from fir_todos.api import TodoSerializer
except ModuleNotFoundError:
    pass
else:
    api_urls = [
        (r"todo", api.TodoViewSet),
    ]
