"""Клавиатуры бота."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Кнопка для отправки контакта (номера телефона)
share_phone_button = KeyboardButton(text="Поделиться номером ☎", request_contact=True)

# Клавиатура с одной кнопкой
phone_button = ReplyKeyboardMarkup(
    keyboard=[[share_phone_button]],
    resize_keyboard=True,
)
