from path import Path
import os
import random

coupon_db_path = Path().joinpath('data', 'CouponCodes.txt')
used_coupon_db_path = Path().joinpath('data', 'UsedCouponCodes.txt')

def read(mask: str):
    coupon_codes = []
    if os.path.isfile(coupon_db_path):
        with open(coupon_db_path, mode='r', encoding='utf-8') as file:
            coupon_codes = [line.splitlines() for line in file if mask in line]
    return coupon_codes[0]
    
# def write(coupon_codes):
    # with open(coupon_db_path, mode='w', encoding='utf-8') as file:
        # file.write("\n".join(coupon_codes) + "\n")
        
def get_random_coupon_code(mask: str):
    print('Вход в get_random_coupon_code(' + mask + ')')
    if not coupon_db_path.exists():
        raise FileNotFoundError("Файл CouponCodes.txt не найден.")
    if not used_coupon_db_path.exists():
        open(used_coupon_db_path, 'a').close()
    
    with open(coupon_db_path, "r", encoding="utf-8") as file, open(used_coupon_db_path, 'r') as used_codes:
        codes = [line.strip() for line in file if mask in line.strip() and line not in used_codes]
    if not codes:
        raise ValueError("Файл CouponCodes.txt пуст.")
        return ''

    selected_code = random.choice(codes)
    print('get_random_coupon_code:selected_code = ' + selected_code)
    
    # Записываем свободный код в файл с использоваными кодами
    mark_code_as_used(selected_code)
    
    return selected_code
    

def mark_code_as_used(code_to_find):
    """
    Функция ищет указанный код в файле с кодами,
    и если находит, добавляет его в файл использованных кодов.
    """
    # Открываем файл с кодами для чтения
    with open(coupon_db_path, 'r') as codes:
        # Читаем все строки в список
        all_codes = codes.read().splitlines()
        
    # Проверяем, есть ли указанный код среди всех кодов
    if code_to_find in all_codes:
        print(f"Код '{code_to_find}' найден.")
        
        # Добавляем код в файл использованных кодов
        with open(used_coupon_db_path, 'a+') as used_codes:
            used_codes.write(f"{code_to_find}\n")  # добавляем код с новой строкой
            
        print(f"Код '{code_to_find}' добавлен в файл использованных кодов.")
    else:
        print(f"Код '{code_to_find}' не найден.")