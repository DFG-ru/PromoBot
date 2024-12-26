from aiogram import types
from aiogram.types import Message
from .keyboards import phone_button
import logging


async def unknown_message_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or None
    full_name = message.from_user.full_name or None
    logging.info(f"Unknown Command from user. | fullname={full_name}, username=@{username}, id={user_id}, text=\"{str(message.text)}\"")
    await message.answer("Чтобы поделиться вашим номером нажмите кнопку ниже", reply_markup=phone_button)