"""Thin synchronous Telegram Bot API HTTP client.

Not used by the two login flows (the bot's own aiogram Bot instance sends
those replies), but kept real and minimal for anything outside the bot's
event loop that needs to push a message to a chat (e.g. a Django view or a
management command notifying a user).
"""

import requests

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramClient:
    def __init__(self, bot_token: str, timeout: float = 10.0):
        self._bot_token = bot_token
        self._timeout = timeout
        self._base_url = f"{TELEGRAM_API_BASE}/bot{bot_token}"

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
        response = requests.post(
            f"{self._base_url}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()
