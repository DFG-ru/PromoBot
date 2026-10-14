"""Файловая база кодов купонов: свободные (CouponCodes.txt) и использованные."""
import asyncio
import logging
import random

from bot.paths import DATA_DIR

COUPON_DB_PATH = DATA_DIR / "CouponCodes.txt"
USED_COUPON_DB_PATH = DATA_DIR / "UsedCouponCodes.txt"

# Лок защищает операцию «выбрать свободный код -> пометить использованным»
# от гонок: без него два одновременных запроса могли получить один и тот же код.
_coupon_lock = asyncio.Lock()


def read(mask: str, db_path=None) -> list[str]:
    """Возвращает список всех кодов, содержащих указанный маскированный префикс."""
    target = db_path or COUPON_DB_PATH
    codes = []
    if target.is_file():
        with open(target, mode="r", encoding="utf-8") as file:
            for line in file:
                code = line.strip()
                if code and mask in code:
                    codes.append(code)
    else:
        logging.debug(f"Файл базы купонов не найден: {target}")
    logging.debug(f"read(mask={mask!r}): найдено кодов: {len(codes)}")
    return codes


def _read_used_codes(used_path=None) -> set[str]:
    """Читает множество уже использованных кодов (без учёта пробелов по краям)."""
    target = used_path or USED_COUPON_DB_PATH
    used = set()
    if target.is_file():
        with open(target, mode="r", encoding="utf-8") as file:
            for line in file:
                code = line.strip()
                if code:
                    used.add(code)
    else:
        logging.debug(f"Файл использованных кодов ещё не создан: {target}")
    logging.debug(f"Использованных кодов в базе: {len(used)}")
    return used


async def get_random_coupon_code(mask: str, db_path=None, used_path=None) -> str:
    """Выбирает случайный свободный код купона и помечает его использованным.

    Бросает FileNotFoundError, если база кодов отсутствует,
    ValueError — если свободные коды закончились.
    """
    target_db = db_path or COUPON_DB_PATH
    logging.debug(f"Запрос свободного купона по маске {mask!r}, ожидание лока...")
    async with _coupon_lock:
        logging.debug(f"Лок купонов захвачен, маска {mask!r}")
        if not target_db.is_file():
            logging.debug(f"База купонов отсутствует: {target_db}")
            raise FileNotFoundError("Файл CouponCodes.txt не найден.")

        all_codes = read(mask, db_path=target_db)
        used_codes = _read_used_codes(used_path)
        free_codes = [code for code in all_codes if code not in used_codes]
        logging.debug(f"По маске {mask!r}: всего кодов {len(all_codes)}, "
                      f"использовано {len(used_codes)}, свободно {len(free_codes)}")

        if not free_codes:
            logging.debug(f"Свободные коды по маске {mask!r} закончились")
            raise ValueError("Свободные купоны закончились.")

        selected_code = random.choice(free_codes)
        logging.debug(f"Выбран код {selected_code!r} из {len(free_codes)} свободных")

        # Помечаем код использованным (файл создаётся автоматически при необходимости)
        mark_code_as_used(selected_code, db_path=target_db, used_path=used_path)

        logging.info(f"Выдан купон {selected_code} (маска {mask}), "
                     f"свободно осталось: {len(free_codes) - 1}")
        return selected_code


def mark_code_as_used(code_to_find: str, db_path=None, used_path=None) -> None:
    """Добавляет указанный код в файл использованных кодов, если он есть в базе."""
    target_db = db_path or COUPON_DB_PATH
    target_used = used_path or USED_COUPON_DB_PATH
    logging.debug(f"Пометка кода {code_to_find!r} как использованного")
    all_codes = read("", db_path=target_db)
    if code_to_find in all_codes:
        with open(target_used, "a+", encoding="utf-8") as used_codes:
            used_codes.write(f"{code_to_find}\n")
        logging.debug(f"Код {code_to_find!r} записан в {target_used}")
        logging.info(f"Код '{code_to_find}' добавлен в файл использованных кодов.")
    else:
        logging.warning(f"Код '{code_to_find}' не найден в базе купонов.")
