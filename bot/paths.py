"""Единые пути проекта, привязанные к файлу (не к текущей директории запуска)."""
from pathlib import Path

# Корень пакета бота (папка bot/)
BOT_ROOT = Path(__file__).resolve().parent
# Каталог данных (базы купонов, пользователей, история посещений, конфиг)
DATA_DIR = BOT_ROOT / "data"
# Каталог логов
LOG_DIR = BOT_ROOT / "log"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Файл конфигурации ботов (в gitignore, боевой) и его пример.
# Ищем bot/bots_config.json, затем bot/data/bots_config.json.
if (BOT_ROOT / "bots_config.json").is_file():
    CONFIG_PATH = BOT_ROOT / "bots_config.json"
elif (DATA_DIR / "bots_config.json").is_file():
    CONFIG_PATH = DATA_DIR / "bots_config.json"
else:
    CONFIG_PATH = BOT_ROOT / "bots_config.json"
CONFIG_EXAMPLE_PATH = DATA_DIR / "bots_config.json.example"

# История посещений (пишется в хэндлере /start)
VISIT_HISTORY_PATH = DATA_DIR / "VisitHistory.txt"
