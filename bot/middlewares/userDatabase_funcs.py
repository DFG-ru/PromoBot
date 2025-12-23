from path import Path
import csv
import os

user_db_path = Path().joinpath('data', 'UserDatabase.csv')

def write(user_id, first_name, last_name, username, phone_number=None, coupon_code=None):
    file_exists = os.path.isfile(user_db_path)
    with open(user_db_path, mode='a+', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow([
            user_id,
            first_name or None,
            last_name or None,
            username or None,
            phone_number or None,
            coupon_code or None
        ])


def update(phone_number, new_data):
    if not os.path.isfile(user_db_path):
            return False

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

    updated = False
    rows = []

    # 1️⃣ Читаем все данные
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)

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
        with open(user_db_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    
    return updated
    
    
def update_coupon(phone_number, new_data):
    if not os.path.isfile(user_db_path):
            return False

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

    updated = False
    rows = []

    # 1️⃣ Читаем все данные
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)

    # 2️⃣ Ищем запись по номеру телефона
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
        with open(user_db_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    
    return updated


def phone_exist(phone_number):
    if not os.path.isfile(user_db_path):
        return False
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)

        # Читаем строки по одной
        for row in reader:
            if row[4] == phone_number:
                return True

        # Номер не найден
        return False


def coupon_exist(user_id, coupon_mask):
    user_id = str(user_id)
    if not os.path.isfile(user_db_path):
        return False
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)

        # Читаем строки по одной
        for row in reader:
            if row[0] == user_id:
                if row[5][:7] == coupon_mask:
                    return True

        # Номер не найден
        return False


def get_user_coupon(phone_number, coupon_mask):
    if not os.path.isfile(user_db_path):
        return None
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[4] == phone_number:
                if row[5] == "":
                    return None
                if row[5][:7] == coupon_mask:
                    return row[5]
    return None