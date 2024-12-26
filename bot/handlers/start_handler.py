from aiogram import types
from aiogram.types import Message
from .keyboards import phone_button
from datetime import datetime
import logging


async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or None
    full_name = message.from_user.full_name or None
    last_active = datetime.now().isoformat()
    logging.info(f"User logged in. | fullname={full_name}, username=@{username}, id={user_id}")
    await message.answer("Здравствуйте, поделитесь вашим номером по кнопке ниже, чтобы получить купон!", reply_markup=phone_button)