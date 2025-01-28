from aiogram import types
from aiogram.types import Message
from .keyboards import phone_button
from datetime import datetime
import logging

# Константа для приветственного сообщения
WELCOME_MESSAGE = (
    "Здравствуйте, поделитесь вашим номером по кнопке ниже, "
    "чтобы получить купон!"
)

async def start_handler(message: Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение с кнопкой, чтобы поделиться номером телефона.
    """
    user_id = message.from_user.id
    username = message.from_user.username or None
    full_name = message.from_user.full_name or None
    last_active = datetime.now().isoformat()

    # Логирование информации о пользователе
    logging.info(
        f"User logged in. | fullname={full_name}, username=@{username}, id={user_id}"
    )

    # Отправка приветственного сообщения с кнопкой, чтобы поделиться номером телефона
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=phone_button
    )
