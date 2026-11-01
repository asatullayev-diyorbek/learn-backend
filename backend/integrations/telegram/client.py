"""Thin synchronous Telegram Bot API HTTP client.

Not used by the two login flows (the bot's own aiogram Bot instance sends
those replies), but kept real and minimal for anything outside the bot's
event loop that needs to push a message or manage webhooks (e.g. Django views
or management commands).
"""

from typing import Any, Dict, Optional
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

    def set_webhook(
        self,
        url: str,
        secret_token: Optional[str] = None,
        drop_pending_updates: bool = False,
    ) -> Dict[str, Any]:
        """Configure Telegram to deliver updates to url via webhook."""
        payload: Dict[str, Any] = {
            "url": url,
            "drop_pending_updates": drop_pending_updates,
        }
        if secret_token:
            payload["secret_token"] = secret_token

        response = requests.post(
            f"{self._base_url}/setWebhook",
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def delete_webhook(self, drop_pending_updates: bool = False) -> Dict[str, Any]:
        """Remove webhook integration, returning bot to polling mode."""
        payload = {"drop_pending_updates": drop_pending_updates}
        response = requests.post(
            f"{self._base_url}/deleteWebhook",
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_webhook_info(self) -> Dict[str, Any]:
        """Retrieve current webhook status and diagnostics from Telegram."""
        response = requests.get(
            f"{self._base_url}/getWebhookInfo",
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_file(self, file_id: str) -> Dict[str, Any]:
        """Fetch file metadata including file_path from Telegram."""
        response = requests.get(
            f"{self._base_url}/getFile",
            params={"file_id": file_id},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def download_file(self, file_path: str, destination_path: str) -> None:
        """Download file content from Telegram to destination file."""
        file_url = f"{TELEGRAM_API_BASE}/file/bot{self._bot_token}/{file_path}"
        with requests.get(file_url, stream=True, timeout=self._timeout * 3) as r:
            r.raise_for_status()
            with open(destination_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
