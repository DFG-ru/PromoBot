from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

phone_button = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='Поделиться номером ☎️', request_contact=True),
    ]
], resize_keyboard=True)



