"""Файловая база пользователей (CSV): профиль, телефон, выданный купон."""
import csv
import io
import logging

import aiofiles

from bot.paths import DATA_DIR

USER_DB_PATH = DATA_DIR / "UserDatabase.csv"

# Константы для индексов столбцов (явное управление структурой)
COLUMNS = {
    "user_id": 0,
    "first_name": 1,
    "last_name": 2,
    "username": 3,
    "phone_number": 4,   # Номер телефона — ключ поиска
    "coupon_code": 5,
}
MIN_COLUMNS = max(COLUMNS.values()) + 1  # Минимальное кол-во столбцов = 6


def _db_path() -> "object":
    """Актуальный путь к базе (через модуль — удобно для подмены в тестах)."""
    return USER_DB_PATH


async def _read_rows(path=None) -> list[list[str]]:
    """Читает весь CSV и возвращает список строк (парсинг — в памяти)."""
    async with aiofiles.open(path or USER_DB_PATH, mode="r", encoding="utf-8", newline="") as file:
        content = await file.read()
    return list(csv.reader(io.StringIO(content)))


async def _write_rows(rows, path=None) -> None:
    """Сериализует строки через csv.writer в памяти и асинхронно записывает файл."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerows(rows)
    async with aiofiles.open(path or USER_DB_PATH, mode="w", encoding="utf-8", newline="") as file:
        await file.write(buffer.getvalue())


async def write(user_id, first_name, last_name, username, phone_number=None,
                coupon_code=None, path=None) -> None:
    """Добавляет новую запись пользователя в конец базы.

    csv.writer не работает с асинхронными файловыми объектами,
    поэтому сериализуем строку в памяти и пишем через aiofiles.
    """
    target = path or USER_DB_PATH
    logging.debug(f"DB write: user_id={user_id}, phone={phone_number} -> {target}")
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        user_id,
        first_name or None,
        last_name or None,
        username or None,
        phone_number or None,
        coupon_code or None,
    ])
    async with aiofiles.open(target, mode="a+", newline="", encoding="utf-8") as file:
        await file.write(buffer.getvalue())


async def update(phone_number, new_data, path=None) -> bool:
    """Точечно обновляет поля первой записи с указанным телефоном."""
    target = path or USER_DB_PATH
    logging.debug(f"DB update: phone={phone_number}, fields={list(new_data)}")
    if not target.is_file():
        logging.debug(f"DB update: файл базы не найден ({target}), пропуск")
        return False

    rows = await _read_rows(target)
    updated = _apply_update(rows, phone_number, new_data, require_empty_coupon=False)
    if updated:
        await _write_rows(rows, target)
    logging.debug(f"DB update: phone={phone_number} -> "
                  f"{'запись обновлена' if updated else 'запись не найдена'}")
    return updated


async def update_coupon(phone_number, new_data, path=None) -> bool:
    """Привязывает купон к первой записи с телефоном и пустым полем купона."""
    target = path or USER_DB_PATH
    logging.debug(f"DB update_coupon: phone={phone_number}, fields={list(new_data)}")
    if not target.is_file():
        logging.debug(f"DB update_coupon: файл базы не найден ({target}), пропуск")
        return False

    rows = await _read_rows(target)
    updated = _apply_update(rows, phone_number, new_data, require_empty_coupon=True)
    if updated:
        await _write_rows(rows, target)
    logging.debug(f"DB update_coupon: phone={phone_number} -> "
                  f"{'купон записан' if updated else 'запись с пустым купоном не найдена'}")
    return updated


def _apply_update(rows, phone_number, new_data, require_empty_coupon: bool) -> bool:
    """Меняет ТОЛЬКО указанные поля первой подходящей записи (в памяти)."""
    for row in rows:
        # Защита от коротких строк (меньше 5 столбцов)
        if len(row) <= COLUMNS["phone_number"]:
            continue
        if row[COLUMNS["phone_number"]] != phone_number:
            continue
        if require_empty_coupon:
            coupon_value = row[COLUMNS["coupon_code"]] if len(row) > COLUMNS["coupon_code"] else ""
            if coupon_value != "":
                continue

        # Дополняем строку до минимальной длины, если нужно
        if len(row) < MIN_COLUMNS:
            row.extend([""] * (MIN_COLUMNS - len(row)))

        for field, value in new_data.items():
            if field in COLUMNS:  # Проверяем, что поле существует в структуре
                col_idx = COLUMNS[field]
                # Автоматически расширяем строку, если не хватает столбцов
                if col_idx >= len(row):
                    row.extend([""] * (col_idx - len(row) + 1))
                row[col_idx] = value
        return True  # Обновляем только первую найденную запись
    return False


async def phone_exist(phone_number, path=None) -> bool:
    """Есть ли в базе запись с таким номером телефона."""
    target = path or USER_DB_PATH
    if not target.is_file():
        logging.debug(f"DB phone_exist: файл базы не найден ({target}) -> False")
        return False
    rows = await _read_rows(target)
    found = any(len(row) > COLUMNS["phone_number"] and row[COLUMNS["phone_number"]] == phone_number
                for row in rows)
    logging.debug(f"DB phone_exist: phone={phone_number} -> {found} (строк в базе: {len(rows)})")
    return found


async def coupon_exist(user_id, coupon_mask, path=None) -> bool:
    """Выдан ли пользователю купон с указанным маскированным префиксом."""
    target = path or USER_DB_PATH
    user_id = str(user_id)
    if not target.is_file():
        logging.debug(f"DB coupon_exist: файл базы не найден ({target}) -> False")
        return False
    rows = await _read_rows(target)
    found = any(
        len(row) > COLUMNS["coupon_code"]
        and row[COLUMNS["user_id"]] == user_id
        and row[COLUMNS["coupon_code"]][:len(coupon_mask)] == coupon_mask
        for row in rows
    )
    logging.debug(f"DB coupon_exist: user_id={user_id}, mask={coupon_mask!r} -> {found}")
    return found


async def get_user_coupon(phone_number, coupon_mask, path=None) -> str | None:
    """Возвращает купон пользователя по телефону (если он принадлежит маске)."""
    target = path or USER_DB_PATH
    if not target.is_file():
        logging.debug(f"DB get_user_coupon: файл базы не найден ({target}) -> None")
        return None
    rows = await _read_rows(target)
    for row in rows:
        if len(row) > COLUMNS["coupon_code"] and row[COLUMNS["phone_number"]] == phone_number:
            coupon = row[COLUMNS["coupon_code"]]
            if coupon == "":
                logging.debug(f"DB get_user_coupon: phone={phone_number} -> None (купон пуст)")
                return None
            if coupon[:len(coupon_mask)] == coupon_mask:
                logging.debug(f"DB get_user_coupon: phone={phone_number} -> {coupon!r}")
                return coupon
    logging.debug(f"DB get_user_coupon: phone={phone_number}, mask={coupon_mask!r} -> None (не найдено)")
    return None
