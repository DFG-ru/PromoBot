"""Генерация изображения купона: QR-код + номер на подложке (шаблоне)."""
import io
import logging
from pathlib import Path

import aiofiles
import qrcode
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from bot.paths import BOT_ROOT

MIDDLEWARES_DIR = BOT_ROOT / "middlewares"
OUTPUT_DIR = MIDDLEWARES_DIR / "output"
TEMPLATES_DIR = MIDDLEWARES_DIR / "templates"
FONTS_DIR = MIDDLEWARES_DIR / "fonts"
# Запасной каталог шрифтов в корне репозитория
REQUIREMENTS_DIR = BOT_ROOT.parent / "requirements"

DEFAULT_FONT_NAME = "Shentox-Regular (RUS by Slavchansky).ttf"

# Гарантируем существование рабочих директорий
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def resolve_font_path(font: str | None, fonts_dir=None) -> Path | None:
    """Находит файл шрифта, указанный в конфиге бота (поле font).

    Порядок поиска: абсолютный путь -> bot/middlewares/fonts/ -> requirements/.
    Если ничего не найдено — возвращает None (купон генерируется без номера).
    """
    target_fonts_dir = fonts_dir or FONTS_DIR
    candidates = []
    if font:
        p = Path(font)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.extend([target_fonts_dir / font, REQUIREMENTS_DIR / font])
    candidates.append(target_fonts_dir / DEFAULT_FONT_NAME)

    logging.debug(f"Поиск шрифта {font!r}, кандидаты: {[str(c) for c in candidates]}")
    for candidate in candidates:
        if candidate.is_file():
            logging.debug(f"Шрифт найден: {candidate}")
            return candidate
        logging.debug(f"Шрифт не найден по пути: {candidate}")
    logging.error(f"Шрифт {font!r} не найден ни в одном из каталогов: "
                  f"{', '.join(str(c.parent) for c in candidates)}")
    return None


async def save_image(img: Image.Image, name: str, output_dir=None) -> Path:
    """Асинхронно сохраняет изображение купона в OUTPUT_DIR.

    PIL не умеет писать напрямую в асинхронный файловый объект,
    поэтому кодируем изображение в байтовый буфер и выгружаем его через aiofiles.
    """
    target = output_dir or OUTPUT_DIR
    output_path = target / f"{name}.jpg"
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG")
    logging.debug(f"Сохранение изображения купона: {output_path} ({len(buffer.getvalue())} байт)")
    async with aiofiles.open(output_path, "wb") as file:
        await file.write(buffer.getvalue())
    logging.debug(f"Изображение купона сохранено: {output_path}")
    return output_path


def get_substrate_path(template: str, templates_dir=None) -> Path:
    path = (templates_dir or TEMPLATES_DIR) / template
    logging.debug(f"Путь к подложке купона: {path}")
    return path


def draw_number(img: Image.Image, text: str, xy=(0, 0), size=58,
                font: str | None = None, fonts_dir=None) -> None:
    """Наносит номер купона на изображение.

    Шрифт берётся из конфигурации бота (поле font) и ищется через
    resolve_font_path(); если шрифт не найден — фиксируется ошибка в лог,
    купон генерируется без номера, без падения бота.
    """
    font_path = resolve_font_path(font, fonts_dir=fonts_dir)
    idraw = ImageDraw.Draw(img, "RGBA")
    if font_path is None:
        logging.debug("Шрифт не разрешён — пропуск нанесения номера купона")
        return
    try:
        truetype_font = ImageFont.truetype(str(font_path), size)
        logging.debug(f"Нанесение номера {text!r} в {xy}, размер {size}, шрифт {font_path}")
        idraw.text(xy, text, (255, 255, 255, 88), anchor="mt", font=truetype_font)
    except OSError:
        logging.error(f"Не удалось загрузить шрифт {font_path}, номер купона не нанесён")


async def generate_coupon_image(template: str, coupon: str, font: str | None = None,
                                 output_dir=None, templates_dir=None, fonts_dir=None) -> bool:
    """Собирает купон: подложка + полупрозрачный QR + номер. True при успехе."""
    coupon = str(coupon)
    target_out = output_dir or OUTPUT_DIR
    target_tpl = templates_dir or TEMPLATES_DIR
    logging.debug(f"generate_coupon_image старт: template={template!r}, "
                  f"coupon={coupon!r}, font={font!r}")
    path_to_substrate = get_substrate_path(template, templates_dir=target_tpl)
    if not path_to_substrate.is_file():
        logging.error(f"Шаблон купона не найден: {path_to_substrate}")
        return False

    qr = gen_qr_code(coupon)
    logging.debug(f"QR-код сгенерирован: coupon={coupon!r}, размер qr={qr.size}")
    qr_xy = (52, 651)
    qr_width, qr_height = qr.size
    number_xy = (qr_xy[0] + qr_width / 2, qr_xy[1] + qr_width + 3)
    logging.debug(f"Координаты QR: {qr_xy}, координаты номера: {number_xy}")

    try:
        substrate = Image.open(path_to_substrate).convert("RGBA")
        logging.debug(f"Подложка открыта: {path_to_substrate}, размер {substrate.size}")
    except (FileNotFoundError, UnidentifiedImageError):
        logging.error(f"Шаблон купона не найден или повреждён: {path_to_substrate}")
        return False

    try:
        output_img = substrate.copy()

        alpha = Image.new("RGBA", (qr_width, qr_width), (255, 255, 255, int(255 * 0.40)))
        output_img.paste(alpha, qr_xy, alpha)

        output_img.paste(qr, qr_xy, qr)
        logging.debug("QR-код наложен на подложку")
    finally:
        substrate.close()

    # Файл и имя купона — по последним 6 символам кода, номер — без маски (7 символов).
    draw_number(output_img, coupon[7:], number_xy, 40, font=font, fonts_dir=fonts_dir)
    await save_image(output_img, coupon[-6:], output_dir=target_out)

    logging.info(f"QR {coupon} создан")
    logging.debug(f"generate_coupon_image завершён: coupon={coupon!r}")
    return True


def gen_qr_code(text: str) -> Image.Image:
    """Рисует «стилизованный» QR-код со скруглёнными зонами finder-паттернов."""
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
    matrix = qr.get_matrix()
    logging.debug(f"QR-матрица построена: версия {qr.version}, "
                  f"размер матрицы {len(matrix)}x{len(matrix[0]) if matrix else 0}")

    coeff = 7                           # размер модуля QR-кода
    coeff_small = coeff / (300 / 100)   # отступ кубика внутри модуля
    length_qr = len(matrix) * coeff

    output_qr = Image.new("RGBA", (length_qr, length_qr), (0, 0, 0, 0))

    white_1 = (255, 255, 255, 50)     # фон зон finder-паттернов
    black_2 = (0, 0, 0, 230)          # тёмные модули/рамки
    white_2 = (255, 255, 255, 230)    # светлые модули

    idraw = ImageDraw.Draw(output_qr, "RGBA")

    x = y = 0
    for row in matrix:
        for cell in row:
            fill = black_2 if cell else white_2
            idraw.rectangle((x + coeff_small, y + coeff_small,
                             x + coeff - coeff_small, y + coeff - coeff_small),
                            fill=fill)
            x += coeff
        x = 0
        y += coeff

    def rect(a, b, c, d, fill):
        idraw.rectangle((a, b, c, d), fill=fill)

    L = length_qr
    # Светлые подложки трёх finder-паттернов и alignment-паттерна
    rect(0, 0, coeff * 9, coeff * 9, white_1)
    rect(L - coeff * 9, 0, L, coeff * 9, white_1)
    rect(0, L - coeff * 9, coeff * 9, L, white_1)
    rect(L - coeff * 10, L - coeff * 9, L - coeff * 6, L - coeff * 6, white_1)

    # Рамки finder-паттернов (верхний левый, верхний правый, нижний левый)
    rect(coeff, coeff, coeff * 8, coeff * 2, black_2)
    rect(L - coeff * 8, coeff, L - coeff, coeff * 2, black_2)
    rect(coeff, coeff * 7, coeff * 8, coeff * 8, black_2)
    rect(L - coeff * 8, coeff * 7, L - coeff, coeff * 8, black_2)
    rect(coeff, L - coeff * 8, coeff * 8, L - coeff * 7, black_2)
    rect(coeff, L - coeff * 2, coeff * 8, L - coeff, black_2)
    rect(L - coeff * 8, L - coeff * 8, L - coeff * 7, L - coeff * 7, black_2)
    # Центральные квадраты
    rect(coeff * 3, coeff * 3, coeff * 6, coeff * 6, black_2)
    rect(L - coeff * 6, coeff * 3, L - coeff * 3, coeff * 6, black_2)
    rect(coeff * 3, L - coeff * 6, coeff * 6, L - coeff * 3, black_2)
    # Боковые стороны рамок
    rect(coeff, coeff, coeff * 2, coeff * 8, black_2)
    rect(coeff * 7, coeff, coeff * 8, coeff * 8, black_2)
    rect(L - coeff * 2, coeff, L - coeff, coeff * 8, black_2)
    rect(L - coeff * 8, coeff, L - coeff * 7, coeff * 8, black_2)
    rect(coeff, L - coeff * 8, coeff * 2, L - coeff, black_2)
    rect(coeff * 7, L - coeff * 8, coeff * 8, L - coeff, black_2)

    # Alignment-паттерн (нижний правый угол)
    rect(L - coeff * 10, L - coeff * 10, L - coeff * 9, L - coeff * 5, black_2)
    rect(L - coeff * 6, L - coeff * 10, L - coeff * 5, L - coeff * 5, black_2)
    rect(L - coeff * 10, L - coeff * 10, L - coeff * 6, L - coeff * 9, black_2)
    rect(L - coeff * 10, L - coeff * 6, L - coeff * 6, L - coeff * 5, black_2)
    return output_qr
