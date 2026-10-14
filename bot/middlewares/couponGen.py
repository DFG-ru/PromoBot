import io
import logging

import aiofiles
import qrcode
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent  # Директория middlewares
OUTPUT_DIR = BASE_DIR / 'output'
TEMPLATES_DIR = BASE_DIR / 'templates'
FONTS_DIR = BASE_DIR / 'fonts'
# Запасной каталог шрифтов в корне репозитория
REQUIREMENTS_DIR = BASE_DIR.parent.parent / 'requirements'

DEFAULT_FONT_NAME = 'Shentox-Regular (RUS by Slavchansky).ttf'


def resolve_font_path(font: str | None) -> Path | None:
    """Находит файл шрифта, указанный в конфиге бота (поле font).

    Порядок поиска: абсолютный путь -> bot/middlewares/fonts/ -> requirements/.
    Если ничего не найдено — возвращает None (купон генерируется без номера).
    """
    candidates = []
    if font:
        p = Path(font)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.extend([FONTS_DIR / font, REQUIREMENTS_DIR / font])
    candidates.append(FONTS_DIR / DEFAULT_FONT_NAME)

    logging.debug(f"Поиск шрифта {font!r}, кандидаты: {[str(c) for c in candidates]}")
    for candidate in candidates:
        if candidate.is_file():
            logging.debug(f"Шрифт найден: {candidate}")
            return candidate
        logging.debug(f"Шрифт не найден по пути: {candidate}")
    logging.error(f"Шрифт {font!r} не найден ни в одном из каталогов: "
                  f"{', '.join(str(c.parent) for c in candidates)}")
    return None

# Гарантируем существование директорий
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


async def saveImage(img: Image, s: str):
    """Асинхронно сохраняет изображение купона в OUTPUT_DIR.

    PIL не умеет писать напрямую в асинхронный файловый объект,
    поэтому кодируем изображение в байтовый буфер и выгружаем его через aiofiles.
    """
    output_path = OUTPUT_DIR / f"{s}.jpg"
    buffer = io.BytesIO()
    img.convert('RGB').save(buffer, format='JPEG')
    logging.debug(f"Сохранение изображения купона: {output_path} ({len(buffer.getvalue())} байт)")
    async with aiofiles.open(output_path, 'wb') as f:
        await f.write(buffer.getvalue())
    logging.debug(f"Изображение купона сохранено: {output_path}")
    return output_path


def get_substrate_path(template: str):
    path = TEMPLATES_DIR / template
    logging.debug(f"Путь к подложке купона: {path}")
    return path
    

def drawNumber(img, s, xy=(0, 0), size=58, font: str | None = None):
    """Наносит номер купона на изображение.

    Шрифт берётся из конфигурации бота (поле font) и ищется через
    resolve_font_path(); если шрифт не найден — фиксируется ошибка в лог,
    купон генерируется без номера, без падения бота.
    """
    font_path = resolve_font_path(font)
    idraw = ImageDraw.Draw(img, "RGBA")
    if font_path is None:
        logging.debug("Шрифт не разрешён — пропуск нанесения номера купона")
        return
    try:
        truetype_font = ImageFont.truetype(str(font_path), size)
        logging.debug(f"Нанесение номера {s!r} в {xy}, размер {size}, шрифт {font_path}")
        idraw.text(xy, s, (255, 255, 255, 88), anchor="mt", font=truetype_font)
    except OSError:
        logging.error(f"Не удалось загрузить шрифт {font_path}, номер купона не нанесён")


async def couponGen(template: str, coupon, font: str | None = None):
    coupon = str(coupon)
    logging.debug(f"couponGen старт: template={template!r}, coupon={coupon!r}, font={font!r}")
    path_to_substrate = get_substrate_path(template)
    if not path_to_substrate.is_file():
        logging.error(f"Шаблон купона не найден: {path_to_substrate}")
        return False

    qr = gen_qr_code(coupon)
    logging.debug(f"QR-код сгенерирован: coupon={coupon!r}, размер qr={qr.size}")
    qr_xy = (52, 651)
    qr_width, qr_height = qr.size
    fontcords = (qr_xy[0] + qr_width / 2, qr_xy[1] + qr_width + 3)
    logging.debug(f"Координаты QR: {qr_xy}, координаты номера: {fontcords}")

    try:
        substrate = Image.open(path_to_substrate).convert("RGBA")
        logging.debug(f"Подложка открыта: {path_to_substrate}, размер {substrate.size}")
    except (FileNotFoundError, UnidentifiedImageError):
        logging.error(f"Шаблон купона не найден или повреждён: {path_to_substrate}")
        return False

    try:
        output_img = substrate.copy()

        alpha = Image.new('RGBA', (qr_width, qr_width), (255, 255, 255, int(255 * 0.40)))
        output_img.paste(alpha, qr_xy, alpha)

        output_img.paste(qr, qr_xy, qr)
        logging.debug("QR-код наложен на подложку")
    finally:
        substrate.close()

    drawNumber(output_img, coupon[7:], fontcords, 40, font=font)
    await saveImage(output_img, coupon[7:])

    logging.info(f"QR {coupon} создан")
    logging.debug(f"couponGen завершён: coupon={coupon!r}")
    return True


def gen_qr_code(text):
    text = str(text)
    logging.debug(f"Генерация QR-кода для текста: {text!r}")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.get_matrix()
    logging.debug(f"QR-матрица построена: версия {qr.version}, размер матрицы {len(img)}x{len(img[0]) if img else 0}")
    # for i in img:
        # for j in i:
            # if j:
                # print(1, end=' ')
            # else:
                # print(' ', end=' ')
        # print()

    coeff = 7                           #размер qr кода
    coeff_small = coeff / (300 / 100)   #размер кубиков 
    length_qr = len(img) * coeff

    output_qr = Image.new('RGBA', (length_qr, length_qr), (0, 0, 0, 0))
    
    black_1 = (0, 0, 0, 0)
    black_2 = (0, 0, 0, 230)
    white_1 = (255, 255, 255, 50)
    white_2 = (255, 255, 255, 230)

    white_3 = (0, 0, 0, 0)

    idraw = ImageDraw.Draw(output_qr, "RGBA")
    
    x = 0
    y = 0
    for string in qr.get_matrix():
        this_str = ''
        for i in string:
            if i:
                this_str += '1'
                idraw.rectangle((x + coeff_small, y + coeff_small, x + coeff - coeff_small, y + coeff - coeff_small),
                                fill=black_2)
            else:
                this_str += '0'
                idraw.rectangle((x + coeff_small, y + coeff_small, x + coeff - coeff_small, y + coeff - coeff_small),
                                fill=white_2)
            x += coeff
        x = 0
        y += coeff
        
    idraw.rectangle((0, 0, coeff * 9, coeff * 9), fill=white_1)
    idraw.rectangle((length_qr - coeff * 9, 0, length_qr, coeff * 9), fill=white_1)
    idraw.rectangle((0, length_qr - coeff * 9, coeff * 9, length_qr), fill=white_1)
    idraw.rectangle((length_qr - coeff * 10, length_qr - coeff * 9, length_qr - coeff * 6, length_qr - coeff * 6),
                    fill=white_1)
                    
    idraw.rectangle((coeff, coeff, coeff * 8, coeff * 2), fill=black_2)
    idraw.rectangle((length_qr - coeff * 8, coeff, length_qr - coeff, coeff * 2), fill=black_2)
    idraw.rectangle((coeff, coeff * 7, coeff * 8, coeff * 8), fill=black_2)
    idraw.rectangle((length_qr - coeff * 8, coeff * 7, length_qr - coeff, coeff * 8), fill=black_2)
    idraw.rectangle((coeff, length_qr - coeff * 8, coeff * 8, length_qr - coeff * 7), fill=black_2)
    idraw.rectangle((coeff, length_qr - coeff * 2, coeff * 8, length_qr - coeff), fill=black_2)
    idraw.rectangle((length_qr - coeff * 8, length_qr - coeff * 8, length_qr - coeff * 7, length_qr - coeff * 7),
                    fill=black_2)
    idraw.rectangle((coeff * 3, coeff * 3, coeff * 6, coeff * 6), fill=black_2)
    idraw.rectangle((length_qr - coeff * 6, coeff * 3, length_qr - coeff * 3, coeff * 6), fill=black_2)
    idraw.rectangle((coeff * 3, length_qr - coeff * 6, coeff * 6, length_qr - coeff * 3), fill=black_2)
    idraw.rectangle((coeff, coeff, coeff * 2, coeff * 8), fill=black_2)
    idraw.rectangle((coeff * 7, coeff, coeff * 8, coeff * 8), fill=black_2)

    idraw.rectangle((length_qr - coeff * 2, coeff, length_qr - coeff, coeff * 8), fill=black_2)
    idraw.rectangle((length_qr - coeff * 8, coeff, length_qr - coeff * 7, coeff * 8), fill=black_2)

    idraw.rectangle((coeff, length_qr - coeff * 8, coeff * 2, length_qr - coeff), fill=black_2)
    idraw.rectangle((coeff * 7, length_qr - coeff * 8, coeff * 8, length_qr - coeff), fill=black_2)

    idraw.rectangle((length_qr - coeff * 10, length_qr - coeff * 10, length_qr - coeff * 9, length_qr - coeff * 5),
                    fill=black_2)
    idraw.rectangle((length_qr - coeff * 6, length_qr - coeff * 10, length_qr - coeff * 5, length_qr - coeff * 5),
                    fill=black_2)

    idraw.rectangle((length_qr - coeff * 10, length_qr - coeff * 10, length_qr - coeff * 6, length_qr - coeff * 9),
                    fill=black_2)
    idraw.rectangle((length_qr - coeff * 10, length_qr - coeff * 6, length_qr - coeff * 6, length_qr - coeff * 5),
                    fill=black_2)
    return output_qr
