from django.urls import re_path
from incidents import views

app_name = "ajax"

urlpatterns = [
    re_path(
        r"^comment/(?P<comment_id>\d+)$", views.update_comment, name="update_comment"
    ),
]
