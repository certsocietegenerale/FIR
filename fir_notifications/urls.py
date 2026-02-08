from fir_notifications import api

app_name = "fir_notifications"

urlpatterns = []

api_urls = [
    ("notifications_preferences", api.NotificationPreferenceViewSet),
    ("notifications_method_configuration", api.MethodConfigurationViewSet),
]
