import csv
import os
from aiogram import F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, Contact, FSInputFile, ReplyKeyboardRemove
from middlewares import couponGen
from middlewares import couponCodes_funcs as couponDB
from middlewares import userDatabase_funcs as userDB
import logging

template = 'pro9_substrate.jpg'
couponMask = '9082024'

async def contact_handler_pro9(message: Message):
    contact: Contact = message.contact
    user_id = message.from_user.id
    user = message.from_user
    username = message.from_user.username or None
    full_name = message.from_user.full_name or None
    if userDB.phone_exist(contact.phone_number):
        logging.info(f"Existing user found, data updated. | fullname={full_name}, username=@{username}, id={user_id}")
        new_data = {
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
        userDB.update(contact.phone_number, new_data)
    else:
        logging.info(f"New user authorized. | fullname={full_name}, username=@{username}, id={user_id}")
        userDB.write(user.id, user.first_name, user.last_name, user.username, contact.phone_number)
    if not userDB.coupon_exist(contact.phone_number):
        logging.info(f"User did not receive coupon. The promotion has ended. | fullname={full_name}, username=@{username}, id={user_id}")
        await message.answer("Выдача купонов завершена.\n" +
        "Следите за новыми предложениями в наших соц. сетях и на сайте:\n" +
        "Вконтакте: https://vk.com/pro9_rest\n" +
        "Наш сайт: https://prosecco9.ru/", reply_markup=types.ReplyKeyboardRemove())
        return
    coupon_code = userDB.get_user_coupon(contact.phone_number)
    qr_file_name = f"middlewares/output/{coupon_code[-6:]}.jpg"
    if not os.path.exists(qr_file_name):
        couponGen(template, coupon_code)
    qr_file = FSInputFile(qr_file_name)
    logging.info(f"User received an existing coupon. | fullname={full_name}, username=@{username}, id={user_id}, coupon=\"{coupon_code}\"")
    await message.answer("О! У вас есть купон!\n" +
        "Вы можете его использовать до конца января 2025 года.\n" +
        "\n" +
        "Выдача новых купонов завершена.\n" +
        "Следите за новыми предложениями в наших соц. сетях и на сайте:\n" +
        "Вконтакте: https://vk.com/pro9_rest\n" +
        "Наш сайт: https://prosecco9.ru/\n" +
        "\n" +
        "Ваш купон:", reply_markup=types.ReplyKeyboardRemove())
    await message.answer_photo(photo=qr_file, reply_markup=ReplyKeyboardRemove())