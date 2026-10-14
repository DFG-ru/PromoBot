"""Сборка диспетчера: единый роутер с регистрацией всех хэндлеров."""
from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandStart

from bot.handlers import contact_handler, start_handler, unknown_message_handler


def setup_router(dp: Dispatcher) -> None:
    router = Router(name="main_router")
    router.message.register(start_handler, CommandStart())
    router.message.register(contact_handler, F.contact)
    router.message.register(unknown_message_handler)
    dp.include_router(router)
