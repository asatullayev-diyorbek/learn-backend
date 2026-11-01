import json
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.views.decorators.csrf import csrf_exempt

from bot import config as bot_config
from bot.dispatcher import dispatcher

logger = logging.getLogger(__name__)


@csrf_exempt
async def telegram_webhook_view(request: HttpRequest) -> HttpResponse:
    """Telegram webhook endpoint that receives updates and feeds them to aiogram."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", bot_config.WEBHOOK_SECRET)
    if secret:
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_secret != secret:
            logger.warning("Telegram webhook secret mismatch")
            return HttpResponseForbidden("Invalid secret token")

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", bot_config.BOT_TOKEN)
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured")
        return JsonResponse({"ok": False, "error": "Bot token not configured"}, status=503)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("Invalid JSON in telegram webhook: %s", e)
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    try:
        async with Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        ) as bot:
            await dispatcher.feed_raw_update(bot, payload)
    except Exception as e:
        logger.exception("Error processing telegram update: %s", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=200)

    return JsonResponse({"ok": True})

