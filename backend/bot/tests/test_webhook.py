import json
from unittest.mock import AsyncMock, patch

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_webhook_get_not_allowed():
    client = Client()
    url = reverse("bot:telegram-webhook")
    response = client.get(url)
    assert response.status_code == 405


@pytest.mark.django_db
def test_webhook_invalid_json(settings):
    settings.TELEGRAM_BOT_TOKEN = "test-token"
    settings.TELEGRAM_WEBHOOK_SECRET = ""
    client = Client()
    url = reverse("bot:telegram-webhook")
    response = client.post(
        url,
        data="not-a-json",
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False


@pytest.mark.django_db
def test_webhook_secret_token_validation(settings):
    settings.TELEGRAM_BOT_TOKEN = "123456:test"
    settings.TELEGRAM_WEBHOOK_SECRET = "super-secret"
    client = Client()
    url = reverse("bot:telegram-webhook")

    # Missing header
    res_missing = client.post(
        url,
        data=json.dumps({"update_id": 1}),
        content_type="application/json",
    )
    assert res_missing.status_code == 403

    # Wrong header
    res_wrong = client.post(
        url,
        data=json.dumps({"update_id": 1}),
        content_type="application/json",
        HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="wrong-secret",
    )
    assert res_wrong.status_code == 403

    # Correct header
    with patch("bot.views.dispatcher.feed_raw_update", new_callable=AsyncMock) as mock_feed:
        res_ok = client.post(
            url,
            data=json.dumps({"update_id": 1}),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="super-secret",
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["ok"] is True
        mock_feed.assert_awaited_once()


@pytest.mark.django_db
def test_webhook_missing_bot_token(settings):
    settings.TELEGRAM_BOT_TOKEN = ""
    settings.TELEGRAM_WEBHOOK_SECRET = ""
    client = Client()
    url = reverse("bot:telegram-webhook")
    response = client.post(
        url,
        data=json.dumps({"update_id": 1}),
        content_type="application/json",
    )
    assert response.status_code == 503
    assert response.json()["ok"] is False


@pytest.mark.django_db
def test_webhook_successful_update_processing(settings):
    settings.TELEGRAM_BOT_TOKEN = "123456:test"
    settings.TELEGRAM_WEBHOOK_SECRET = ""
    client = Client()
    url = reverse("bot:telegram-webhook")

    payload = {
        "update_id": 123456,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 111, "type": "private"},
            "from": {"id": 111, "is_bot": False, "first_name": "Test"},
            "text": "/start",
        },
    }

    with patch("bot.views.dispatcher.feed_raw_update", new_callable=AsyncMock) as mock_feed:
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        mock_feed.assert_awaited_once()


def test_management_command_set_webhook(settings):
    settings.TELEGRAM_BOT_TOKEN = "123456:test"
    settings.TELEGRAM_WEBHOOK_URL = "https://example.com/api/telegram/webhook/"
    settings.TELEGRAM_WEBHOOK_SECRET = "sec"

    with patch("integrations.telegram.client.TelegramClient.set_webhook") as mock_set:
        mock_set.return_value = {"ok": True, "result": True, "description": "Webhook was set"}
        call_command("set_telegram_webhook")
        mock_set.assert_called_once_with(
            url="https://example.com/api/telegram/webhook/",
            secret_token="sec",
            drop_pending_updates=False,
        )


def test_management_command_delete_webhook(settings):
    settings.TELEGRAM_BOT_TOKEN = "123456:test"

    with patch("integrations.telegram.client.TelegramClient.delete_webhook") as mock_delete:
        mock_delete.return_value = {"ok": True, "result": True, "description": "Webhook was deleted"}
        call_command("delete_telegram_webhook", drop_pending_updates=True)
        mock_delete.assert_called_once_with(drop_pending_updates=True)


def test_management_command_get_webhook_info(settings):
    settings.TELEGRAM_BOT_TOKEN = "123456:test"

    with patch("integrations.telegram.client.TelegramClient.get_webhook_info") as mock_info:
        mock_info.return_value = {
            "ok": True,
            "result": {"url": "https://example.com/api/telegram/webhook/", "has_custom_certificate": False},
        }
        call_command("get_telegram_webhook_info")
        mock_info.assert_called_once()


@pytest.mark.django_db
def test_webhook_executes_start_command_flow(settings):
    from apps.accounts.models import TelegramAuthChallenge
    from apps.accounts.services import create_auth_challenge

    settings.TELEGRAM_BOT_TOKEN = "123456:test"
    settings.TELEGRAM_WEBHOOK_SECRET = ""

    raw_token, _ = create_auth_challenge()

    payload = {
        "update_id": 999,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 88888, "type": "private"},
            "from": {
                "id": 88888,
                "is_bot": False,
                "first_name": "Vali",
                "last_name": "Aliyev",
                "username": "valiyev",
            },
            "text": f"/start {raw_token}",
        },
    }

    client = Client()
    url = reverse("bot:telegram-webhook")

    with patch("aiogram.types.Message.answer", new_callable=AsyncMock) as mock_answer:
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        mock_answer.assert_awaited_once()
        assert "Tasdiqlandi" in mock_answer.call_args[0][0]

    # Verify database state was updated
    challenge = TelegramAuthChallenge.objects.filter(telegram_id=88888).first()
    assert challenge is not None
    assert challenge.status == TelegramAuthChallenge.STATUS_CONFIRMED
    assert challenge.user.username == "tg_88888"


@pytest.mark.django_db
def test_webhook_executes_login_command_flow(settings):
    from apps.accounts.models import TelegramLoginCode

    settings.TELEGRAM_BOT_TOKEN = "123456:test"
    settings.TELEGRAM_WEBHOOK_SECRET = ""

    payload = {
        "update_id": 1000,
        "message": {
            "message_id": 2,
            "date": 1700000000,
            "chat": {"id": 77777, "type": "private"},
            "from": {
                "id": 77777,
                "is_bot": False,
                "first_name": "Gani",
                "username": "ganiyev",
            },
            "text": "/login",
        },
    }

    client = Client()
    url = reverse("bot:telegram-webhook")

    with patch("aiogram.types.Message.answer", new_callable=AsyncMock) as mock_answer:
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        mock_answer.assert_awaited_once()
        assert "Kodingiz:" in mock_answer.call_args[0][0]

    # Verify login code was created in database
    code_obj = TelegramLoginCode.objects.filter(telegram_id=77777).first()
    assert code_obj is not None
