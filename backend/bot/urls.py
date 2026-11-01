from django.urls import path
from bot import views

app_name = "bot"

urlpatterns = [
    path("webhook/", views.telegram_webhook_view, name="telegram-webhook"),
]

