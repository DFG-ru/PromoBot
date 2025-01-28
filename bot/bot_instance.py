import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Contact, FSInputFile, ReplyKeyboardRemove
from middlewares import couponGen
from middlewares import couponCodes_funcs as couponDB
from middlewares import userDatabase_funcs as userDB
from routers import setup_router
import logging

class BotInstance:
    def __init__(self, token: str, template: str, coupon_mask: str, social_media_url: str, website_url: str):
        self.token = token
        self.template = template
        self.coupon_mask = coupon_mask
        self.social_media_url = social_media_url
        self.website_url = website_url
        self.dp = Dispatcher()
        self.init_done = False

    async def setup_router(self):
        if not self.init_done:
            setup_router(self.dp)
            self.dp.update.outer_middleware(self.middleware)
            self.init_done = True

    async def middleware(self, handler, event, data):
        data['bot_instance'] = self
        return await handler(event, data)

    async def run(self):
        bot = Bot(self.token)
        botInfo = await bot.get_me()
        logging.info(f"Инициализация бота \"{botInfo.first_name}\", ID: {botInfo.id}")
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Бот {botInfo.first_name} запущен')

        await self.setup_router()

        await bot.delete_webhook(drop_pending_updates=True)
        try:
            logging.info(f"Бот \"{botInfo.first_name}\" запущен")
            await self.dp.start_polling(bot)
        finally:
            await bot.session.close()
