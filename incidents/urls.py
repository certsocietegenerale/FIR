from django.urls import re_path

from incidents import views

app_name = "incidents"

urlpatterns = [
    re_path(r"^$", views.incident_display, {"is_incident": True}, name="index"),
    re_path(r"^(?P<incident_id>\d+)/$", views.details, name="details"),
    re_path(r"^(?P<incident_id>\d+)/followup/$", views.followup, name="followup"),
    re_path(r"^(?P<incident_id>\d+)/comment/$", views.comment, name="comment"),
    re_path(
        r"^(?P<incident_id>\d+)/comment/(?P<comment_id>\d+)/delete/$",
        views.delete_comment,
        name="delete_comment",
    ),
    re_path(r"^(?P<incident_id>\d+)/edit/$", views.edit_incident, name="edit"),
    re_path(r"^(?P<incident_id>\d+)/delete/$", views.delete_incident, name="delete"),
]
