"""Крок 5: покриття інвентарю й рендеринг для кожного шрифту з results/fonts/font_list.json.

Для кожного символу інвентарю:
- cmap — чи є кодові точки в таблиці cmap (fontTools; для Kobzar KS — HarfBuzz, див. нижче);
- shaping — HarfBuzz: чи потрапляє в результат .notdef (gid 0), чи прикріплено комбінований знак;
- render — Pillow з libraqm (так рендерить ukrainian-handwriting-synth): чи є чорнило на зображенні.
Статус: ok | missing (немає в cmap → .notdef) | empty_glyph (у cmap є, але гліф порожній).
Для комбінованих знаків додатково: чи збігається рендеринг по одному символу (як у doc_gen)
з рендерингом цілого рядка.

Kobzar KS: ліцензія забороняє розбір шрифту, тому для нього таблиці не читаємо fontTools,
а лише рендеримо (HarfBuzz і Pillow) — тобто користуємося шрифтом як будь-яка програма.

Запуск: python3 scripts/fonts/audit_fonts.py
Результати: results/fonts/coverage.json, coverage.csv, summary.md, sheets/*.png,
key_letters.png і key_letters_coding.csv (бланк для кроку 6).
"""

import csv
import json
import os
import sys
import unicodedata
from pathlib import Path

import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, features

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("AUDIT_WORK", Path.home() / ".cache" / "ukr-htg-audit" / "work"))
sys.path.insert(0, str(ROOT / "inventory"))
from load import load_inventory  # noqa: E402

OUT = ROOT / "results" / "fonts"
FONTS = json.loads((OUT / "font_list.json").read_text(encoding="utf-8"))["fonts"]
SIZE = 64
GROUPS = ("alphabet", "apostrophe", "punctuation", "historical")
KEY = ["т", "д", "и", "п", "ш", "г", "б", "в", "з"]
NO_TABLE_READING = {"kobzar"}  # джерела, для яких не читаємо таблиці шрифту (ліцензія)


def hb_font(path):
    blob = hb.Blob.from_file_path(str(path))
    return hb.Font(hb.Face(blob))


def hb_cmap(font, text):
    return [font.get_nominal_glyph(ord(c)) is not None for c in text]


def shape(font, text, feats=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats or {})
    return buf.glyph_infos, buf.glyph_positions


def ink(img):
    return int((np.asarray(img) < 128).sum())


def render(pil_font, text, per_char=False):
    """Біле тло, чорний текст; per_char — по одному символу, як у doc_gen."""
    img = Image.new("L", (SIZE * 4 * max(1, len(text)), SIZE * 3), 255)
    draw = ImageDraw.Draw(img)
    if per_char:
        x = SIZE
        for ch in text:
            draw.text((x, SIZE), ch, fill=0, font=pil_font)
            x += draw.textlength(ch, font=pil_font)
    else:
        draw.text((SIZE, SIZE), text, fill=0, font=pil_font)
    return img


def audit_font(f, entries):
    path = WORK / f["path"]  # шляхи у font_list.json — відносно AUDIT_WORK
    font = hb_font(path)
    pil_font = ImageFont.truetype(str(path), SIZE, layout_engine=ImageFont.Layout.RAQM)
    tt_cmap = None
    if f["group"] not in NO_TABLE_READING:
        tt_cmap = TTFont(str(path), lazy=True).getBestCmap() or {}
    rows = {}
    for e in entries:
        text = e["char"]
        in_hb = hb_cmap(font, text)
        in_tt = [ord(c) in tt_cmap for c in text] if tt_cmap is not None else None
        infos, pos = shape(font, text)
        notdef = any(i.codepoint == 0 for i in infos)
        img = render(pil_font, text)
        n_ink = ink(img)
        if not all(in_hb):
            status = "missing"
        elif n_ink == 0:
            status = "empty_glyph"
        else:
            status = "ok"
        row = {"status": status, "cmap": all(in_hb), "notdef": notdef, "ink": n_ink,
               "missing": [f"U+{ord(c):04X}" for c, ok in zip(text, in_hb) if not ok]}
        if in_tt is not None and in_tt != in_hb:
            row["cmap_disagreement"] = {"fontTools": in_tt, "harfbuzz": in_hb}
        if len(text) > 1 and unicodedata.combining(text[-1]) and status == "ok":
            mark = pos[-1]
            row["mark_offset"] = [mark.x_offset, mark.y_offset]
            row["mark_glyphs"] = len(infos)
            whole = np.asarray(img) < 128
            split = np.asarray(render(pil_font, text, per_char=True)) < 128
            row["per_char_differs"] = bool((whole != split).sum() > 0.02 * max(1, whole.sum()))
        rows[e["id"]] = row
    accepted = all(font.get_nominal_glyph(ord(e["char"])) is not None
                   for e in entries if e["group"] == "alphabet")
    return rows, accepted


def sheet(f, entries, rows, label_font):
    cols, cell = 12, 96
    lines = -(-len(entries) // cols)
    img = Image.new("L", (cols * cell, lines * cell + 40), 255)
    draw = ImageDraw.Draw(img)
    draw.text((8, 8), f"{f['id']} {f['name']} — {f['ref']}", fill=0, font=label_font)
    pil_font = ImageFont.truetype(str(WORK / f["path"]), 48, layout_engine=ImageFont.Layout.RAQM)
    for i, e in enumerate(entries):
        x, y = (i % cols) * cell, 40 + (i // cols) * cell
        r = rows[e["id"]]
        draw.rectangle([x, y, x + cell - 1, y + cell - 1], outline=200 if r["status"] == "ok" else 0,
                       width=1 if r["status"] == "ok" else 3)
        draw.text((x + 18, y + 12), e["char"], fill=0, font=pil_font)
        draw.text((x + 4, y + cell - 18), " ".join(e["codepoints"]), fill=110, font=label_font)
    return img


def key_letters(fonts, label_font):
    cell, left = 90, 300
    img = Image.new("L", (left + cell * len(KEY), 50 + cell * len(fonts)), 255)
    draw = ImageDraw.Draw(img)
    for j, ch in enumerate(KEY):
        draw.text((left + j * cell + 35, 15), ch, fill=0, font=ImageFont.truetype(LABEL_CYR, 28))
    for i, f in enumerate(fonts):
        y = 50 + i * cell
        draw.text((8, y + 30), f"{f['id']} {f['name']}"[:34], fill=0, font=label_font)
        pil_font = ImageFont.truetype(str(WORK / f["path"]), 56, layout_engine=ImageFont.Layout.RAQM)
        for j, ch in enumerate(KEY):
            draw.text((left + j * cell + 20, y + 5), ch, fill=0, font=pil_font)
        draw.line([0, y, img.width, y], fill=220)
    return img


def main():
    if not features.check("raqm"):
        raise SystemExit("Pillow без libraqm: результати рендерингу не відповідатимуть інструментам синтетики")
    inv, entries = load_inventory()
    label_font = ImageFont.truetype(LABEL_LATIN, 13)
    (OUT / "sheets").mkdir(parents=True, exist_ok=True)
    results = {}
    for f in FONTS:
        rows, accepted = audit_font(f, entries)
        results[f["id"]] = {"font": f, "accepted_by_ukr_synth": accepted, "entries": rows}
        sheet(f, entries, rows, label_font).save(OUT / "sheets" / f"{f['id']}.png")
        bad = sum(r["status"] != "ok" for r in rows.values())
        print(f"{f['id']} {f['name'][:32]:<32} не ok: {bad:3d}  усі 66 літер: {'так' if accepted else 'ні'}")

    (OUT / "coverage.json").write_text(json.dumps({
        "inventory_version": inv["inventory_version"],
        "render": {"pillow_raqm": features.version("raqm"), "harfbuzz": hb.version_string(), "size_px": SIZE},
        "fonts": results}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(OUT / "coverage.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "char", "codepoints", "group"] + [f"{r['font']['id']} {r['font']['name']}" for r in results.values()])
        for e in entries:
            w.writerow([e["id"], e["char"], " ".join(e["codepoints"]), e["group"]]
                       + [r["entries"][e["id"]]["status"] for r in results.values()])
    write_summary(results, entries)
    key_letters(FONTS, label_font).save(OUT / "key_letters.png")
    with open(OUT / "key_letters_coding.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["font_id", "font", "letter", "code (відповідає / відмінна / невизначено)", "коментар"])
        for f in FONTS:
            for ch in KEY:
                w.writerow([f["id"], f["name"], ch, "", ""])


def write_summary(results, entries):
    by_group = {g: [e for e in entries if e["group"] == g] for g in GROUPS}
    ukr = [e for e in entries if e["char"] in "ґҐєЄіІїЇ"]
    apo = next(e for e in entries if e["codepoints"] == ["U+02BC"])
    lines = ["# Крок 5: покриття інвентарю шрифтами", "",
             "ok — символ є в cmap і має гліф; missing — немає в cmap (рендериться .notdef); "
             "empty_glyph — у cmap є, але гліф порожній. Повні дані — coverage.json/csv, аркуші — sheets/.", "",
             "| ID | Шрифт | Джерело | " + " | ".join(GROUPS) + " | ґєії | ʼ U+02BC | Не ok |",
             "|---|---|---|" + "---|" * (len(GROUPS) + 3)]
    for r in results.values():
        f, rows = r["font"], r["entries"]
        cells = [f"{sum(rows[e['id']]['status'] == 'ok' for e in by_group[g])}/{len(by_group[g])}" for g in GROUPS]
        ukr_ok = sum(rows[e["id"]]["status"] == "ok" for e in ukr)
        bad = [next(e["char"] for e in entries if e["id"] == i) for i, x in rows.items() if x["status"] != "ok"]
        lines.append(f"| {f['id']} | {f['name']} | {f['group']} | " + " | ".join(cells)
                     + f" | {ukr_ok}/8 | {'так' if rows[apo['id']]['status'] == 'ok' else 'ні'} | "
                     + (" ".join(bad) if len(bad) <= 24 else " ".join(bad[:24]) + f" … (+{len(bad) - 24})") + " |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _label_fonts():
    """Підписи на аркушах — друкованим шрифтом з ukrainian-handwriting-synth (є латиниця й кирилиця)."""
    synth = next((WORK / f["path"]).parents[1] for f in FONTS if f["group"] == "ukrainian-handwriting-synth")
    p = synth / "printed_fonts" / "OpenSans-Regular.ttf"
    return str(p), str(p)


LABEL_LATIN, LABEL_CYR = _label_fonts()

if __name__ == "__main__":
    main()
