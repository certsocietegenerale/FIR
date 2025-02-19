from django.urls import path
from fir_stats import views, api

app_name = "stats"

urlpatterns = [
    path("yearly", views.yearly_stats, name="yearly"),
    path("quarterly", views.quarterly_stats, name="quarterly"),
    path("quarterly/close_old", views.close_old, name="close_old"),
    path("compare", views.compare, name="compare"),
    path("sandbox", views.sandbox, name="sandbox"),
    path("attributes", views.attributes, name="attributes"),
    path("major", views.major, name="major"),
]

api_urls = [
    (r"stats", api.StatsViewSet),
]
