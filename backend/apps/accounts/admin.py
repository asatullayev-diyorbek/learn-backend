from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TelegramAuthChallenge, TelegramIdentity, TelegramLoginCode, User


@admin.register(User)
class LearnUserAdmin(UserAdmin):
    pass


@admin.register(TelegramIdentity)
class TelegramIdentityAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "telegram_username", "user", "linked_at")
    search_fields = ("telegram_id", "telegram_username")


@admin.register(TelegramAuthChallenge)
class TelegramAuthChallengeAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "telegram_id", "user", "created_at", "expires_at")
    list_filter = ("status",)
    # Never expose token_hash by itself as if it were useful outside the
    # DB; it's a hash, not the secret, but there's no reason to show it.
    exclude = ("token_hash",)


@admin.register(TelegramLoginCode)
class TelegramLoginCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "created_at", "expires_at", "used_at")
    exclude = ("code_hash",)
