from django.urls import re_path

from incidents import views

app_name = "user"

urlpatterns = [
    re_path(r"^profile$", views.user_profile, name="profile"),
]
