"""Крок 8: матриця «вимога × метод/шрифт» (чернетка на погодження).

Джерела: results/level12/symbol_x_method.csv (рівні 1–2), results/level3/blind_rows.csv
(рівень 3), results/fonts/coverage.json і step6_coding.csv (шрифти, рівень 4),
checkpoints/training_data.json і versions/pinned.json (джерельні вимоги).

Стани клітинок (пропозиція, розд. «Чотири рівні»): так за конструкцією · можливе розширення
конфігурації · лише після перенавчання · неможливо без зміни методу · недостатньо даних ·
не перевірено. Правила призначення — RULES нижче; поріг рівня 3 — THRESHOLD.

Запуск: python3 scripts/build_matrix.py
Результат: results/matrix/matrix.md, matrix.csv (стан + доказ для кожної клітинки)
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "matrix"
FINAL6 = ROOT / "results" / "fonts" / "step6_final.csv"
THRESHOLD = 0.80  # частка «потрібна» на рівні 3, з якої вимогу вважаємо виконаною (погоджено 02.11.2026)

SHORT = {"так": "так", "розш": "розш.", "перенавч": "перенавч.", "метод": "зміна методу",
         "дані": "недост. даних", "не_перев": "не перев.", "ні": "ні", "na": "—"}

REQUIREMENTS = [  # (код, група, назва, підгрупа інвентарю або None)
    ("Г1", "графічні", "Сучасний алфавіт: 33 літери в обох регістрах (66)", "alphabet"),
    ("Г2", "графічні", "Форми 9 літер (т д и п ш г б в з) за прописами — рівень 4", None),
    ("Г3", "графічні", "Варіанти накреслень у контексті (OpenType)", None),
    ("П1", "правописні", "Апостроф: U+02BC, U+2019, U+0027", "apostrophe"),
    ("П2", "правописні", "Розділові знаки правопису 2019 (24)", "punctuation"),
    ("П3", "правописні", "Історичні літери, основні: ы ъ ѣ ѳ ѵ (10)", "historical/core"),
    ("П4", "правописні", "Історичні літери, засвідчені: ё э j ѯ ѱ ꙋ ѧ g (16)", "historical/attested"),
    ("П5", "правописні", "Комбіновані знаки: о̂ е̂ у̂ и̂ а́ а̀ (12)", "historical/combining"),
    ("Д1", "джерельні", "Навчальні дані checkpoint містять українське письмо", None),
    ("Д2", "джерельні", "Ваги опубліковано й можна зафіксувати версію", None),
    ("Д3", "джерельні", "Ліцензія дозволяє дослідницьке використання", None),
]

# Метод → (стовпці шляхів генерації, стовпці файлів гліфів) у symbol_x_method.csv; додаткові шляхи — у примітки
METHODS = {
    "GANwriting": ["GANwriting |"], "HiGAN+": ["HiGAN+ |"], "HWT": ["HWT |"],
    "VATr": ["VATr | generator.py", "VATr | mytext.txt"], "VATr++": ["VATr++ | generate.py"],
    "WordStylist": ["WordStylist |"], "One-DM": ["One-DM | test.py"], "DiffusionPen": ["DiffusionPen |"],
    "Українська DiffusionPen": ["Українська DiffusionPen | CanineTokenizer"],
    "Emuru": ["Emuru |"], "Eruku": ["Eruku | eruku"],
}
GLYPHS = {"VATr": "VATr | гліфи", "VATr++": "VATr++ | гліфи", "One-DM": "One-DM | гліфи"}
EXTRA_PATHS = {"Українська DiffusionPen": "Українська DiffusionPen | app.py"}
LEVEL3 = {"Українська DiffusionPen": "ukr_diffusionpen", "DiffusionPen": "diffusionpen",
          "Emuru": "emuru", "Eruku": "eruku", "VATr": "vatr_extended"}
WEIGHTS = {  # Д2: з manifest.json / training_data.json
    "GANwriting": ("ні", "ваги не опубліковано (README: навчити самостійно)"),
    "HiGAN+": ("так", "у репозиторії, зафіксовано комітом 5d37de7"),
    "HWT": ("так", "Google Drive, без ревізій"), "VATr": ("так", "Google Drive, без ревізій; SHA-256 vatr.pth записано"),
    "VATr++": ("так", "HF blowing-up-groundhogs/vatrpp, ревізія"), "WordStylist": ("так", "Google Drive, без ревізій"),
    "One-DM": ("так", "Google Drive / Baidu, без ревізій"), "DiffusionPen": ("так", "HF konnik/DiffusionPen, ревізія"),
    "Українська DiffusionPen": ("так", "HF kdonitz/diffusionpen-ukrainian, ревізія"),
    "Emuru": ("так", "HF, ревізія"), "Eruku": ("так", "HF, ревізія"),
}
LICENSES = {  # Д3: файли LICENSE у зафіксованих комітах і картки HF
    "GANwriting": ("так", "MIT"), "HiGAN+": ("так", "без файлу ліцензії; README: лише академічне використання"),
    "HWT": ("так", "MIT"), "VATr": ("так", "MIT"), "VATr++": ("ні", "код без ліцензії; ваги HF — MIT"),
    "WordStylist": ("так", "MIT; VAE SD 1.5 — OpenRAIL-M"), "One-DM": ("так", "MIT; VAE SD 1.5 — OpenRAIL-M"),
    "DiffusionPen": ("так", "MIT; VAE SD 1.5 — OpenRAIL-M"),
    "Українська DiffusionPen": ("ні", "ваги без ліцензії (картки немає); код Space — Apache-2.0"),
    "Emuru": ("так", "MIT"), "Eruku": ("так", "код MIT, ваги Apache-2.0"),
}
FONT_GROUPS = {  # стовпець → групи з font_list.json
    "Google Fonts": ["google_fonts", "google_fonts_classification"], "Kobzar KS": ["kobzar"],
    "ukrainian-handwriting-synth": ["ukrainian-handwriting-synth"], "doc_gen": ["doc_gen"],
}
PIPELINE = {  # втрати в коді інструмента синтетики (results/fonts/README.md, знахідки 3–4)
    "ukrainian-handwriting-synth": {
        "П1": "конвеєр відкидає рядки з ʼ і ’ (src/ukr_synth/config.py:27–32)",
        "П2": "конвеєр відкидає рядки з „ “ ” … (config.py:27–32)",
        "П3": "конвеєр відкидає рядки з історичними літерами (config.py:27–32)",
        "П4": "конвеєр відкидає рядки з історичними літерами (config.py:27–32)",
        "П5": "конвеєр відкидає рядки з комбінованими знаками (config.py:27–32)"},
    "doc_gen": {"П5": "рендеринг по одному символу: знак не позиціюється (document_generator.py:361)",
                "Г3": "рендеринг по одному символу: контекстні заміни не діють (document_generator.py:361)"},
}
FONT_LICENSE = {"Google Fonts": ("так", "SIL OFL"),
                "Kobzar KS": ("ні", "ліцензія «Київстар»: заборонено розбір, вбудовування в ПЗ, ШІ (п. 3.2)"),
                "ukrainian-handwriting-synth": ("дані", "ліцензій шрифтів не вказано; є комерційні гарнітури"),
                "doc_gen": ("дані", "ліцензій шрифтів не вказано; є «Free Trial»")}

RULES = [
    "Р1. Рівні 1–2 втрачають символи, файлу гліфів немає (закритий алфавіт, ембедінги класів) → лише після перенавчання.",
    "Р2. Рівні 1–2 втрачають символи, але файл гліфів їх містить → можливе розширення конфігурації.",
    f"Р3. Конфігурацію, що проходить рівні 1–2, перевірено на рівні 3: частка «потрібна» ≥ {THRESHOLD:.0%} → так за "
    "конструкцією, інакше → лише після перенавчання (кодує, але не малює). Діє й для розширеної конфігурації (VATr).",
    "Р4. Рівні 1–2 пройдено, рівень 3 не проводився (розділові знаки) → не перевірено.",
    "Р5. Втрата в коді конвеєра, яку не усунути конфігурацією (фільтр рядків, рендеринг по символу) → неможливо без зміни методу.",
    "Р6. Рівень 4 (форми за прописами) для методів → не перевірено (потрібен матеріал конкретної руки).",
    "Р7. Шрифти: стан групи «так», якщо вимогу виконують усі шрифти групи; інакше показано k/n і стан «так для k з n».",
    "Р8. Джерельні вимоги: так · ні · недостатньо даних (шість станів описують можливості, а не походження).",
]


def subgroup(e):
    if e["group"] != "historical":
        return e["group"]
    return "historical/combining" if e["n_codepoints"] > 1 else f"historical/{e['status']}"


def pick(header, prefix):
    cols = [i for i, h in enumerate(header) if h.startswith(prefix)]
    if not cols:
        raise SystemExit(f"немає стовпця {prefix!r}")
    return cols


def main():
    inventory = json.loads((ROOT / "inventory" / "charset_inventory.json").read_text(encoding="utf-8"))["entries"]
    ids_by_sg = defaultdict(list)
    for e in inventory:
        ids_by_sg[subgroup(e)].append(e["id"])

    rows = list(csv.reader(open(ROOT / "results" / "level12" / "symbol_x_method.csv", encoding="utf-8")))
    header, l12 = rows[0], {r[0]: r for r in rows[1:]}
    blind = list(csv.DictReader(open(ROOT / "results" / "level3" / "blind_rows.csv", encoding="utf-8")))
    l3 = defaultdict(Counter)
    for r in blind:
        l3[(r["model"], r["subgroup"])][r["code"]] += 1
    training = {m["method"]: m for m in json.loads((ROOT / "checkpoints" / "training_data.json").read_text(encoding="utf-8"))["methods"]}

    cells = {}  # (req, column) → (стан, доказ)

    for method, prefixes in METHODS.items():
        gen = [c for p in prefixes for c in pick(header, p)]
        glyph = pick(header, GLYPHS[method]) if method in GLYPHS else []
        extra = pick(header, EXTRA_PATHS[method]) if method in EXTRA_PATHS else []
        for code, _g, _name, sg in REQUIREMENTS:
            if sg is None:
                continue
            ids = ids_by_sg[sg]
            ok = [i for i in ids if all(l12[i][c] == "ok" for c in gen)]
            where = Counter(l12[i][c].split(" @ ")[-1] for i in ids for c in gen if l12[i][c] != "ok")
            ev = f"р.1–2: {len(ok)}/{len(ids)}" + (f" ({where.most_common(1)[0][0]})" if where else "")
            if extra:
                lost = [i for i in ids if l12[i][extra[0]] != "ok"]
                if lost:
                    ev += f"; застосунок Space: втрачено {len(lost)} ({l12[lost[0]][extra[0]].split(' @ ')[-1]})"
            glyph_ok = bool(glyph) and all(l12[i][c] == "ok" for i in ids for c in glyph)
            c3 = l3.get((LEVEL3.get(method), sg))
            if c3 and sg != "punctuation":
                share = c3["1"] / sum(c3.values())
                ev += f"; р.3: {share:.1%} «потрібна» (n={sum(c3.values())})"
                if len(ok) < len(ids):
                    ev += "; р.3 — з розширеним алфавітом"
                state = "так" if share >= THRESHOLD else "перенавч"
            elif len(ok) == len(ids):
                state = "не_перев"
                ev += "; р.3 не проводився"
            elif glyph_ok:
                state, ev = "розш", ev + "; гліфи є для всіх"
            else:
                state = "перенавч"
            cells[(code, method)] = (state, ev)
        cells[("Г2", method)] = ("не_перев", "рівень 4 для методів не перевіряється")
        cells[("Г3", method)] = ("na", "не застосовно")
        lang = training[method]["language"]
        cells[("Д1", method)] = ("так", lang) if "україн" in lang else ("ні", lang)
        cells[("Д2", method)] = WEIGHTS[method]
        cells[("Д3", method)] = LICENSES[method]

    fonts = json.loads((ROOT / "results" / "fonts" / "coverage.json").read_text(encoding="utf-8"))["fonts"]
    if FINAL6.exists():  # підсумкове кодування після консенсусу (scripts/coding/finalize_step6.py)
        step6 = list(csv.DictReader(open(FINAL6, encoding="utf-8")))
        coders = ["підсумок"]
    else:
        step6 = list(csv.DictReader(open(ROOT / "results" / "fonts" / "step6_coding.csv", encoding="utf-8")))
        coders = [k for k in step6[0] if k not in ("id", "font_id", "font", "group", "letter", "збіг")]
    for col, groups in FONT_GROUPS.items():
        members = [f for f in fonts.values() if f["font"]["group"] in groups]
        n = len(members)
        for code, _g, _name, sg in REQUIREMENTS:
            if sg is None:
                continue
            k = sum(all(f["entries"][i]["status"] == "ok" for i in ids_by_sg[sg]) for f in members)
            per_font = [sum(f["entries"][i]["status"] == "ok" for i in ids_by_sg[sg]) for f in members]
            ev = (f"шрифтів з усіма символами: {k}/{n}; символів на шрифт: "
                  f"{min(per_font)}–{max(per_font)} з {len(ids_by_sg[sg])}")
            state = "так" if k == n else ("ні" if k == 0 else "так")
            label = None if k in (0, n) else f"так для {k} з {n}"
            if code in PIPELINE.get(col, {}):
                state, label = "метод", None
                ev += "; " + PIPELINE[col][code]
            cells[(code, col)] = (state, ev, label) if label else (state, ev)
        rows6 = [r for r in step6 if r["group"] in groups]
        shares = [sum(r[c] == "1" for r in rows6) / len(rows6) for c in coders]
        by_font6 = defaultdict(list)
        for r in rows6:
            by_font6[r["font_id"]].append(r)
        full = [sum(all(r[c] == "1" for r in rs) for rs in by_font6.values()) for c in coders]
        label = " / ".join(f"{k} з {n}" for k in full) if len(set(full)) > 1 else (
            "так" if full[0] == n else ("ні" if full[0] == 0 else f"так для {full[0]} з {n}"))
        cells[("Г2", col)] = ("так" if min(full) == n else "ні",
                              "шрифтів з усіма 9 літерами «відповідає»: " + ", ".join(
                                  f"{c} {k}/{n}" for c, k in zip(coders, full))
                              + "; частка «відповідає»: " + ", ".join(f"{c} {s:.0%}" for c, s in zip(coders, shares))
                              + ("" if FINAL6.exists() else "; консенсус не проведено"), label)
        if col == "Kobzar KS":
            cells[("Г3", col)] = ("розш", "32 з 66 літер мають 2–4 форми, лише через salt/ss01/ss03/init/fina")
        elif col in PIPELINE and "Г3" in PIPELINE[col]:
            cells[("Г3", col)] = ("метод", PIPELINE[col]["Г3"])
        else:
            cells[("Г3", col)] = ("не_перев", "OpenType-варіанти перевірено лише для Kobzar KS")
        cells[("Д1", col)] = ("na", "не застосовно")
        cells[("Д2", col)] = ("так", "зафіксовано комітом / SHA-256")
        cells[("Д3", col)] = FONT_LICENSE[col]

    columns = list(METHODS) + list(FONT_GROUPS)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "matrix.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["код", "група", "вимога", "стовпець", "стан", "доказ"])
        for code, g, name, _sg in REQUIREMENTS:
            for col in columns:
                cell = cells[(code, col)]
                w.writerow([code, g, name, col, cell[2] if len(cell) > 2 else SHORT[cell[0]], cell[1]])

    def show(cell):
        return cell[2] if len(cell) > 2 else SHORT[cell[0]]

    lines = ["# Крок 8: матриця «вимога × метод/шрифт»", "",
             f"Погоджено 02.11.2026: перелік вимог (11), поріг рівня 3 — {THRESHOLD:.0%}, правила Р1–Р8. "
             + ("Г2 для шрифтів — за підсумковим кодуванням (консенсус)." if FINAL6.exists()
                else "Г2 для шрифтів — два кодувальники окремо; консенсус ще не проведено."), "",
             "Стани: **так** — так за конструкцією · **розш.** — можливе розширення конфігурації · "
             "**перенавч.** — лише після перенавчання · **зміна методу** — неможливо без зміни методу · "
             "**недост. даних** · **не перев.** — не перевірено · **—** не застосовно. Докази — matrix.csv.", "",
             "## Методи", "", "| Вимога | " + " | ".join(METHODS) + " |", "|---" * (len(METHODS) + 1) + "|"]
    for code, _g, name, _sg in REQUIREMENTS:
        lines.append(f"| {code} {name} | " + " | ".join(show(cells[(code, m)]) for m in METHODS) + " |")
    lines += ["", "## Шрифти й інструменти синтетики", "",
              "| Вимога | " + " | ".join(FONT_GROUPS) + " |", "|---" * (len(FONT_GROUPS) + 1) + "|"]
    for code, _g, name, _sg in REQUIREMENTS:
        lines.append(f"| {code} {name} | " + " | ".join(show(cells[(code, c)]) for c in FONT_GROUPS) + " |")
    lines += ["", "## Правила призначення станів", ""] + [f"- {r}" for r in RULES]
    (OUT / "matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
