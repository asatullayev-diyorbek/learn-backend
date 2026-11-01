import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from integrations.telegram.client import TelegramClient


class Command(BaseCommand):
    help = "Gets current Telegram webhook status and info."

    def handle(self, *args, **options):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set in Django settings or environment.")

        client = TelegramClient(bot_token)
        try:
            info = client.get_webhook_info()
            self.stdout.write(self.style.SUCCESS(json.dumps(info, indent=2)))
        except Exception as exc:
            raise CommandError(f"Failed to fetch webhook info: {exc}")

