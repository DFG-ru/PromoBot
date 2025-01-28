import qrcode
from PIL import Image, ImageDraw, ImageFont
from pyzbar.pyzbar import decode
from path import Path
from msvcrt import getch
from random import randint
from os import mkdir, path, getcwd


def saveImage(img: Image, s: str):
    img.convert('RGB').save(Path().joinpath("middlewares\\output", s + ".jpg"))


def get_substrate_path(template: str):
    return Path().joinpath("middlewares\\templates", template)


def drawNumber(img, s, xy=(0,0), size=58):
    f = 'Shentox-Regular (RUS by Slavchansky).ttf'
    # font = 'segoeuib.ttf'
    idraw = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype(f, size)
        idraw.text(xy, s, (255,255,255,88), anchor="mt", font=font)
    except:
        print("Ошибка:")
        print("Нужно установить шрифт:\n" + f + "\n")
        getch()


def couponGen(template: str, code: str):
    path_to_substrate = get_substrate_path(template)
    
    coupon = code
    qr = gen_qr_code(coupon)
    qr_xy = (52, 651)
    qr_width, qr_height = qr.size
    fontcords = (qr_xy[0] + qr_width / 2, qr_xy[1] + qr_width + 3)
    
    try:
        substrate = Image.open(path_to_substrate).convert("RGBA")
        output_img = substrate.copy()

        alpha = Image.new('RGBA', (qr_width, qr_width), (255, 255, 255, int(255 * 0.40)))
        output_img.paste(alpha, qr_xy, alpha)

        output_img.paste(qr, qr_xy, qr)
        substrate.close()
    except FileNotFoundError as err:
        print(f"Файл не найден")
        print(path_to_substrate)
        return False
    
    drawNumber(output_img, coupon[7:], fontcords, 40)
    saveImage(output_img, coupon[7:])
    
    print(f"QR {coupon} создан")


def gen_qr_code(text: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.get_matrix()
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
