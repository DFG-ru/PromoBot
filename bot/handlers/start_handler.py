from pathlib import Path
import os
from aiogram import types
from aiogram.types import Message
from .keyboards import phone_button
from datetime import datetime
# from middlewares import userDatabase_funcs as userDB
import logging

import aiofiles

# Константа для приветственного сообщения
WELCOME_MESSAGE = (
    "Здравствуйте! Чтобы получить купон, поделитесь номером телефона с помощью кнопки ниже⬇️⬇️⬇️"
)

async def start_handler(message: Message, bot_instance):
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
    # logging.info(f"New user authorized. | fullname={full_name}, username=@{username}, id={user_id}")
    # userDB.write(user.id, user.first_name, user.last_name, user.username, contact.phone_number)
    # Отправка приветственного сообщения с кнопкой, чтобы поделиться номером телефона
    visit_history_path = Path('data') / 'VisitHistory.txt'
    visit_history_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(visit_history_path, 'a+', encoding='utf-8') as used_codes:

            await used_codes.write(f"{last_active};{user_id};{username};{full_name};{bot_instance.botname}\n")  # добавляем код с новой строкой
    
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=phone_button
    )
