from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создание кнопки для отправки контакта
share_phone_button = KeyboardButton(text='Поделиться номером ☎', request_contact=True)

# Создание клавиатуры с кнопкой
phone_button = ReplyKeyboardMarkup(
    keyboard=[[share_phone_button]],
    resize_keyboard=True
)
