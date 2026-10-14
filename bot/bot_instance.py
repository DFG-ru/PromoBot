import datetime
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import ErrorEvent

from config_loader import mask_token
from routers import setup_router


class BotInstance:
    def __init__(self, token: str, template: str, coupon_mask: str, social_media_url: str,
                 website_url: str, promo_end_date: str | None = None, font: str | None = None):
        """Экземпляр бота.

        Имя бота (botname) определяется автоматически через get_me() в run(),
        поэтому отдельный Bot + get_me() в main.py больше не нужен —
        один экземпляр Bot на бота.

        promo_end_date — дата окончания акции из конфига (ГГГГ-ММ-ДД).
        Валидируется сразу при создании, чтобы опечатка в конфиге была
        видна в логе с именем/токеном бота, а не приводила к тихому
        закрытию выдачи купонов.
        """
        self.token = token
        self.botname = None
        self.template = template
        self.coupon_mask = coupon_mask
        self.social_media_url = social_media_url
        self.website_url = website_url
        self.font = font
        self.promo_end_date = None
        self.set_promo_end_date(promo_end_date)
        self.dp = Dispatcher()
        self.init_done = False

    def set_promo_end_date(self, value):
        """Парсит и сохраняет дату окончания акции; при ошибке — выдача закрыта."""
        logging.debug(f"set_promo_end_date({value!r}) для бота {mask_token(self.token)}")
        if not value:
            return
        try:
            self.promo_end_date = datetime.datetime.strptime(str(value), "%Y-%m-%d").date()
            logging.debug(f"Дата окончания акции установлена: {self.promo_end_date}")
        except ValueError:
            logging.error(
                f"Некорректная дата promo_end_date {value!r} у бота "
                f"{mask_token(self.token)} (ожидается ГГГГ-ММ-ДД) — "
                f"выдача купонов считается закрытой"
            )
            self.promo_end_date = None

    @property
    def promo_active(self) -> bool:
        """Окно акции открыто, если дата задана и сегодня <= promo_end_date."""
        if self.promo_end_date is None:
            return False
        return datetime.date.today() <= self.promo_end_date

    async def setup_router(self):
        if not self.init_done:
            setup_router(self.dp)
            self.dp.update.outer_middleware(self.middleware)
            # Глобальный перехватчик необработанных исключений в хэндлерах
            self.dp.errors.register(error_handler)
            self.init_done = True

    async def middleware(self, handler, event, data):
        data['bot_instance'] = self
        return await handler(event, data)

    async def run(self):
        logging.debug(f"run(): инициализация бота {mask_token(self.token)}")
        bot = Bot(self.token)
        try:
            botInfo = await bot.get_me()
            logging.debug(f"get_me() успешен: id={botInfo.id}, username=@{botInfo.username}")
        except TelegramUnauthorizedError:
            logging.error(f"Неверный токен {mask_token(self.token)} — бот не запущен")
            print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - '
                  f'Бот {mask_token(self.token)}: неверный токен, пропуск')
            await bot.session.close()
            return
        self.botname = botInfo.first_name
        logging.info(f"Инициализация бота \"{botInfo.first_name}\", ID: {botInfo.id}")
        print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - Бот {botInfo.first_name} запущен')

        await self.setup_router()

        await bot.delete_webhook(drop_pending_updates=True)
        try:
            logging.info(f"Бот \"{botInfo.first_name}\" запущен")
            await self.dp.start_polling(bot)
        finally:
            await bot.session.close()


async def error_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок aiogram 3.x (dp.errors).

    Логирует traceback и уведомляет пользователя, что его запрос не удалось
    обработать, вместо тихого падения обработки апдейта.
    """
    update = event.update
    exception = event.exception
    logging.exception(
        f"Необработанное исключение при обработке апдейта "
        f"{getattr(update, 'update_id', '?')}: {exception}"
    )
    message = getattr(update, 'message', None) or getattr(update, 'edited_message', None)
    if message is not None:
        try:
            await message.answer(
                "Произошла ошибка при обработке вашего запроса. "
                "Попробуйте ещё раз позже."
            )
        except Exception:
            logging.exception("Не удалось отправить пользователю сообщение об ошибке")
