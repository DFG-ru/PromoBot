from path import Path
import csv
import os

user_db_path = Path().joinpath('data', 'UserDatabase.csv')

def write(user_id, first_name, last_name, username, contact=None, coupon_code=None):
    file_exists = os.path.isfile(user_db_path)
    with open(user_db_path, mode='a+', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        if not file_exists:
            writer.writerow(
                ['ID', 'Имя', 'Фамилия', 'Имя пользователя', 'Номер телефона', 'Купон'])
        writer.writerow([user_id, first_name or "Не указано", last_name or "Не указано", username or "Не указано",
                         contact or "Не указано", f"{coupon_code}" or "Не указано"])


def update(phone_number, new_data):
    if not os.path.isfile(user_db_path):
        return
    rows = []
    updated = False
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    if rows:
        header = rows[0]
        for i, row in enumerate(rows[1:], start=1):
            if row[4] == phone_number:
                rows[i] = [
                    row[0],
                    new_data.get('first_name', row[1]),
                    new_data.get('last_name', row[2]),
                    new_data.get('username', row[3]),
                    row[4],
                    row[5]
                ]
                updated = True
                break
    if updated:
        with open(user_db_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)


def phone_exist(phone_number):
    if not os.path.isfile(user_db_path):
        return False
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if row[4] == phone_number:
                return True
    return False
    
def get_user_coupon(phone_number):
    if not os.path.isfile(user_db_path):
        return None
    with open(user_db_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if row[4] == phone_number:
                return row[5]
    return None