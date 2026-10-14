"""Точка входа PromoBot: запуск одного и более ботов из bots_config.json.

Запуск из корня репозитория:
    python -m bot.main
или (для совместимости со старыми скриптами и NSSM):
    python bot/main.py
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Позволяет запускать файл напрямую (python bot/main.py): добавляем корень
# репозитория в sys.path, чтобы пакет `bot` был импортируем.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.paths import LOG_DIR
from bot.settings import load_bots_config, mask_token

# Уровень логирования можно задать переменной окружения LOG_LEVEL
# (например, LOG_LEVEL=DEBUG для подробного отладочного лога).
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging() -> None:
    """Настраивает корневой логгер: файл + консоль."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(str(LOG_DIR / "main_log.log"), mode="a+", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _log(msg: str) -> None:
    """Пишет сообщение и в консоль, и в лог."""
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")
    logging.info(msg)


async def main() -> None:
    logging.debug(f"Старт main, уровень логирования: {LOG_LEVEL}")
    # Понятная ошибка вместо трейсбека, если конфиг отсутствует/битый
    try:
        bots_config = load_bots_config()
        logging.debug(f"Конфигурация загружена, ботов в конфиге: {len(bots_config)}")
    except (FileNotFoundError, ValueError, KeyError) as exc:
        _log(f"Ошибка загрузки конфигурации: {exc}")
        logging.exception("Не удалось загрузить bots_config.json")
        sys.exit(1)

    from bot.bot_runner import BotRunner  # импорт после настройки логов

    tasks = []
    for idx, bot_config in enumerate(bots_config, start=1):
        # Поле enabled (по умолчанию true) — позволяет выключить бота,
        # не удаляя его запись из конфига.
        if not bot_config["enabled"]:
            _log(f"Бот {mask_token(bot_config['token'])} отключён (enabled=false), пропуск запуска")
            continue
        logging.debug(f"Создание BotRunner #{idx}: token={mask_token(bot_config['token'])}, "
                      f"template={bot_config['template']!r}, coupon_mask={bot_config['coupon_mask']!r}, "
                      f"promo_end_date={bot_config['promo_end_date']!r}, font={bot_config['font']!r}")
        runner = BotRunner(
            token=bot_config["token"],
            template=bot_config["template"],
            coupon_mask=bot_config["coupon_mask"],
            social_media_url=bot_config["social_media_url"],
            website_url=bot_config["website_url"],
            promo_end_date=bot_config["promo_end_date"],
            font=bot_config["font"],
        )
        tasks.append(asyncio.create_task(runner.run()))
        logging.debug(f"Задача запуска бота #{idx} создана (всего задач: {len(tasks)})")

    if not tasks:
        _log("В конфигурации нет ни одного включённого бота (все enabled=false или пустой список). Выход.")
        return

    logging.debug(f"Старт polling для {len(tasks)} бот(ов)")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    setup_logging()
    _log("Запуск бота(ов)...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _log("Exit")
