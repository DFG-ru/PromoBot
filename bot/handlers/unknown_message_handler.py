from aiogram import types
from aiogram.types import Message
from .keyboards import phone_button
import logging

async def unknown_message_handler(message: Message):
    """
    Обработчик неизвестных сообщений.
    Предлагает пользователю поделиться своим номером телефона.
    """
    user_id = message.from_user.id
    username = message.from_user.username or None
    full_name = message.from_user.full_name or None
    text = message.text

    # Логирование информации о пользователе и сообщении
    logging.info(
        f"Unknown Command from user. | fullname={full_name}, username=@{username}, id={user_id}, text=\"{text}\""
    )

    # Отправка сообщения с кнопкой для поделки номера телефона
    await message.answer(
        "Чтобы поделиться вашим номером нажмите кнопку ниже",
        reply_markup=phone_button
    )
