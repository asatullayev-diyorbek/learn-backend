from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("csrf/", views.CsrfCookieView.as_view(), name="csrf"),
    path("telegram/token/", views.TelegramTokenCreateView.as_view(), name="telegram-token-create"),
    path(
        "telegram/token/<str:token>/status/",
        views.TelegramTokenStatusView.as_view(),
        name="telegram-token-status",
    ),
    path("telegram/code/verify/", views.TelegramCodeVerifyView.as_view(), name="telegram-code-verify"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.CurrentUserView.as_view(), name="me"),
]
