"""MTProto-клиент PromoBot (Telethon): обмен данными через MTProto-прокси.

Подключение идёт к локальному MTProto-прокси (ip:port + секрет), который
формирует TLS-туннель к серверам Telegram. Конфигурация хранится в
bot/data/mtproto_config.json — порт, ip и ключ можно менять без правки кода.

Запуск проверки из корня репозитория:
    python -m bot.mtproto            # connection_test с конфигом
    python -m bot.mtproto 127.0.0.1 1443 <ключ>   # разовая проверка параметрами
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import (
    AuthKeyDuplicatedError,
    AuthKeyUnregisteredError,
    SessionPasswordNeededError,
)
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.sessions import StringSession

from bot.paths import DATA_DIR

# Файл конфигурации MTProto-подключения (в gitignore, боевой) и его пример.
MTPROTO_CONFIG_PATH = DATA_DIR / "mtproto_config.json"
MTPROTO_CONFIG_EXAMPLE_PATH = DATA_DIR / "mtproto_config.json.example"

# Значения по умолчанию, если поля отсутствуют в конфиге.
DEFAULT_API_ID = 2040
DEFAULT_API_HASH = "b18441a4ff7d1494126a7e9b0c7f5a3c"
DEFAULT_DEVICE_MODEL = "PromoBot"
DEFAULT_SYSTEM_VERSION = "1.0"
DEFAULT_APP_VERSION = "1.0"
DEFAULT_LANG_CODE = "ru"
DEFAULT_SESSION_PREFIX = "mtproto_session"


def mask_secret(value: str) -> str:
    """Маскирует секрет прокси для логов: видны только края."""
    value = str(value or "")
    if len(value) <= 8:
        return "*" * len(value) if value else "<пустой>"
    return f"{value[:4]}…{value[-4:]}"


def load_mtproto_config(path: Path | None = None) -> dict:
    """Читает mtproto_config.json и возвращает словарь настроек подключения.

    Ожидаемая структура: {"ip": "...", "port": 1443, "secret": "hex", ...}.
    Необязательные поля (api_id/api_hash/session_name/device_model и т.д.)
    получают значения по умолчанию. Бросает FileNotFoundError/ValueError/KeyError.
    """
    path = path or MTPROTO_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"Файл конфигурации MTProto {path} не найден.\n"
            f"Скопируйте {MTPROTO_CONFIG_EXAMPLE_PATH.name} в {path.name} "
            f"и заполните ip/port/secret."
        )
    try:
        with open(path, mode="r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ошибка чтения конфига {path}: {exc}") from exc

    if not isinstance(config, dict):
        raise KeyError("mtproto_config.json должен содержать объект с ip/port/secret")

    ip = str(config.get("ip", "")).strip()
    if not ip:
        raise ValueError('В mtproto_config.json пустое или отсутствует обязательное поле "ip"')

    try:
        port = int(config.get("port"))
    except (TypeError, ValueError):
        raise ValueError(
            f'В mtproto_config.json некорректное "port" ({config.get("port")!r}): '
            f"ожидается целое число"
        ) from None
    if not 1 <= port <= 65535:
        raise ValueError(f'В mtproto_config.json port вне диапазона 1..65535: {port}')

    secret = str(config.get("secret", "")).strip().lower()
    if not secret:
        raise ValueError('В mtproto_config.json пустое или отсутствует обязательное поле "secret"')
    try:
        bytes.fromhex(secret)
    except ValueError:
        raise ValueError(
            f'В mtproto_config.json secret содержит недопустимые символы '
            f"(ожидается hex-строка, например e983be...)"
        ) from None

    return {
        "ip": ip,
        "port": port,
        "secret": secret,
        "api_id": int(config.get("api_id", DEFAULT_API_ID)),
        "api_hash": str(config.get("api_hash", DEFAULT_API_HASH)),
        "session_name": str(config.get("session_name", DEFAULT_SESSION_PREFIX)),
        "device_model": str(config.get("device_model", DEFAULT_DEVICE_MODEL)),
        "system_version": str(config.get("system_version", DEFAULT_SYSTEM_VERSION)),
        "app_version": str(config.get("app_version", DEFAULT_APP_VERSION)),
        "lang_code": str(config.get("lang_code", DEFAULT_LANG_CODE)),
    }


def build_client(config: dict) -> TelegramClient:
    """Собирает Telethon-клиент с MTProto-прокси из конфига.

    Сессия хранится в файле bot/data/<session_name>.session (перезапись
    конфига не влияет на авторизацию — сессию можно удалить для сброса).
    Для MTProto-прокси Telethon использует ConnectionTcpMTProxyRandomizedIntermediate.
    """
    session_path = DATA_DIR / f"{config['session_name']}.session"
    client = TelegramClient(
        str(session_path),
        api_id=config["api_id"],
        api_hash=config["api_hash"],
        connection=ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=(
            config["ip"],       # адрес MTProto-прокси
            config["port"],     # порт MTProto-прокси
            config["secret"],   # секрет MTProto (hex)
        ),
        device_model=config["device_model"],
        system_version=config["system_version"],
        app_version=config["app_version"],
        lang_code=config["lang_code"],
    )
    logging.debug(
        f"MTProto-клиент создан: {config['ip']}:{config['port']} "
        f"secret={mask_secret(config['secret'])}, session={session_path.name}"
    )
    return client


async def connect(config: dict) -> TelegramClient:
    """Подключает клиент; при необходимости запускает интерактивную авторизацию.

    Возвращает уже подключённый (и, для user-аккаунта, авторизованный) клиент.
    При неверном аккаунте/секрете бросает исключение Telethon с понятным логом.
    """
    client = build_client(config)
    await client.connect()
    logging.info(
        f"TCP-соединение через MTProto-прокси {config['ip']}:{config['port']} установлено"
    )
    if not await client.is_user_authorized():
        phone = input("Номер телефона аккаунта Telegram (+7...): ").strip()
        await client.send_code_request(phone)
        code = input("Код из Telegram: ").strip()
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = input("Облачный пароль аккаунта: ")
            await client.sign_in(password=password)
        logging.info(f"Аккаунт авторизован: {(await client.get_me()).username}")
    else:
        me = await client.get_me()
        logging.info(f"Сессия активна, аккаунт: @{me.username} (id={me.id})")
    return client


async def connection_test(config: dict) -> bool:
    """Проверка связности: коннект, get_me(), исходящее сообщение себе (если задан target_chat).

    Возвращает True, если MTProto-канал работает и API отвечает.
    """
    ok = False
    try:
        client = await connect(config)
    except (AuthKeyUnregisteredError, AuthKeyDuplicatedError) as exc:
        logging.error(
            f"Сессия недействительна ({type(exc).__name__}) — удалите файл "
            f"{DATA_DIR / (config['session_name'] + '.session')} и повторите"
        )
        return False
    except OSError as exc:
        logging.error(
            f"Не удалось подключиться к прокси {config['ip']}:{config['port']}: {exc}"
        )
        return False
    try:
        me = await client.get_me()
        logging.info(f"MTProto OK: аккаунт @{me.username} (id={me.id})")
        target = config.get("target_chat")
        if target:
            await client.send_message(target, "PromoBot: проверка MTProto-канала")
            logging.info(f"Тестовое сообщение отправлено в {target!r}")
        ok = True
    except Exception:
        logging.exception("Ошибка при проверке MTProto-связности")
    finally:
        await client.disconnect()
    return ok


def main(argv: list[str]) -> int:
    """CLI-точка: python -m bot.mtproto [ip port secret]."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(module)s - %(levelname)s: %(message)s",
    )
    if len(argv) >= 4:
        # Разовая проверка параметрами из командной строки.
        config = {
            "ip": argv[1],
            "port": int(argv[2]),
            "secret": argv[3].lower(),
            "api_id": DEFAULT_API_ID,
            "api_hash": DEFAULT_API_HASH,
            "session_name": DEFAULT_SESSION_PREFIX,
            "device_model": DEFAULT_DEVICE_MODEL,
            "system_version": DEFAULT_SYSTEM_VERSION,
            "app_version": DEFAULT_APP_VERSION,
            "lang_code": DEFAULT_LANG_CODE,
        }
    else:
        try:
            config = load_mtproto_config()
        except (FileNotFoundError, ValueError, KeyError) as exc:
            print(f"Ошибка конфигурации MTProto: {exc}")
            return 1
    print(
        f"MTProto-прокси: {config['ip']}:{config['port']} "
        f"secret={mask_secret(config['secret'])}"
    )
    return 0 if asyncio.run(connection_test(config)) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
