"""aiogram v3 polling entrypoint for the Learn Telegram bot.

Run with: python -m bot.main (from the backend/ directory, with the venv
active and TELEGRAM_BOT_TOKEN set).
"""

import asyncio
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

# django.setup() MUST run before anything below imports Django models.
django.setup()

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402

from bot.config import BOT_TOKEN  # noqa: E402
from bot.handlers import login, start  # noqa: E402


async def _run():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(login.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
