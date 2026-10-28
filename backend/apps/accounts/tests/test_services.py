from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts import services
from apps.accounts.models import TelegramAuthChallenge, TelegramIdentity, TelegramLoginCode

pytestmark = pytest.mark.django_db

TG_ID = 555000111


def test_challenge_create_confirm_status_happy_path():
    raw_token, challenge = services.create_auth_challenge(ip="127.0.0.1")
    assert challenge.status == TelegramAuthChallenge.STATUS_PENDING
    assert challenge.is_expired() is False

    status_challenge = services.get_auth_challenge_status(raw_token)
    assert status_challenge.id == challenge.id
    assert status_challenge.status == TelegramAuthChallenge.STATUS_PENDING

    user, error = services.confirm_auth_challenge(
        raw_token, TG_ID, "diyor", "Diyorbek", "Asatullayev"
    )
    assert error is None
    assert user is not None
    assert user.telegram_identity.telegram_id == TG_ID

    status_challenge.refresh_from_db()
    assert status_challenge.status == TelegramAuthChallenge.STATUS_CONFIRMED
    assert status_challenge.user_id == user.id


def test_expired_challenge_is_rejected():
    raw_token, challenge = services.create_auth_challenge()
    challenge.expires_at = timezone.now() - timedelta(seconds=1)
    challenge.save(update_fields=["expires_at"])

    user, error = services.confirm_auth_challenge(raw_token, TG_ID, "u", "f", "l")
    assert user is None
    assert error == "expired"


def test_confirmed_challenge_cannot_be_confirmed_twice():
    raw_token, _ = services.create_auth_challenge()

    user1, error1 = services.confirm_auth_challenge(raw_token, TG_ID, "u", "f", "l")
    assert error1 is None
    assert user1 is not None

    # Second (duplicate / concurrent) confirm attempt must not double-spend.
    user2, error2 = services.confirm_auth_challenge(raw_token, TG_ID, "u", "f", "l")
    assert user2 is None
    assert error2 == "used"


def test_unknown_token_returns_not_found():
    user, error = services.confirm_auth_challenge("does-not-exist", TG_ID, "u", "f", "l")
    assert user is None
    assert error == "not_found"


def test_get_or_create_user_for_telegram_is_idempotent():
    user1 = services.get_or_create_user_for_telegram(TG_ID, "a", "First", "Last")
    user2 = services.get_or_create_user_for_telegram(TG_ID, "a_renamed", "First", "Last")

    assert user1.id == user2.id
    assert TelegramIdentity.objects.filter(telegram_id=TG_ID).count() == 1
    identity = TelegramIdentity.objects.get(telegram_id=TG_ID)
    assert identity.telegram_username == "a_renamed"
    assert user1.has_usable_password() is False


def test_login_code_create_and_verify_happy_path():
    raw_code, error = services.create_login_code(TG_ID, "diyor", "Diyorbek", "A")
    assert error is None
    assert len(raw_code) == 5

    user, verify_error = services.verify_login_code(raw_code)
    assert verify_error is None
    assert user is not None
    assert user.telegram_identity.telegram_id == TG_ID


def test_login_code_rate_limited_on_rapid_recreation():
    _, error1 = services.create_login_code(TG_ID, "u", "f", "l")
    assert error1 is None

    raw_code2, error2 = services.create_login_code(TG_ID, "u", "f", "l")
    assert raw_code2 is None
    assert error2 == "rate_limited"


def test_login_code_rejected_when_expired():
    raw_code, _ = services.create_login_code(TG_ID, "u", "f", "l")
    code = TelegramLoginCode.objects.get()
    code.expires_at = timezone.now() - timedelta(seconds=1)
    code.save(update_fields=["expires_at"])

    user, error = services.verify_login_code(raw_code)
    assert user is None
    assert error == "expired"


def test_login_code_rejected_when_already_used():
    raw_code, _ = services.create_login_code(TG_ID, "u", "f", "l")

    user1, error1 = services.verify_login_code(raw_code)
    assert error1 is None
    assert user1 is not None

    user2, error2 = services.verify_login_code(raw_code)
    assert user2 is None
    assert error2 == "used"


def test_login_code_rejected_when_invalid():
    user, error = services.verify_login_code("00000")
    assert user is None
    assert error == "invalid"
