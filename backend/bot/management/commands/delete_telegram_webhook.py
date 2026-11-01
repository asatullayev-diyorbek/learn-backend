from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from integrations.telegram.client import TelegramClient


class Command(BaseCommand):
    help = "Deletes the Telegram webhook so the bot can revert to polling."

    def add_arguments(self, parser):
        parser.add_argument(
            "--drop-pending-updates",
            action="store_true",
            help="Drop any pending updates queued in Telegram.",
        )

    def handle(self, *args, **options):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set in Django settings or environment.")

        drop_pending = options["drop_pending_updates"]
        client = TelegramClient(bot_token)
        try:
            result = client.delete_webhook(drop_pending_updates=drop_pending)
            self.stdout.write(self.style.SUCCESS(f"Webhook deleted successfully: {result}"))
        except Exception as exc:
            raise CommandError(f"Failed to delete webhook: {exc}")

