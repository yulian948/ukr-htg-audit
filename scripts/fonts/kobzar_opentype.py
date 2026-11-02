"""Крок 5: чи справді застосовуються OpenType-варіанти Kobzar KS.

Лише рендеринг (HarfBuzz і Pillow з libraqm) — таблиць шрифту fontTools не читаємо, бо
ліцензія Kobzar KS забороняє розбір шрифту. Перевіряємо:
1) які функції GSUB оголошує шрифт (так їх бачить кожен рушій шейпінгу);
2) чи дає типовий шейпінг різні гліфи для тієї самої літери в різних контекстах;
3) що змінюється, якщо вимкнути кожну функцію, і що — якщо ввімкнути необов'язкові (salt, ssXX);
4) чи застосовує їх Pillow типово (як у ukrainian-handwriting-synth) і що лишається при
   рендерингу по одному символу (як у doc_gen).

Запуск: python3 scripts/fonts/kobzar_opentype.py
Результати: results/fonts/kobzar_opentype.json, kobzar_opentype.png
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("AUDIT_WORK", Path.home() / ".cache" / "ukr-htg-audit" / "work"))
sys.path.insert(0, str(ROOT / "inventory"))
from load import load_inventory  # noqa: E402

OUT = ROOT / "results" / "fonts"
FONT = next(f for f in json.loads((OUT / "font_list.json").read_text(encoding="utf-8"))["fonts"]
            if f["group"] == "kobzar")
DEFAULT_ON = {"ccmp", "locl", "rlig", "calt", "clig", "liga", "kern", "mark", "mkmk", "rclt", "curs"}
WORDS = ["Тараса", "Шевченка", "аааа", "ннн", "мама", "оборона", "щастя", "пʼять", "мережа", "Кобзар",
         "садок вишневий коло хати"]


def shape(font, text, feats=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats or {})
    return [(i.codepoint, i.cluster) for i in buf.glyph_infos]


def gids(font, text, feats=None):
    return [g for g, _ in shape(font, text, feats)]


def variants_by_char(font, texts, feats=None):
    """Для кожного символу — набір гліфів, якими HarfBuzz його подав у різних контекстах."""
    seen = defaultdict(set)
    for t in texts:
        out = shape(font, t, feats)
        by_cluster = defaultdict(list)
        for g, c in out:
            by_cluster[c].append(g)
        for c, gs in by_cluster.items():
            if t[c].strip():
                seen[t[c]].add(tuple(gs))
    return {ch: len(v) for ch, v in seen.items() if len(v) > 1}


def pil(text, feats=None, per_char=False, size=64):
    font = ImageFont.truetype(str(WORK / FONT["path"]), size, layout_engine=ImageFont.Layout.RAQM)
    img = Image.new("L", (size * len(text) + 2 * size, size * 2), 255)
    draw = ImageDraw.Draw(img)
    if per_char:
        x = size // 2
        for ch in text:
            draw.text((x, size // 3), ch, fill=0, font=font)
            x += draw.textlength(ch, font=font)
    else:
        draw.text((size // 2, size // 3), text, fill=0, font=font, features=feats)
    return img


def feature_tags(face, table):
    """Функції таблиці для всіх скриптів і мов — так їх бачить рушій шейпінгу."""
    tags = set()
    for si, _ in enumerate(face.get_table_script_tags(table)):
        langs = face.get_script_language_tags(table, si)
        for li in [0xFFFF, *range(len(langs))]:
            tags.update(face.get_language_feature_tags(table, si, li))
    return sorted(tags)


def diff(a, b):
    a, b = np.asarray(a) < 128, np.asarray(b) < 128
    return round(float((a != b).sum() / max(1, a.sum())), 3)


def main():
    face = hb.Face(hb.Blob.from_file_path(str(WORK / FONT["path"])))
    font = hb.Font(face)
    gsub, gpos = feature_tags(face, "GSUB"), feature_tags(face, "GPOS")
    inv, entries = load_inventory()
    texts = WORDS + [inv["test_strings"][k] for k in ("pangram", "quick", "punctuation_line")]
    off_all = {t: False for t in gsub}

    per_feature = {}
    for tag in gsub:
        changed = sum(gids(font, t) != gids(font, t, {tag: False}) for t in texts)
        enabled = sum(gids(font, t) != gids(font, t, {tag: True}) for t in texts)
        per_feature[tag] = {"default_on": tag in DEFAULT_ON, "texts_changed_when_off": changed,
                            "texts_changed_when_forced_on": enabled}

    default_vars = variants_by_char(font, texts)
    plain_vars = variants_by_char(font, texts, off_all)
    optional = [t for t in gsub if t not in DEFAULT_ON and per_feature[t]["texts_changed_when_forced_on"]]
    forced_vars = {t: variants_by_char(font, texts, {t: True}) for t in optional}
    forced_all = variants_by_char(font, texts, {t: True for t in ("init", "fina", "salt") if t in gsub})
    # Скільки різних форм шрифт має для кожної літери абетки: ізольована літера
    # з типовими налаштуваннями та з кожною необов'язковою функцією окремо
    settings = [{}] + [{t: True} for t in optional]
    alt_forms = {}
    for e in entries:
        if e["group"] == "alphabet":
            forms = {tuple(gids(font, e["char"], f)) for f in settings}
            alt_forms[e["char"]] = len(forms)
    pil_cmp = {}
    for t in WORDS:
        base = pil(t)
        pil_cmp[t] = {"no_gsub_features": diff(base, pil(t, feats=[f"-{x}" for x in gsub])),
                      "per_char_doc_gen": diff(base, pil(t, per_char=True))}

    result = {
        "font": FONT["ref"], "sha256": FONT["sha256"], "harfbuzz": hb.version_string(),
        "gsub_features": gsub, "gpos_features": gpos, "per_feature": per_feature,
        "chars_with_contextual_variants_default": default_vars,
        "chars_with_variants_all_gsub_off": plain_vars,
        "chars_with_variants_when_forced_on": forced_vars,
        "chars_with_variants_init_fina_salt": forced_all,
        "forms_per_letter_across_features": alt_forms,
        "pillow_pixel_difference": pil_cmp,
        "note": "pixel difference = частка пікселів чорнила, що різняться, відносно типового рендерингу Pillow (libraqm)",
    }
    (OUT / "kobzar_opentype.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    rows = [("типово (Pillow + libraqm, як ukrainian-handwriting-synth)", lambda t: pil(t)),
            ("усі функції GSUB вимкнено", lambda t: pil(t, feats=[f"-{x}" for x in gsub])),
            ("по одному символу (як doc_gen)", lambda t: pil(t, per_char=True))]
    sample = "Тараса Шевченка аааа щастя"
    imgs = [(label, fn(sample)) for label, fn in rows]
    sheet = Image.new("L", (imgs[0][1].width, sum(i.height + 24 for _, i in imgs)), 255)
    d, y = ImageDraw.Draw(sheet), 0
    for label, img in imgs:
        d.text((8, y + 4), label, fill=0)
        sheet.paste(img, (0, y + 24))
        y += img.height + 24
    sheet.save(OUT / "kobzar_opentype.png")

    print("GSUB:", ", ".join(gsub) or "—", "| GPOS:", ", ".join(gpos) or "—")
    for tag, r in per_feature.items():
        print(f"  {tag}: типово {'увімк.' if r['default_on'] else 'вимк.'}; вимкнення змінює {r['texts_changed_when_off']} "
              f"з {len(texts)} рядків; примусове ввімкнення змінює {r['texts_changed_when_forced_on']}")
    print("Літери з кількома варіантами (типово):", default_vars or "—")
    print("…з вимкненим GSUB:", plain_vars or "—")
    for t, v in forced_vars.items():
        print(f"…з увімкненим {t}: {len(v)} літер мають кілька форм", dict(list(v.items())[:12]))
    print(f"…з init+fina+salt: {len(forced_all)} літер мають кілька форм")
    multi = {k: v for k, v in alt_forms.items() if v > 1}
    print(f"Форм на літеру в усіх налаштуваннях: {len(multi)} з {len(alt_forms)} літер мають >1:", multi)
    for t, r in pil_cmp.items():
        print(f"  Pillow «{t}»: без GSUB {r['no_gsub_features']}, по символу {r['per_char_doc_gen']}")


if __name__ == "__main__":
    main()
