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
    re_path(
        r"^(?P<incident_id>\d+)/status/(?P<status>[OBC])$",
        views.change_status,
        name="change_status",
    ),
    re_path(
        r"^(?P<incident_id>\d+)/attribute$", views.add_attribute, name="add_attribute"
    ),
    re_path(
        r"^(?P<incident_id>\d+)/attribute/(?P<attribute_id>\d+)/delete/$",
        views.delete_attribute,
        name="delete_attribute",
    ),
]
