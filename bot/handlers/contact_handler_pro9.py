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
        coupon_code = userDB.get_user_coupon(contact.phone_number)
        new_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
        userDB.update(contact.phone_number, new_data)
        qr_file_name = f"middlewares/output/{coupon_code[-6:]}.jpg"
        if not os.path.exists(qr_file_name):
            couponGen(template, coupon_code)
        qr_file = FSInputFile(qr_file_name)
        logging.info(f"User received an existing coupon. | fullname={full_name}, username=@{username}, id={user_id}, coupon=\"{coupon_code}\"")
        await message.answer_photo(photo=qr_file, caption="О! У вас уже есть купон! Вот он:", reply_markup=ReplyKeyboardRemove())
    else:
        coupon_code = couponDB.get_random_coupon_code(couponMask)
        if coupon_code != '':
            couponGen(template, coupon_code)
            userDB.write(user.id, user.first_name, user.last_name, user.username, contact.phone_number, coupon_code)
            qr_file_name = f"middlewares/output/{coupon_code[-6:]}.jpg"
            qr_file = FSInputFile(qr_file_name)
            logging.info(f"User received a new coupon. | fullname={full_name}, username=@{username}, id={user_id}, coupon=\"{coupon_code}\"")
            await message.answer_photo(photo=qr_file, caption="Ваш купон:", reply_markup=ReplyKeyboardRemove())
        else:
            logging.info(f"User did not receive coupon. Coupons are out. | fullname={full_name}, username=@{username}, id={user_id}, coupon=\"{coupon_code}\"")
            await message.answer("Извините, закончились купоны. Бежим за новыми!", reply_markup=types.ReplyKeyboardRemove())