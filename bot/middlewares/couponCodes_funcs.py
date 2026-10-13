from pathlib import Path
import random

import aiofiles


BASE_DIR = Path(__file__).resolve().parent.parent  # Переходим из middlewares в корень bot
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)  # Гарантируем существование папки data

coupon_db_path = DATA_DIR / 'CouponCodes.txt'
used_coupon_db_path = DATA_DIR / 'UsedCouponCodes.txt'


async def read(mask: str):
    coupon_codes = []
    if coupon_db_path.is_file():
        async with aiofiles.open(coupon_db_path, mode='r', encoding='utf-8') as file:
            async for line in file:
                if mask in line:
                    coupon_codes.append(line.splitlines())
    return coupon_codes[0]

# def write(coupon_codes):
    # with open(coupon_db_path, mode='w', encoding='utf-8') as file:
        # file.write("\n".join(coupon_codes) + "\n")


async def get_random_coupon_code(mask: str):
    print('Вход в get_random_coupon_code(' + mask + ')')
    if not coupon_db_path.exists():
        raise FileNotFoundError("Файл CouponCodes.txt не найден.")
    if not used_coupon_db_path.exists():
        async with aiofiles.open(used_coupon_db_path, 'a'):
            pass

    async with aiofiles.open(coupon_db_path, mode='r', encoding='utf-8') as file:
        all_lines = [line.strip() for line in await file.readlines()]
    async with aiofiles.open(used_coupon_db_path, mode='r', encoding='utf-8') as used_codes:
        used_set = {line.strip() for line in await used_codes.readlines()}

    codes = [line for line in all_lines if mask in line and line not in used_set]
    if not codes:
        raise ValueError("Файл CouponCodes.txt пуст.")

    selected_code = random.choice(codes)
    print('get_random_coupon_code:selected_code = ' + selected_code)

    # Записываем свободный код в файл с использоваными кодами
    await mark_code_as_used(selected_code)

    return selected_code


async def mark_code_as_used(code_to_find):
    """
    Функция ищет указанный код в файле с кодами,
    и если находит, добавляет его в файл использованных кодов.
    """
    # Открываем файл с кодами для чтения
    async with aiofiles.open(coupon_db_path, mode='r', encoding='utf-8') as codes:
        # Читаем все строки в список
        all_codes = (await codes.read()).splitlines()

    # Проверяем, есть ли указанный код среди всех кодов
    if code_to_find in all_codes:
        print(f"Код '{code_to_find}' найден.")

        # Добавляем код в файл использованных кодов
        async with aiofiles.open(used_coupon_db_path, mode='a+', encoding='utf-8') as used_codes:
            await used_codes.write(f"{code_to_find}\n")  # добавляем код с новой строкой

        print(f"Код '{code_to_find}' добавлен в файл использованных кодов.")
    else:
        print(f"Код '{code_to_find}' не найден.")
