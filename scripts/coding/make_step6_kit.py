"""Крок 6: комплект для незалежного кодування форм 9 літер двома кодувальниками.

Кожна з 9 літер (т д и п ш г б в з) у кожному з 59 шрифтів (results/fonts/font_list.json)
рендериться окремим зображенням (Pillow з libraqm, як в audit_fonts.py). Зображення
перемішано з фіксованим зерном і пронумеровано L001…L531 без назв шрифтів.

Результати:
- coding_kit/step6/images/L*.png — зображення;
- coding_kit/step6/кодування_форм.xlsx — бланк із вбудованими зображеннями і списком кодів;
- coding_kit/_key/step6_key.csv — ключ «номер → шрифт» (кодувальникам не передається).

Запуск: python3 scripts/coding/make_step6_kit.py
Шлях до шрифтів: AUDIT_WORK (типово ~/.cache/ukr-htg-audit/work); шляхи у font_list.json — відносно неї.
"""

import csv
import json
import os
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation
from PIL import Image, ImageDraw, ImageFont, features

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("AUDIT_WORK", Path.home() / ".cache" / "ukr-htg-audit" / "work"))
FONTS = json.loads((ROOT / "results" / "fonts" / "font_list.json").read_text(encoding="utf-8"))["fonts"]
KEY_LETTERS = ["т", "д", "и", "п", "ш", "г", "б", "в", "з"]
OUT = ROOT / "coding_kit" / "step6"
KEY = ROOT / "coding_kit" / "_key" / "step6_key.csv"
SEED = 20261027
SIZE, W, H = 96, 200, 160  # розмір кегля і полотна, px


def font_path(f):
    return WORK / f["path"]


def render(path, ch):
    font = ImageFont.truetype(str(path), SIZE, layout_engine=ImageFont.Layout.RAQM)
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)
    l, t, r, b = draw.textbbox((0, 0), ch, font=font)
    draw.text(((W - (r - l)) / 2 - l, (H - (b - t)) / 2 - t), ch, fill=0, font=font)
    return img


def main():
    if not features.check("raqm"):
        raise SystemExit("Pillow без libraqm")
    items = [(f, ch) for f in FONTS for ch in KEY_LETTERS]
    random.Random(SEED).shuffle(items)
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    KEY.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "кодування"
    ws.append(["ID", "Зображення", "Літера", "Код: 1 відповідає / 2 відмінна / 0 невизначено", "Коментар"])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 8, 30
    ws.column_dimensions["C"].width, ws.column_dimensions["D"].width = 8, 22
    ws.column_dimensions["E"].width = 40
    dv = DataValidation(type="list", formula1='"1,2,0"', allow_blank=True,
                        error="Лише 1, 2 або 0", errorTitle="Невірний код")
    ws.add_data_validation(dv)

    with open(KEY, "w", newline="", encoding="utf-8") as fk:
        key = csv.writer(fk)
        key.writerow(["id", "letter", "font_id", "font", "group"])
        for i, (f, ch) in enumerate(items, start=1):
            iid = f"L{i:03d}"
            png = OUT / "images" / f"{iid}.png"
            render(font_path(f), ch).save(png)
            row = i + 1
            ws.append([iid, None, ch, None, None])
            img = XLImage(str(png))
            img.width, img.height = W * 0.6, H * 0.6
            ws.add_image(img, f"B{row}")
            ws.row_dimensions[row].height = H * 0.6 * 0.75 + 4
            dv.add(f"D{row}")
            for col in "ACD":
                ws[f"{col}{row}"].alignment = Alignment(horizontal="center", vertical="center")
            key.writerow([iid, ch, f["id"], f["name"], f["group"]])
    ws.freeze_panes = "A2"
    wb.save(OUT / "кодування_форм.xlsx")
    print(f"{len(items)} зображень → {OUT}; ключ → {KEY}")


if __name__ == "__main__":
    main()
