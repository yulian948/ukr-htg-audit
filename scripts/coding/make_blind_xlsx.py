"""Крок 7: бланк сліпої оцінки рівня 3 у форматі xlsx із вбудованими зображеннями.

Бере теку blind/ з make_blind.py (images/B*.png і rating.csv) і створює поруч
оцінка_рівень3.xlsx: номер, зображення, слово, цільовий символ, код, коментар.
Ключ key.csv не читається і в бланк не потрапляє.

Запуск: python3 scripts/coding/make_blind_xlsx.py <шлях до теки blind>
"""

import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation
from PIL import Image

MAX_W, MAX_H = 360, 72  # розмір зображення в бланку, px


def main():
    blind = Path(sys.argv[1])
    rows = list(csv.reader(open(blind / "rating.csv", encoding="utf-8")))[1:]
    wb = Workbook()
    ws = wb.active
    ws.title = "оцінка"
    ws.append(["ID", "Зображення", "Слово", "Цільовий символ",
               "Код: 1 потрібна літера / 2 інша літера / 0 невпізнавано", "Коментар"])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for col, width in zip("ABCDEF", (8, 52, 16, 10, 24, 40)):
        ws.column_dimensions[col].width = width
    dv = DataValidation(type="list", formula1='"1,2,0"', allow_blank=True,
                        error="Лише 1, 2 або 0", errorTitle="Невірний код")
    ws.add_data_validation(dv)
    for i, (bid, word, target, *_rest) in enumerate(rows, start=2):
        ws.append([bid, None, word, target, None, None])
        with Image.open(blind / "images" / f"{bid}.png") as im:
            scale = min(MAX_W / im.width, MAX_H / im.height)
        img = XLImage(str(blind / "images" / f"{bid}.png"))
        img.width, img.height = img.width * scale, img.height * scale
        ws.add_image(img, f"B{i}")
        ws.row_dimensions[i].height = MAX_H * 0.75 + 4
        dv.add(f"E{i}")
        for col in "ACDE":
            ws[f"{col}{i}"].alignment = Alignment(horizontal="center", vertical="center")
        ws[f"C{i}"].font = ws[f"D{i}"].font = Font(size=14)
    ws.freeze_panes = "A2"
    wb.save(blind / "оцінка_рівень3.xlsx")
    print(f"{len(rows)} рядків → {blind / 'оцінка_рівень3.xlsx'}")


if __name__ == "__main__":
    main()
