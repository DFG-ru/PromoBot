"""Загрузка и валидация конфигурации ботов (bots_config.json)."""
import json
import logging
from pathlib import Path

from config_paths import CONFIG_PATH, CONFIG_EXAMPLE_PATH

# Поле «дата окончания акции» по умолчанию, если не задано в конфиге.
DEFAULT_PROMO_END_DATE = "2026-12-31"


def parse_bool(value, default: bool = True) -> bool:
    """Гибко разбирает булево значение из конфига.

    Поддерживает bool, а также строковые/числовые варианты вида
    "true", "1", "yes", "on" / "false", "0", "no", "off" (без учёта регистра).
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("true", "1", "yes", "y", "on"):
            return True
        if s in ("false", "0", "no", "n", "off", ""):
            return False
    logging.warning(f"Не удалось распознать логическое значение {value!r}, используем {default}")
    return default


def mask_token(token: str) -> str:
    """Маскирует токен для безопасного вывода в лог/консоль."""
    if not token:
        return "<пустой>"
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}…{token[-4:]}"


def load_bots_config(config_path: Path | str = CONFIG_PATH) -> list[dict]:
    """Читает bots_config.json и возвращает нормализованный список конфигов ботов.

    Понятные ошибки вместо падений с непонятным трейсбеком:
    - FileNotFoundError — файл не найден (подсказка про .example);
    - json.JSONDecodeError — битый JSON;
    - KeyError/ValueError — отсутствует секция \"bots\" или у бота нет токена.
    """
    config_path = Path(config_path)
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Файл конфигурации {config_path} не найден. "
            f"Скопируйте {CONFIG_EXAMPLE_PATH.name} рядом с ним и заполните значения."
        )
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Файл конфигурации {config_path} содержит некорректный JSON: {exc}") from exc

    if "bots" not in config:
        raise KeyError("В файле конфигурации отсутствует секция \"bots\"")

    bots = []
    for idx, bot_config in enumerate(config["bots"], start=1):
        token = (bot_config.get("token") or "").strip()
        if not token:
            raise ValueError(f"В записи №{idx} списка \"bots\" отсутствует поле \"token\"")
        bots.append({
            "enabled": parse_bool(bot_config.get("enabled"), default=True),
            "token": token,
            "template": bot_config.get("template"),
            "coupon_mask": bot_config.get("coupon_mask"),
            "social_media_url": bot_config.get("social_media_url"),
            "website_url": bot_config.get("website_url"),
            "promo_end_date": bot_config.get("promo_end_date", DEFAULT_PROMO_END_DATE),
            "font": bot_config.get("font"),
        })
    return bots
