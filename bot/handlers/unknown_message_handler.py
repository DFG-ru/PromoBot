"""Хэндлер сообщений, не распознанных роутером."""
import logging

from aiogram.types import Message

from bot.handlers.keyboards import phone_button
from bot.handlers.messages import UNKNOWN_MESSAGE


async def unknown_message_handler(message: Message) -> None:
    """Предлагает пользователю поделиться номером телефона по кнопке."""
    user = message.from_user
    logging.info(
        f"Unknown Command from user. | fullname={user.full_name}, "
        f"username=@{user.username or None}, id={user.id}, text=\"{message.text}\""
    )
    await message.answer(UNKNOWN_MESSAGE, reply_markup=phone_button)
