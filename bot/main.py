import asyncio
import os
import sys
import logging
from datetime import datetime
import json
from bot_instance import BotInstance

logging.basicConfig(level=logging.INFO,
                    filename="log/main_log.log", filemode="a+",
                    format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
                    datefmt='%H:%M:%S',
                    )

def load_config(config_path: str):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config

async def main():
    config_path = os.path.join(os.getcwd(), 'bots_config.json')
    config = load_config(config_path)
    tasks = []

    if 'bots' in config:
        for bot_config in config['bots']:
            bot_instance = BotInstance(
                token=bot_config.get('token'),
                template=bot_config.get('template'),
                coupon_mask=bot_config.get('coupon_mask'),
                social_media_url=bot_config.get('social_media_url'),
                website_url=bot_config.get('website_url')
            )
            task = asyncio.create_task(bot_instance.run())
            tasks.append(task)

        await asyncio.gather(*tasks)
    else:
        raise KeyError("No bots configuration in JSON file")

if __name__ == "__main__":
    print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Запуск бота(ов)...')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f'{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} - Exit')
