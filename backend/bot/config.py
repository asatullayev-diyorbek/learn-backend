import os
from django.conf import settings

def _get_setting(name: str, default: str = "") -> str:
    if settings.configured:
        return getattr(settings, name, os.environ.get(name, default))
    return os.environ.get(name, default)

BOT_TOKEN = _get_setting("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME = _get_setting("TELEGRAM_BOT_USERNAME", "")
WEBHOOK_SECRET = _get_setting("TELEGRAM_WEBHOOK_SECRET", "")
WEBHOOK_URL = _get_setting("TELEGRAM_WEBHOOK_URL", "")
