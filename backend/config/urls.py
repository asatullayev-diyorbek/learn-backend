from django.contrib import admin
from django.urls import include, path, re_path
from bot import views as bot_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/courses/", include("apps.courses.urls")),
    path("api/submissions/", include("apps.submissions.urls")),
    path("api/telegram/", include("bot.urls")),
    path("webhook/", bot_views.telegram_webhook_view, name="telegram-webhook-root"),
    re_path(r"^webhook/?$", bot_views.telegram_webhook_view),
]
