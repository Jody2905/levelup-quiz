from django.contrib import admin
from django.urls import include, path

from quizzes.auth_views import RateLimitedLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", RateLimitedLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("quizzes.urls")),
]
