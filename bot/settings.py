"""Загрузка и валидация конфигурации ботов (bots_config.json).

Поддерживает запуск нескольких ботов из одного конфига: секция "bots" —
список словарей с параметрами каждого экземпляра бота.
"""
import json
import logging
from pathlib import Path

from bot.paths import CONFIG_PATH, CONFIG_EXAMPLE_PATH

# Поле «дата окончания акции» по умолчанию, если не задано в конфиге.
DEFAULT_PROMO_END_DATE = "2026-12-31"


def parse_bool(value, default: bool = True) -> bool:
    """Толерантный парсинг булева значения из JSON/строки (true/"yes"/1...)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def mask_token(token: str) -> str:
    """Маскирует токен для логов/консоли: видны только края."""
    token = str(token or "")
    if len(token) <= 8:
        return "*" * len(token) if token else "<пустой>"
    return f"{token[:4]}…{token[-6:]}"


def load_bots_config(path: Path | None = None) -> list[dict]:
    """Читает bots_config.json и возвращает нормализованный список конфигов ботов.

    Каждому элементу гарантированно проставлены значения по умолчанию для
    необязательных полей, чтобы код дальше мог безопасно обращаться по ключам.
    Бросает FileNotFoundError/ValueError/KeyError при проблемах с конфигом.
    """
    path = path or CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"Файл конфигурации {path} не найден.\n"
            f"Скопируйте {CONFIG_EXAMPLE_PATH.name} в {path.name} и заполните значения."
        )
    try:
        with open(path, mode="r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ошибка чтения конфига {path}: {exc}") from exc

    # Ожидаемая структура: {"bots": [ {...}, {...}, ... ]}.
    if not isinstance(config, dict) or "bots" not in config:
        raise KeyError("В bots_config.json отсутствует секция \"bots\" (ожижается список ботов)")
    raw_bots = config["bots"]
    if not isinstance(raw_bots, list):
        raise KeyError("Секция \"bots\" должна быть списком объектов-ботов")

    bots = []
    for idx, entry in enumerate(raw_bots, start=1):
        if not isinstance(entry, dict):
            raise KeyError(f"Элемент №{idx} в секции \"bots\" не является объектом")
        token = str(entry.get("token", "")).strip()
        if not token:
            raise ValueError(f"У бота №{idx} в bots_config.json пустой или отсутствует обязательный \"token\"")
        bots.append({
            "token": token,
            "template": str(entry.get("template", "")),
            "coupon_mask": str(entry.get("coupon_mask", "")),
            "social_media_url": str(entry.get("social_media_url", "")),
            "website_url": str(entry.get("website_url", "")),
            "font": str(entry.get("font", "")),
            "promo_end_date": str(entry.get("promo_end_date") or DEFAULT_PROMO_END_DATE),
            "enabled": parse_bool(entry.get("enabled"), default=True),
        })

    logging.debug(f"Загружена конфигурация {path}: включённых ботов "
                  f"{sum(b['enabled'] for b in bots)} из {len(bots)}")
    return bots
