from aiogram import Dispatcher
from bot.handlers import login, start, video


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(login.router)
    dp.include_router(video.router)
    return dp


dispatcher = create_dispatcher()

