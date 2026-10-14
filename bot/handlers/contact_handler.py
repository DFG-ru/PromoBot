"""Хэндлер входящего контакта: регистрация пользователя и выдача купона."""
import logging

from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove

from bot.handlers.messages import (
    COUPONS_EXHAUSTED_TEMPLATE,
    COUPONS_TEMPORARILY_UNAVAILABLE,
    COUPON_RENDER_ERROR,
    PROMO_ENDED_TEMPLATE,
    YOUR_COUPON,
    follow_channel_text,
    promo_deadline_text,
)
from bot.middlewares import coupon_codes, coupon_generator, user_database

REMOVE_KEYBOARD = ReplyKeyboardRemove()


def _log_user(user) -> str:
    return f"fullname={user.full_name}, username=@{user.username or None}, id={user.id}"


async def _register_user(message: Message, bot_instance) -> None:
    """Создаёт запись пользователя или обновляет данные существующего."""
    contact = message.contact
    user = message.from_user

    if await user_database.phone_exist(contact.phone_number):
        logging.info(f"Existing user found, data updated. | {_log_user(user)}")
        await user_database.update(contact.phone_number, {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        })
    else:
        logging.info(f"New user authorized. | {_log_user(user)}")
        await user_database.write(user.id, user.first_name, user.last_name,
                                  user.username, contact.phone_number)


async def _issue_new_coupon(message: Message, bot_instance, phone_number: str) -> str | None:
    """Выбирает свободный код по маске бота и привязывает его к пользователю."""
    # Окно акции определяется конфигом: today() <= promo_end_date.
    # Если дата не задана или некорректна — выдача закрыта (безопасно по умолчанию).
    if not bot_instance.promo_active:
        logging.info(f"Окно акции закрыто (promo_end_date={bot_instance.promo_end_date}) | "
                     f"{_log_user(message.from_user)}")
        await message.answer(PROMO_ENDED_TEMPLATE + follow_channel_text(bot_instance.social_media_url),
                             reply_markup=REMOVE_KEYBOARD)
        return None

    try:
        coupon_code = await coupon_codes.get_random_coupon_code(bot_instance.coupon_mask)
    except FileNotFoundError:
        logging.error("Файл CouponCodes.txt не найден — выдача купонов невозможна")
        await message.answer(COUPONS_TEMPORARILY_UNAVAILABLE, reply_markup=REMOVE_KEYBOARD)
        return None
    except ValueError:
        logging.warning("Свободные купоны закончились")
        await message.answer(COUPONS_EXHAUSTED_TEMPLATE + follow_channel_text(bot_instance.social_media_url),
                             reply_markup=REMOVE_KEYBOARD)
        return None

    bound = await user_database.update_coupon(phone_number, {"coupon_code": coupon_code})
    logging.debug(f"Привязка купона {coupon_code!r} к телефону в базе: "
                  f"{'успешно' if bound else 'НЕ найдена запись'}")
    logging.info(f"User received a new coupon. | {_log_user(message.from_user)}, coupon=\"{coupon_code}\"")
    return coupon_code


async def _render_coupon(message: Message, bot_instance, coupon_code: str) -> bool:
    """Гарантирует существование файла купона; при необходимости генерирует его."""
    qr_file_name = coupon_generator.OUTPUT_DIR / f"{coupon_code[-6:]}.jpg"
    if qr_file_name.is_file():
        logging.debug(f"Файл купона уже существует, генерация пропущена: {qr_file_name}")
        return True

    logging.info(f"Generating QR code for coupon: {coupon_code}")
    success = await coupon_generator.generate_coupon_image(
        bot_instance.template, str(coupon_code), font=bot_instance.font)
    if not success:
        logging.error(f"Не удалось сгенерировать купон: {coupon_code}")
        await message.answer(COUPON_RENDER_ERROR, reply_markup=REMOVE_KEYBOARD)
    return success


async def contact_handler(message: Message, bot_instance) -> None:
    """Основной сценарий: пользователь делится номером -> получает купон с QR-кодом."""
    contact = message.contact
    user = message.from_user
    logging.info(f"User logged in. | {_log_user(user)}")
    logging.debug(f"contact_handler старт | id={user.id}, phone={contact.phone_number}, "
                  f"coupon_mask={bot_instance.coupon_mask!r}, template={bot_instance.template!r}, "
                  f"promo_active={bot_instance.promo_active}")

    await _register_user(message, bot_instance)

    # Уже выданный ранее купон или новый
    coupon_code = await user_database.get_user_coupon(contact.phone_number,
                                                      bot_instance.coupon_mask)
    logging.debug(f"Купон пользователя из базы: {coupon_code!r} | id={user.id}")
    if coupon_code is None:
        coupon_code = await _issue_new_coupon(message, bot_instance, contact.phone_number)
        if coupon_code is None:
            return

    if not await _render_coupon(message, bot_instance, coupon_code):
        return

    # Отправка купона пользователю
    logging.info(f"User received coupon. | {_log_user(user)}, coupon=\"{coupon_code}\"")
    await message.answer(YOUR_COUPON, reply_markup=REMOVE_KEYBOARD)
    await message.answer_photo(photo=FSInputFile(str(
        coupon_generator.OUTPUT_DIR / f"{coupon_code[-6:]}.jpg")), reply_markup=REMOVE_KEYBOARD)
    await message.answer(
        f"🎉{promo_deadline_text(bot_instance.promo_end_date)}\n\n"
        + follow_channel_text(bot_instance.social_media_url),
        reply_markup=REMOVE_KEYBOARD,
    )
    logging.debug(f"contact_handler завершён | id={user.id}, coupon={coupon_code!r}")
