from aiogram import Router, F
from aiogram import Dispatcher
from aiogram.filters import CommandStart
from handlers import start_handler, contact_handler, unknown_message_handler


def setup_router(dp: Dispatcher):
    router = Router(name="main_router")
    router.message.register(start_handler, CommandStart())
    router.message.register(contact_handler, F.contact)
    router.message.register(unknown_message_handler)
    dp.include_router(router)
