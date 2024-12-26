from aiogram import Router, F
from aiogram.filters import CommandStart
from handlers import start_handler, contact_handler_pro9, unknown_message_handler

router = Router()
router.message.register(start_handler, CommandStart())
router.message.register(contact_handler_pro9, F.contact)
router.message.register(unknown_message_handler)
# router.message.register(<хендлер>, Command(commands=["<команда>"]))