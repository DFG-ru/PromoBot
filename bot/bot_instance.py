import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Contact, FSInputFile, ReplyKeyboardRemove
from middlewares import couponGen
from middlewares import couponCodes_funcs as couponDB
from middlewares import userDatabase_funcs as userDB
from routers import router
import logging

class BotInstance:
    def __init__(self, token: str, template: str, coupon_mask: str, social_media_url: str, website_url: str):
        self.token = token
        self.template = template
        self.coupon_mask = coupon_mask
        self.social_media_url = social_media_url
        self.website_url = website_url
        self.dp = Dispatcher()
        self.setup_routers()

    async def setup_routers(self):
        self.dp.include_router(router)

    async def run(self):
        bot = Bot(self.token)
        botInfo = await bot.get_me()
        logging.info(f"Инициализация бота \"{botInfo.first_name}\", ID: {botInfo.id}")
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Бот {botInfo.first_name} запущен')

        self.dp.update.outer_middleware(self.middleware)

        await bot.delete_webhook(drop_pending_updates=True)
        try:
            logging.info(f"Бот \"{botInfo.first_name}\" запущен")
            await self.dp.start_polling(bot)
        finally:
            await bot.session.close()

    async def middleware(self, handler, event, data):
        data['bot_instance'] = self
        return await handler(event, data)