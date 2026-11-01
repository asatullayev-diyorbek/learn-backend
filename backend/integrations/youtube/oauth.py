"""Google OAuth2 helper for YouTube Data API v3.

Reads refresh token and client credentials from environment or client secret file,
and exchanges them for a short-lived access token.
"""

import json
import logging
import os
from typing import Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def _read_client_credentials() -> Tuple[str, str]:
    """Read client_id and client_secret from env or client_secrets.json."""
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")

    if client_id and client_secret:
        return client_id, client_secret

    secrets_file = getattr(settings, "YOUTUBE_CLIENT_SECRETS_FILE", "")
    if secrets_file and os.path.exists(secrets_file):
        try:
            with open(secrets_file, "r") as f:
                data = json.load(f)
            web_or_installed = data.get("installed") or data.get("web") or {}
            return web_or_installed.get("client_id", ""), web_or_installed.get("client_secret", "")
        except Exception as exc:
            logger.warning("Error reading YOUTUBE_CLIENT_SECRETS_FILE: %s", exc)

    return "", ""


def get_access_token() -> Optional[str]:
    """Exchange refresh token for a fresh access token."""
    refresh_token = getattr(settings, "YOUTUBE_REFRESH_TOKEN", "") or os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
    if not refresh_token:
        return None

    client_id, client_secret = _read_client_credentials()
    if not client_id or not client_secret:
        logger.warning("YouTube client credentials not configured.")
        return None

    try:
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as exc:
        logger.error("Failed to refresh Google OAuth2 access token: %s", exc)
        return None

