import asyncio
import os
import sys
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv, find_dotenv
from routers import setup_routers

load_dotenv(find_dotenv())
last_active = datetime.now().isoformat()

def getTokens():
    env = dict(os.environ)
    tokens = {}
    for k, v in env.items():
        if 'token' in k.lower():
            tokens[k] = v
    return tokens

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Получить купон"),
        # Добавьте другие команды здесь
    ]
    await bot.set_my_commands(commands)

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    return dp

async def main():
    tokens = getTokens()
    if not tokens:
        raise KeyError("No tokens in .env")
    
    bots = [Bot(token_value) for token_value in tokens.values()]
    dp = create_dispatcher()
    for token in tokens.keys():
        setup_routers(token, dp)
    
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=True)
        # await set_bot_commands(bot)
    
    try:
        await dp.start_polling(*bots)
    except KeyboardInterrupt:
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Exit')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        filename="log/main_log.log", filemode="a+",
                        format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
                        datefmt='%H:%M:%S',
                        )
    print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Запуск бота(ов)...')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Exit')
