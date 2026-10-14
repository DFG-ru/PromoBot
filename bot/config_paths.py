"""Единые пути проекта, привязанные к файлу (не к текущей директории запуска)."""
from pathlib import Path

# Корень пакета бота (папка bot/)
BOT_ROOT = Path(__file__).resolve().parent
# Каталог данных (базы купонов, пользователей, история посещений)
DATA_DIR = BOT_ROOT / 'data'
# Каталог логов
LOG_DIR = BOT_ROOT / 'log'

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Файл конфигурации ботов (в gitignore, боевой) и его пример.
# Ищем рядом с bots_config.json.example (в bot/), затем в data/.
CONFIG_PATH = (BOT_ROOT / 'bots_config.json') if (BOT_ROOT / 'bots_config.json').is_file() \
    else (DATA_DIR / 'bots_config.json')
CONFIG_EXAMPLE_PATH = BOT_ROOT / 'bots_config.json.example'
