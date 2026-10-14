import asyncio
import logging
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # Переходим из middlewares в корень bot
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)  # Гарантируем существование папки data

coupon_db_path = DATA_DIR / 'CouponCodes.txt'
used_coupon_db_path = DATA_DIR / 'UsedCouponCodes.txt'

# Лок защищает операцию «выбрать свободный код -> пометить использованным»
# от гонок: без него два одновременных запроса могли получить один и тот же код.
_coupon_lock = asyncio.Lock()


def read(mask: str) -> list[str]:
    """Возвращает список всех кодов с указанным маскированным префиксом."""
    codes = []
    if coupon_db_path.is_file():
        with open(coupon_db_path, mode='r', encoding='utf-8') as file:
            for line in file:
                code = line.strip()
                if code and mask in code:
                    codes.append(code)
    else:
        logging.debug(f"Файл базы купонов не найден: {coupon_db_path}")
    logging.debug(f"read(mask={mask!r}): найдено кодов: {len(codes)}")
    return codes


def _read_used_codes() -> set[str]:
    """Читает множество уже использованных кодов (без учёта регистра пробелов)."""
    used = set()
    if used_coupon_db_path.is_file():
        with open(used_coupon_db_path, mode='r', encoding='utf-8') as file:
            for line in file:
                code = line.strip()
                if code:
                    used.add(code)
    else:
        logging.debug(f"Файл использованных кодов ещё не создан: {used_coupon_db_path}")
    logging.debug(f"Использованных кодов в базе: {len(used)}")
    return used


async def get_random_coupon_code(mask: str) -> str:
    """Выбирает случайный свободный код купона и помечает его использованным.

    Бросает FileNotFoundError, если база кодов отсутствует,
    ValueError — если свободные коды закончились.
    """
    logging.debug(f"Запрос свободного купона по маске {mask!r}, ожидание лока...")
    async with _coupon_lock:
        logging.debug(f"Лок купонов захвачен, маска {mask!r}")
        if not coupon_db_path.is_file():
            logging.debug(f"База купонов отсутствует: {coupon_db_path}")
            raise FileNotFoundError("Файл CouponCodes.txt не найден.")

        all_codes = read(mask)
        used_codes = _read_used_codes()
        free_codes = [code for code in all_codes if code not in used_codes]
        logging.debug(f"По маске {mask!r}: всего кодов {len(all_codes)}, "
                      f"использовано {len(used_codes)}, свободно {len(free_codes)}")

        if not free_codes:
            logging.debug(f"Свободные коды по маске {mask!r} закончились")
            raise ValueError("Свободные купоны закончились.")

        selected_code = random.choice(free_codes)
        logging.debug(f"Выбран код {selected_code!r} из {len(free_codes)} свободных")

        # Помечаем код использованным (файл создаётся автоматически при необходимости)
        mark_code_as_used(selected_code)

        logging.info(f"Выдан купон {selected_code} (маска {mask}), "
                     f"свободно осталось: {len(free_codes) - 1}")
        return selected_code


def mark_code_as_used(code_to_find: str):
    """Добавляет указанный код в файл использованных кодов, если он есть в базе."""
    logging.debug(f"Пометка кода {code_to_find!r} как использованного")
    all_codes = read('')
    if code_to_find in all_codes:
        with open(used_coupon_db_path, 'a+', encoding='utf-8') as used_codes:
            used_codes.write(f"{code_to_find}\n")
        logging.debug(f"Код {code_to_find!r} записан в {used_coupon_db_path}")
        logging.info(f"Код '{code_to_find}' добавлен в файл использованных кодов.")
    else:
        logging.warning(f"Код '{code_to_find}' не найден в базе купонов.")
