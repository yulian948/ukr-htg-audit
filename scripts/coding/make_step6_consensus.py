"""Крок 6: бланк консенсусу для зображень, де кодувальники розійшлися.

Бере results/fonts/step6_coding.csv (analyze_step6.py) і зображення coding_kit/step6/images/,
створює coding_kit/step6_consensus/консенсус_форм.xlsx: номер, зображення, літера, обидва
коди й порожній стовпець «Консенсус». Назв шрифтів у бланку немає.

Запуск: python3 scripts/coding/make_step6_consensus.py
"""

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
CODING = ROOT / "results" / "fonts" / "step6_coding.csv"
IMAGES = ROOT / "coding_kit" / "step6" / "images"
OUT = ROOT / "coding_kit" / "step6_consensus"
LABELS = {"1": "1 відповідає", "2": "2 відмінна", "0": "0 невизначено"}
W, H = 200, 160


def main():
    rows = list(csv.DictReader(open(CODING, encoding="utf-8")))
    coders = [k for k in rows[0] if k not in ("id", "font_id", "font", "group", "letter", "збіг")]
    disagree = [r for r in rows if r["збіг"] == "ні"]

    wb = Workbook()
    ws = wb.active
    ws.title = "консенсус"
    ws.append(["ID", "Зображення", "Літера", *(f"Код: {c}" for c in coders),
               "Консенсус: 1 відповідає / 2 відмінна / 0 невизначено", "Коментар"])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for col, width in zip("ABCDEFG", (8, 30, 8, 16, 16, 22, 40)):
        ws.column_dimensions[col].width = width
    dv = DataValidation(type="list", formula1='"1,2,0"', allow_blank=True,
                        error="Лише 1, 2 або 0", errorTitle="Невірний код")
    ws.add_data_validation(dv)
    for i, r in enumerate(disagree, start=2):
        ws.append([r["id"], None, r["letter"], *(LABELS[r[c]] for c in coders), None, None])
        img = XLImage(str(IMAGES / f"{r['id']}.png"))
        img.width, img.height = W * 0.6, H * 0.6
        ws.add_image(img, f"B{i}")
        ws.row_dimensions[i].height = H * 0.6 * 0.75 + 4
        dv.add(f"F{i}")
        for col in "ACDEF":
            ws[f"{col}{i}"].alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"
    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(OUT / "консенсус_форм.xlsx")
    print(f"{len(disagree)} розбіжностей → {OUT / 'консенсус_форм.xlsx'}")


if __name__ == "__main__":
    main()
