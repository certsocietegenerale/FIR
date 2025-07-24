from django.urls import re_path

from incidents import views

app_name = "fir_dashboard"

urlpatterns = [
    re_path(r"^$", views.dashboard_main, name="main"),
]
