from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from bot import services as bot_services

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject):
    raw_token = command.args

    if not raw_token:
        await message.answer(
            "Salom! Saytga kirish uchun avval learn platformasidagi "
            "\"Telegram orqali kirish\" tugmasini bosing, so'ng shu yerga "
            "qaytib kelasiz."
        )
        return

    # Only the real Telegram-provided numeric id/username/names are trusted
    # for identity -- never anything from the token text itself.
    from_user = message.from_user
    user, error = await bot_services.confirm_auth_challenge(
        raw_token,
        from_user.id,
        from_user.username or "",
        from_user.first_name or "",
        from_user.last_name or "",
    )

    if error == "not_found" or error == "used":
        await message.answer(
            "Bu havola allaqachon ishlatilgan yoki noto'g'ri. Saytda "
            "qaytadan urinib ko'ring."
        )
        return

    if error == "expired":
        await message.answer(
            "Havolaning amal qilish muddati tugagan. Saytda yangi havola "
            "oling va qaytadan urinib ko'ring."
        )
        return

    await message.answer(
        "Tasdiqlandi! Endi saytga qaytib, kirish amalga oshirilganini "
        "ko'rishingiz mumkin."
    )
