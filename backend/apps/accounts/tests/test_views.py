import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts import services

pytestmark = pytest.mark.django_db

TG_ID = 777000222


@pytest.fixture
def client():
    return APIClient()


def test_csrf_view_sets_cookie(client):
    url = reverse("accounts:csrf")
    response = client.get(url)
    assert response.status_code == 200
    assert response.data == {"detail": "ok"}
    assert "csrftoken" in response.cookies


def test_token_create_returns_contract_shape(client):
    url = reverse("accounts:telegram-token-create")
    response = client.post(url)
    assert response.status_code == 201
    body = response.data
    assert set(body.keys()) == {"token", "deep_link", "expires_at", "expires_in_seconds"}
    assert body["deep_link"].startswith("https://t.me/")
    assert body["token"] in body["deep_link"]
    assert body["expires_in_seconds"] == 600


def test_full_deep_link_flow_logs_browser_in(client):
    create_url = reverse("accounts:telegram-token-create")
    create_response = client.post(create_url)
    raw_token = create_response.data["token"]

    status_url = reverse("accounts:telegram-token-status", kwargs={"token": raw_token})
    pending_response = client.get(status_url)
    assert pending_response.status_code == 200
    assert pending_response.data == {"status": "pending"}
    assert "_auth_user_id" not in client.session

    # Simulate the bot confirming the challenge from the Telegram update.
    user, error = services.confirm_auth_challenge(raw_token, TG_ID, "diyor", "Diyorbek", "A")
    assert error is None

    confirmed_response = client.get(status_url)
    assert confirmed_response.status_code == 200
    assert confirmed_response.data == {"status": "confirmed"}
    assert str(user.id) == client.session["_auth_user_id"]

    # Polling again after confirmation must stay idempotent (no crash, no
    # re-login error, still confirmed).
    again_response = client.get(status_url)
    assert again_response.status_code == 200
    assert again_response.data == {"status": "confirmed"}


def test_status_for_unknown_token_is_expired(client):
    status_url = reverse(
        "accounts:telegram-token-status", kwargs={"token": "does-not-exist-at-all"}
    )
    response = client.get(status_url)
    assert response.status_code == 200
    assert response.data == {"status": "expired"}


def test_code_verify_happy_path_logs_browser_in(client):
    raw_code, error = services.create_login_code(TG_ID, "diyor", "Diyorbek", "A")
    assert error is None

    verify_url = reverse("accounts:telegram-code-verify")
    response = client.post(verify_url, {"code": raw_code}, format="json")
    assert response.status_code == 200
    assert response.data == {"status": "ok"}
    assert "_auth_user_id" in client.session


def test_code_verify_rejects_invalid_code(client):
    verify_url = reverse("accounts:telegram-code-verify")
    response = client.post(verify_url, {"code": "00000"}, format="json")
    assert response.status_code == 400
    assert response.data["status"] in {"invalid", "expired", "used"}


def test_code_verify_rejects_malformed_code(client):
    verify_url = reverse("accounts:telegram-code-verify")
    response = client.post(verify_url, {"code": "abc"}, format="json")
    assert response.status_code == 400
    assert response.data["status"] == "invalid"


def test_code_verify_rejects_already_used_code(client):
    raw_code, _ = services.create_login_code(TG_ID, "u", "f", "l")
    verify_url = reverse("accounts:telegram-code-verify")

    first = client.post(verify_url, {"code": raw_code}, format="json")
    assert first.status_code == 200

    second_client = APIClient()
    second = second_client.post(verify_url, {"code": raw_code}, format="json")
    assert second.status_code == 400
    assert second.data["status"] == "used"


def test_logout_clears_session(client):
    raw_code, _ = services.create_login_code(TG_ID, "u", "f", "l")
    verify_url = reverse("accounts:telegram-code-verify")
    client.post(verify_url, {"code": raw_code}, format="json")
    assert "_auth_user_id" in client.session

    logout_url = reverse("accounts:logout")
    response = client.post(logout_url)
    assert response.status_code == 200
    assert response.data == {"status": "ok"}
    assert "_auth_user_id" not in client.session


def test_me_requires_authentication(client):
    response = client.get(reverse("accounts:me"))
    assert response.status_code == 401
    assert response.data == {"detail": "not_authenticated"}


def test_me_returns_current_user_after_login(client):
    raw_code, _ = services.create_login_code(TG_ID, "diyor", "Diyorbek", "A")
    verify_url = reverse("accounts:telegram-code-verify")
    client.post(verify_url, {"code": raw_code}, format="json")

    response = client.get(reverse("accounts:me"))
    assert response.status_code == 200
    assert response.data["username"] == f"tg_{TG_ID}"
    assert response.data["first_name"] == "Diyorbek"
    assert response.data["telegram_id"] == TG_ID
    assert response.data["telegram_username"] == "diyor"


def test_me_returns_401_after_logout(client):
    raw_code, _ = services.create_login_code(TG_ID, "u", "f", "l")
    client.post(reverse("accounts:telegram-code-verify"), {"code": raw_code}, format="json")
    client.post(reverse("accounts:logout"))

    response = client.get(reverse("accounts:me"))
    assert response.status_code == 401
