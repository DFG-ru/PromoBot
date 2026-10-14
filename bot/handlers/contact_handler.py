import logging
import os

from aiogram import types
from aiogram.types import Message, Contact, FSInputFile, ReplyKeyboardRemove

from middlewares import couponGen
from middlewares import couponCodes_funcs as couponDB
from middlewares import userDatabase_funcs as userDB
from middlewares.couponGen import OUTPUT_DIR

# Контактные данные из конфига бота (bot_instance.social_media_url / website_url)
# подставляются в финальное сообщение вместо захардкоженных ссылок.


def _promo_deadline_text(bot_instance) -> str:
    """Формирует текст о дедлайне купона из конфигурации (promo_end_date)."""
    if bot_instance.promo_end_date is not None:
        return f"Вы можете использовать купон до {bot_instance.promo_end_date.strftime('%d.%m.%Y')} включительно."
    return "Сроки действия купона уточняйте у организаторов акции."


async def contact_handler(message: Message, bot_instance):
    """
    Обработчик контактов.
    Обновляет данные пользователя или добавляет нового пользователя и проверяет наличие купона.
    """
    contact: Contact = message.contact
    user_id = message.from_user.id
    user = message.from_user
    username = user.username or None
    full_name = user.full_name or None

    # Логирование информации о пользователе
    logging.info(f"User logged in. | fullname={full_name}, username=@{username}, id={user_id}")
    logging.debug(f"contact_handler старт | id={user_id}, phone={contact.phone_number}, "
                  f"coupon_mask={bot_instance.coupon_mask!r}, template={bot_instance.template!r}, "
                  f"promo_active={bot_instance.promo_active}")

    # Проверка наличия номера телефона в базе данных пользователей
    if await userDB.phone_exist(contact.phone_number) and await userDB.coupon_exist(user_id, bot_instance.coupon_mask):
        logging.info(f"Existing user found, data updated. | fullname={full_name}, username=@{username}, id={user_id}")
        logging.debug(f"Существующий пользователь с купоном: id={user_id}, обновляю данные")
        new_data = {
            'user_id': user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
        await userDB.update(contact.phone_number, new_data)
    else:
        logging.info(f"New user authorized. | fullname={full_name}, username=@{username}, id={user_id}")
        logging.debug(f"Новый пользователь (или без купона): id={user_id}, записываю в базу")
        await userDB.write(user.id, user.first_name, user.last_name, user.username, contact.phone_number)

    # Получение купона для пользователя
    coupon_code = await userDB.get_user_coupon(contact.phone_number, bot_instance.coupon_mask)
    logging.debug(f"Купон пользователя из базы: {coupon_code!r} | id={user_id}")

    if coupon_code is None:
        # Окно акции определяется конфигом: date.today() <= promo_end_date.
        # Если дата не задана или некорректна — выдача закрыта (безопасно по умолчанию).
        if not bot_instance.promo_active:
            logging.debug(f"Окно акции закрыто (promo_end_date={bot_instance.promo_end_date}), "
                          f"выдача купонов недоступна | id={user_id}")
            await message.answer(
                "Выдача купонов завершена.\n"
                "\n"
                f"Следите за новыми предложениями в нашем телеграмм канале:\n"
                f"\n"
                f"{bot_instance.social_media_url}\n"
                f"💎💎💎\n",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        try:
            coupon_code = await couponDB.get_random_coupon_code(bot_instance.coupon_mask)
        except FileNotFoundError:
            logging.error("Файл CouponCodes.txt не найден — выдача купонов невозможна")
            await message.answer(
                "Купоны временно недоступны. Попробуйте позже.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        except ValueError:
            logging.warning("Свободные купоны закончились")
            await message.answer(
                "К сожалению, все купоны уже разыграны.\n"
                "\n"
                f"Следите за новыми предложениями в нашем телеграмм канале:\n"
                f"\n"
                f"{bot_instance.social_media_url}\n"
                f"💎💎💎\n",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        new_data = {
            'coupon_code': coupon_code
        }
        update_result = await userDB.update_coupon(contact.phone_number, new_data)
        logging.debug(f"Привязка купона {coupon_code!r} к телефону в базе: "
                      f"{'успешно' if update_result else 'НЕ найдена запись'} | id={user_id}")
        logging.info(f"User received a new coupon. | fullname={full_name}, username=@{username}, id={user_id}, coupon=\"{coupon_code}\"")

    qr_file_name = OUTPUT_DIR / f"{coupon_code[-6:]}.jpg"
    logging.debug(f"Ожидаемый файл купона: {qr_file_name} | id={user_id}")

    # Генерация QR-кода, если файл не существует
    if not os.path.exists(qr_file_name):
        logging.info(f"Generating QR code for coupon: {coupon_code}")
        logging.debug(f"Файл купона отсутствует, запускаю couponGen "
                      f"(template={bot_instance.template!r}, font={bot_instance.font!r})")
        if not await couponGen.couponGen(bot_instance.template, str(coupon_code), font=bot_instance.font):
            logging.error(f"Не удалось сгенерировать купон: {coupon_code}")
            await message.answer(
                "Не удалось сформировать ваш купон. Попробуйте позже.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        logging.debug(f"couponGen успешно завершён: {coupon_code}")
    else:
        logging.debug(f"Файл купона уже существует, генерация пропущена: {qr_file_name}")

    # Отправка купона пользователю
    qr_file = FSInputFile(str(qr_file_name))
    logging.info(f"User received coupon. | fullname={full_name}, username=@{username}, id={user_id}, coupon=\"{coupon_code}\"")
    logging.debug(f"Отправка купона пользователю | id={user_id}, coupon={coupon_code!r}, файл={qr_file_name}")
    await message.answer(
        "Ваш купон:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer_photo(photo=qr_file, reply_markup=ReplyKeyboardRemove())
    await message.answer(
        f"🎉{_promo_deadline_text(bot_instance)}\n"
        "\n"
        f"Следите за новыми предложениями в нашем телеграмм канале:\n"
        f"\n"
        f"{bot_instance.social_media_url}\n"
        f"💎💎💎\n",
        reply_markup=types.ReplyKeyboardRemove()
    )
    logging.debug(f"contact_handler завершён | id={user_id}, coupon={coupon_code!r}")
