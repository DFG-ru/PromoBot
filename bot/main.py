import asyncio
import os
import sys
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
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


def create_dispatcher(bot, token) -> Dispatcher:
    dp = Dispatcher(bot=bot)
    setup_routers(token, dp)
    return dp


async def run_bot(token, token_value):
    bot = Bot(token_value)
    botInfo = await bot.get_me()
    logging.info(f"Инициализация бота \"{botInfo.first_name}\", ID: {botInfo.id}")
    print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Бот {botInfo.first_name} запущен')
    dp = create_dispatcher(bot, token)
    await bot.delete_webhook(drop_pending_updates=True)
    # await set_bot_commands(bot)
    try:
        logging.info(f"Бот \"{botInfo.first_name}\" запущен")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
    
    
async def main():
    tasks = []
    tokens = getTokens()
    if tokens:
        for token_key, token_value in tokens.items():
            task = asyncio.create_task(run_bot(token_key, token_value))
            tasks.append(task)
        await asyncio.gather(*tasks)
    raise KeyError("No tokens in .env")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        filename="log/main_log.log",filemode="a+", 
                        format = "%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s", 
                        datefmt='%H:%M:%S',
                        )
    print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Запуск бота(ов)...')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Exit')