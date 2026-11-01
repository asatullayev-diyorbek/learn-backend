import logging

from aiogram import F, Router
from aiogram.types import Message
from django.conf import settings

from bot import services as bot_services

logger = logging.getLogger(__name__)

router = Router(name="video")


@router.message(F.video)
async def handle_video_submission(message: Message):
    """Handle incoming student video submissions."""
    video = message.video
    if not video:
        return

    from_user = message.from_user
    submission = await bot_services.create_submission_from_telegram(
        telegram_id=from_user.id,
        file_id=video.file_id,
        username=from_user.username or "",
        first_name=from_user.first_name or "",
        last_name=from_user.last_name or "",
    )

    review_channel = getattr(settings, "TELEGRAM_REVIEW_CHANNEL_ID", "")
    if review_channel:
        try:
            # Forward / copy to admin review channel
            caption = (
                f"📹 <b>Yangi video kelib tushdi!</b>\n\n"
                f"👤 <b>O'quvchi:</b> {from_user.full_name} (@{from_user.username or 'yoqdari'})\n"
                f"🆔 <b>Telegram ID:</b> <code>{from_user.id}</code>\n"
                f"📌 <b>Submission ID:</b> #{submission.id}\n"
                f"⏳ <i>O'quvchi sayt orqali mavzuga biriktirishi kutilmoqda.</i>"
            )
            await message.send_copy(chat_id=review_channel, caption=caption, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Could not copy video to review channel %s: %s", review_channel, exc)

    await message.answer(
        "📹 <b>Videongiz qabul qilindi!</b>\n\n"
        "Keyingi qadam: Learn platformasiga (saytga) kiring va "
        "<b>'Mening videolarim'</b> bo'limida ushbu videoni tegishli kurs "
        "mavzusiga biriktiring (bind qiling).\n\n"
        "Mavzuga biriktirilgach, video ko'rib chiqish navbatiga o'tadi.",
        parse_mode="HTML",
    )
