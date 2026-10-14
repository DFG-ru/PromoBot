import asyncio
import logging
import sys
from datetime import datetime

from config_loader import load_bots_config, mask_token
from config_paths import LOG_DIR

logging.basicConfig(level=logging.INFO,
                    filename=str(LOG_DIR / "main_log.log"), filemode="a+",
                    format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
                    datefmt='%H:%M:%S',
                    )


def _log(msg: str):
    """Пишет сообщение и в консоль, и в лог."""
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {msg}')
    logging.info(msg)


async def main():
    # Понятная ошибка вместо трейсбека, если конфиг отсутствует/битый
    try:
        bots_config = load_bots_config()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        _log(f"Ошибка загрузки конфигурации: {exc}")
        logging.exception("Не удалось загрузить bots_config.json")
        sys.exit(1)

    from bot_instance import BotInstance  # импорт после настройки логов

    tasks = []
    for bot_config in bots_config:
        # Поле enabled (по умолчанию true) — позволяет выключить бота,
        # не удаляя его запись из конфига.
        if not bot_config["enabled"]:
            _log(f"Бот {mask_token(bot_config['token'])} отключён (enabled=false), пропуск запуска")
            continue
        bot_instance = BotInstance(
            token=bot_config["token"],
            template=bot_config["template"],
            coupon_mask=bot_config["coupon_mask"],
            social_media_url=bot_config["social_media_url"],
            website_url=bot_config["website_url"],
            promo_end_date=bot_config["promo_end_date"],
            font=bot_config["font"],
        )
        tasks.append(asyncio.create_task(bot_instance.run()))

    if not tasks:
        _log("В конфигурации нет ни одного включённого бота (все enabled=false или пустой список). Выход.")
        return

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    _log("Запуск бота(ов)...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _log("Exit")
