from pathlib import Path
import csv
import io

import aiofiles


BASE_DIR = Path(__file__).resolve().parent.parent  # Переходим из middlewares в корень bot
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

user_db_path = DATA_DIR / 'UserDatabase.csv'

# 🔑 Константы для индексов столбцов (явное управление структурой)
COLUMNS = {
    'user_id': 0,
    'first_name': 1,
    'last_name': 2,
    'username': 3,
    'phone_number': 4,      # Номер телефона для поиска
    'coupon_code': 5
}
MIN_COLUMNS = max(COLUMNS.values()) + 1  # Минимальное кол-во столбцов = 6


async def _read_rows():
    """Читает весь CSV и возвращает список строк (парсинг — в памяти)."""
    async with aiofiles.open(user_db_path, mode='r', encoding='utf-8', newline='') as file:
        content = await file.read()
    return list(csv.reader(io.StringIO(content)))


async def _write_rows(rows):
    """Сериализует строки через csv.writer в памяти и асинхронно записывает файл."""
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerows(rows)
    async with aiofiles.open(user_db_path, mode='w', encoding='utf-8', newline='') as file:
        await file.write(buffer.getvalue())


async def write(user_id, first_name, last_name, username, phone_number=None, coupon_code=None):
    # csv.writer не работает с асинхронными файловыми объектами,
    # поэтому сериализуем строку в памяти и пишем через aiofiles.
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        user_id,
        first_name or None,
        last_name or None,
        username or None,
        phone_number or None,
        coupon_code or None
    ])
    async with aiofiles.open(user_db_path, mode='a+', newline='', encoding='utf-8') as file:
        await file.write(buffer.getvalue())


async def update(phone_number, new_data):
    if not user_db_path.is_file():
        return False

    updated = False

    # 1️⃣ Читаем все данные
    rows = await _read_rows()

    # 2️⃣ Ищем запись по номеру телефона
    for i, row in enumerate(rows):
        # Защита от коротких строк (меньше 5 столбцов)
        if len(row) <= COLUMNS['phone_number']:
            continue

        if row[COLUMNS['phone_number']] == phone_number:
            # 3️⃣ Дополняем строку до минимальной длины, если нужно
            if len(row) < MIN_COLUMNS:
                row.extend([''] * (MIN_COLUMNS - len(row)))

            # 4️⃣ ТОЧЕЧНОЕ ОБНОВЛЕНИЕ: меняем ТОЛЬКО указанные поля
            for field, value in new_data.items():
                if field in COLUMNS:  # Проверяем, что поле существует в структуре
                    col_idx = COLUMNS[field]
                    # Автоматически расширяем строку, если не хватает столбцов
                    if col_idx >= len(row):
                        row.extend([''] * (col_idx - len(row) + 1))
                    row[col_idx] = value

            updated = True
            break  # Обновляем только первую найденную запись

    # 5️⃣ Сохраняем изменения
    if updated:
        await _write_rows(rows)

    return updated


async def update_coupon(phone_number, new_data):
    if not user_db_path.is_file():
        return False

    updated = False

    # 1️⃣ Читаем все данные
    rows = await _read_rows()

    # 2️⃣ Ищем запись по номеру телефона с пустым купоном
    for i, row in enumerate(rows):
        # Защита от коротких строк (меньше 5 столбцов)
        if len(row) <= COLUMNS['phone_number']:
            continue

        # Убедимся, что в строке есть хотя бы столбец coupon_code
        coupon_value = row[COLUMNS['coupon_code']] if len(row) > COLUMNS['coupon_code'] else ''

        if row[COLUMNS['phone_number']] == phone_number and coupon_value == '':
            # 3️⃣ Дополняем строку до минимальной длины, если нужно
            if len(row) < MIN_COLUMNS:
                row.extend([''] * (MIN_COLUMNS - len(row)))

            # 4️⃣ ТОЧЕЧНОЕ ОБНОВЛЕНИЕ: меняем ТОЛЬКО указанные поля
            for field, value in new_data.items():
                if field in COLUMNS:  # Проверяем, что поле существует в структуре
                    col_idx = COLUMNS[field]
                    # Автоматически расширяем строку, если не хватает столбцов
                    if col_idx >= len(row):
                        row.extend([''] * (col_idx - len(row) + 1))
                    row[col_idx] = value

            updated = True
            break  # Обновляем только первую найденную запись

    # 5️⃣ Сохраняем изменения
    if updated:
        await _write_rows(rows)

    return updated


async def phone_exist(phone_number):
    if not user_db_path.is_file():
        return False
    rows = await _read_rows()

    # Проходим по всем строкам
    for row in rows:
        if len(row) > COLUMNS['phone_number'] and row[4] == phone_number:
            return True

    # Номер не найден
    return False


async def coupon_exist(user_id, coupon_mask):
    user_id = str(user_id)
    if not user_db_path.is_file():
        return False
    rows = await _read_rows()

    # Проходим по всем строкам
    for row in rows:
        if len(row) > COLUMNS['coupon_code'] and row[0] == user_id:
            if row[5][:7] == coupon_mask:
                return True

    # Купон не найден
    return False


async def get_user_coupon(phone_number, coupon_mask):
    if not user_db_path.is_file():
        return None
    rows = await _read_rows()
    for row in rows:
        if len(row) > COLUMNS['coupon_code'] and row[4] == phone_number:
            if row[5] == "":
                return None
            if row[5][:7] == coupon_mask:
                return row[5]
    return None
