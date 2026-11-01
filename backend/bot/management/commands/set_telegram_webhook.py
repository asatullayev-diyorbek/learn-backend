from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from integrations.telegram.client import TelegramClient


class Command(BaseCommand):
    help = "Registers the webhook URL with Telegram Bot API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            default="",
            help="Webhook public URL (defaults to settings.TELEGRAM_WEBHOOK_URL).",
        )
        parser.add_argument(
            "--secret",
            type=str,
            default="",
            help="Webhook secret token (defaults to settings.TELEGRAM_WEBHOOK_SECRET).",
        )
        parser.add_argument(
            "--drop-pending-updates",
            action="store_true",
            help="Drop any pending updates queued in Telegram.",
        )

    def handle(self, *args, **options):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set in Django settings or environment.")

        url = options["url"] or getattr(settings, "TELEGRAM_WEBHOOK_URL", "")
        if not url:
            raise CommandError(
                "Webhook URL not provided. Pass --url or define TELEGRAM_WEBHOOK_URL in your .env/settings."
            )

        secret = options["secret"] or getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        drop_pending = options["drop_pending_updates"]

        self.stdout.write(f"Registering webhook to: {url}")
        client = TelegramClient(bot_token)
        try:
            result = client.set_webhook(
                url=url,
                secret_token=secret or None,
                drop_pending_updates=drop_pending,
            )
            self.stdout.write(self.style.SUCCESS(f"Webhook set successfully: {result}"))
        except Exception as exc:
            raise CommandError(f"Failed to set webhook: {exc}")

