from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import services as bot_services

router = Router(name="login")


@router.message(Command("login"))
async def handle_login(message: Message):
    from_user = message.from_user
    raw_code, error = await bot_services.create_login_code(
        from_user.id,
        from_user.username or "",
        from_user.first_name or "",
        from_user.last_name or "",
    )

    if error == "rate_limited":
        await message.answer(
            "Juda tez-tez so'rov yuborilyapti. Iltimos, biroz kuting va "
            "yana urinib ko'ring."
        )
        return

    await message.answer(
        f"Kodingiz: <b>{raw_code}</b>\nKod 5 daqiqa amal qiladi."
    )
