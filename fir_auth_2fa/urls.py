from django.apps import apps
from django.urls import include, re_path
from two_factor.views import LoginView
from two_factor.urls import urlpatterns as tf_urls
import fir.urls as fir_urls
from incidents import views as incidents_views
from fir_auth_2fa import views


# Remove the original login URL
fir_urls.urlpatterns = [
    x for x in fir_urls.urlpatterns if x.callback != incidents_views.user_login
]

custom_urls = []
for tf_url in tf_urls[0]:
    if getattr(tf_url, "name", "") not in ["login", "backup_tokens"]:
        custom_urls.append(tf_url)

custom_urls.extend(
    [
        re_path(
            r"^account/login/$",
            view=views.CustomLoginView.as_view(),
            name="login",
        ),
        re_path(
            r"^account/two_factor/backup/tokens/$",
            view=views.CustomBackupTokensView.as_view(),
            name="backup_tokens",
        ),
    ]
)

fir_urls.urlpatterns.append(re_path(r"", include((custom_urls, "two_factor"))))

urlpatterns = []
