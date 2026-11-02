"""Крок 7: зведення сліпої оцінки рівня 3.

Читає заповнений бланк coding_kit/returned/оцінка_рівень3.xlsx, ключ
coding_kit/_key/blind_key.csv (номер → модель/одиниця/стиль; оцінювачеві під час роботи не
передавався), журнали генерації results/level3/drive/<модель>/log.jsonl (порожні результати
в сліпий набір не потрапили, але входять у знаменник) і level3/words.json з інвентарем.
Кожна модель має 428 одиниць (214 слів × 2 стилі); частки рахуються від 428.

Категорії: потрібна · інша · невпізнавано (оцінка) · порожньо (модель нічого не згенерувала).
Код 3 (3 клітинки без коментаря) прирівнюється до 0 («невпізнавано»), як у кроці 6.

Запуск: python3 scripts/coding/analyze_level3.py [бланк.xlsx]
Результат: results/level3/blind_summary.md, blind_rows.csv
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
KEY = ROOT / "coding_kit" / "_key" / "blind_key.csv"
WORDS = ROOT / "level3" / "words.json"
INVENTORY = ROOT / "inventory" / "charset_inventory.json"
LOGS = ROOT / "results" / "level3" / "drive"
OUT = ROOT / "results" / "level3"
CODES = {1: "потрібна", 2: "інша", 0: "невпізнавано", "E": "порожньо"}
NORMALIZE = {3: 0}
MODELS = {
    "ukr_diffusionpen": "Українська DiffusionPen", "vatr_extended": "VATr (розширений алфавіт)",
    "diffusionpen": "DiffusionPen (IAM)", "emuru": "Emuru", "eruku": "Eruku",
}


def subgroup(entry):
    """Група інвентарю для зведення: історичні діляться на основні, засвідчені й комбіновані."""
    if entry["group"] != "historical":
        return entry["group"]
    if entry["n_codepoints"] > 1:
        return "historical/combining"
    return f"historical/{entry['status']}"


SUBGROUPS = {"alphabet": "сучасний алфавіт (66)", "apostrophe": "апостроф (3 кодування)",
             "historical/core": "історичні основні: ы ъ ѣ ѳ ѵ", "historical/attested": "історичні засвідчені",
             "historical/combining": "комбіновані знаки: о̂ а́ а̀ …"}


def read_ratings(path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    out = {}
    for bid, _img, _word, _target, code, _comment in ws.iter_rows(min_row=2, values_only=True):
        if bid is None:
            continue
        code = NORMALIZE.get(code, code)
        if code not in (0, 1, 2):
            raise SystemExit(f"{bid}: код {code!r} поза схемою 0/1/2")
        out[bid] = code
    return out


def last_status(model):
    last = {}
    for line in (LOGS / model / "log.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        last[r["file"]] = r["status"]
    return last


def row(counter):
    n = sum(counter.values())
    return n, " | ".join(f"{counter[c] / n:.1%}" for c in CODES)


def main():
    rating_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "coding_kit" / "returned" / "оцінка_рівень3.xlsx"
    ratings = read_ratings(rating_path)
    key = {r["blind_id"]: r for r in csv.DictReader(open(KEY, encoding="utf-8"))}
    if set(ratings) != set(key):
        raise SystemExit(f"бланк і ключ не збігаються: {len(set(ratings) ^ set(key))} ID")
    units = {u["unit"]: u for u in json.loads(WORDS.read_text(encoding="utf-8"))["units"]}
    inventory = {e["id"]: e for e in json.loads(INVENTORY.read_text(encoding="utf-8"))["entries"]}
    by_file = {(k["model"], k["file"]): (bid, ratings[bid]) for bid, k in key.items()}

    rows = []  # одна на (модель, одиниця, стиль): 5 × 428
    for model in MODELS:
        for file, status in last_status(model).items():
            unit_id, style = file[:-4].rsplit("_s", 1)
            u = units[unit_id]
            if status == "ok":
                bid, code = by_file[(model, file)]
            elif status == "empty":
                bid, code = "", "E"
            else:
                raise SystemExit(f"{model}/{file}: статус {status}")
            rows.append({"model": model, "style": style, "unit": unit_id, "entry_id": u["entry_id"],
                         "char": u["char"], "subgroup": subgroup(inventory[u["entry_id"]]),
                         "word": u["word"], "blind_id": bid, "code": code})
    per_model = Counter(r["model"] for r in rows)
    assert all(n == 428 for n in per_model.values()), per_model
    assert sum(1 for r in rows if r["blind_id"]) == len(key)

    agg = defaultdict(Counter)
    for r in rows:
        agg[("model", r["model"])][r["code"]] += 1
        agg[("model×sub", r["model"], r["subgroup"])][r["code"]] += 1
        agg[("model×style", r["model"], r["style"])][r["code"]] += 1
        agg[("char", r["model"], r["char"])][r["code"]] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "blind_rows.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    head = "| " + " | ".join(CODES.values()) + " |"
    sep = "|---" * (len(CODES) + 2) + "|"
    lines = ["# Крок 7: сліпа оцінка рівня 3 — зведення", "",
             f"Кожна модель — 428 одиниць (214 слів × 2 стилі). Оцінено {len(key)} зображень; "
             f"{sum(1 for r in rows if r['code'] == 'E')} одиниць Emuru порожні (модель нічого не згенерувала) "
             "і рахуються окремою категорією. Один оцінювач; код 3 (3 клітинки) прирівняно до «невпізнавано».",
             "", "## За моделлю", "", "| Модель | n " + head, sep]
    for m, name in MODELS.items():
        n, cells = row(agg[("model", m)])
        lines.append(f"| {name} | {n} | {cells} |")

    lines += ["", "## Модель × група інвентарю", "", "| Модель | Група | n " + head, "|---" + sep]
    for m, name in MODELS.items():
        for sg, sg_name in SUBGROUPS.items():
            n, cells = row(agg[("model×sub", m, sg)])
            lines.append(f"| {name} | {sg_name} | {n} | {cells} |")

    lines += ["", "## Модель × стиль", "", "| Модель | Стиль | n " + head, "|---" + sep]
    for m, name in MODELS.items():
        for st in ("0000", "0002"):
            n, cells = row(agg[("model×style", m, st)])
            lines.append(f"| {name} | {st} | {n} | {cells} |")

    lines += ["", "## Символи без жодного «потрібна» (4 одиниці на символ)", "",
              "| Модель | Без влучання | Символи |", "|---|---|---|"]
    for m, name in MODELS.items():
        chars = {k[2]: c for k, c in agg.items() if k[0] == "char" and k[1] == m}
        zero = sorted(ch for ch, c in chars.items() if c[1] == 0)
        total = len(chars)
        listed = " ".join(zero) if len(zero) <= 45 else f"(майже всі; повний перелік — blind_rows.csv)"
        lines.append(f"| {name} | {len(zero)} з {total} | {listed} |")

    (OUT / "blind_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for m, name in MODELS.items():
        n, cells = row(agg[("model", m)])
        print(f"{name:28s} {cells}")
    print(f"→ {OUT / 'blind_summary.md'}\n→ {OUT / 'blind_rows.csv'}")


if __name__ == "__main__":
    main()
