"""Хэндлер команды /start."""
import logging
from datetime import datetime

from aiogram.types import Message

from bot.handlers.keyboards import phone_button
from bot.handlers.messages import WELCOME_MESSAGE
from bot.paths import VISIT_HISTORY_PATH


async def start_handler(message: Message, bot_instance) -> None:
    """Отправляет приветствие с кнопкой «поделиться номером» и пишет историю посещений."""
    user = message.from_user
    user_id = user.id
    username = user.username or None
    full_name = user.full_name or None

    logging.info(f"User logged in. | fullname={full_name}, username=@{username}, id={user_id}")

    # История посещений: timestamp;user_id;username;fullname;botname
    try:
        with open(VISIT_HISTORY_PATH, "a+", encoding="utf-8") as history:
            history.write(f"{datetime.now().isoformat()};{user_id};"
                          f"{username};{full_name};{bot_instance.botname}\n")
    except OSError:
        # Файл истории не критичен для выдачи купона — только сигнал в лог
        logging.exception(f"Не удалось записать визит пользователя id={user_id}")

    await message.answer(WELCOME_MESSAGE, reply_markup=phone_button)
