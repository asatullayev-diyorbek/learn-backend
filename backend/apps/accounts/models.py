from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Learn platform user.

    Telegram is the only authentication path. There is no password login;
    accounts created via the Telegram flows get set_unusable_password().
    """


class TelegramIdentity(models.Model):
    """Links exactly one Learn user to exactly one Telegram id."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="telegram_identity"
    )
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_username = models.CharField(max_length=64, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    linked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TelegramIdentity(telegram_id={self.telegram_id}, user={self.user_id})"


class TelegramAuthChallenge(models.Model):
    """A one-time deep-link login challenge (Flow 1).

    Only the HMAC hash of the raw token is ever stored; the raw token lives
    only in the HTTP response/deep link and in the Telegram /start payload.
    """

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
    ]

    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE
    )
    telegram_id = models.BigIntegerField(null=True, blank=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # Guards idempotent login-on-poll: set the first time the status
    # endpoint actually calls django.contrib.auth.login() for this challenge.
    session_issued_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"TelegramAuthChallenge(status={self.status}, telegram_id={self.telegram_id})"


class TelegramLoginCode(models.Model):
    """A one-time 5-digit login code (Flow 2)."""

    code_hash = models.CharField(max_length=64, unique=True, db_index=True)
    telegram_id = models.BigIntegerField(db_index=True)
    telegram_username = models.CharField(max_length=64, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"TelegramLoginCode(telegram_id={self.telegram_id})"
