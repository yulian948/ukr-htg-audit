"""Крок 6: зведення двох незалежних кодувань форм 9 літер.

Читає два заповнені бланки з coding_kit/returned/, зіставляє з ключем
coding_kit/_key/step6_key.csv (шрифт, група, літера — не передавався кодувальникам),
рахує каппу Коена, відсоток збігу, таблицю спряженості й розбіжності за шрифтом/літерою.

Код 3 («зовсім інший знак/малюнок», використаний одним кодувальником) нормалізується до 0
(«невизначено») — це підкатегорія 0 за інструкцією (coding_kit/step6/ІНСТРУКЦІЯ.txt).

Запуск: python3 scripts/coding/analyze_step6.py <файл1.xlsx> <файл2.xlsx>
Результат: results/fonts/step6_agreement.md, step6_coding.csv
"""

import csv
import sys
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
KEY = ROOT / "coding_kit" / "_key" / "step6_key.csv"
OUT = ROOT / "results" / "fonts"
LABELS = {0: "невизначено", 1: "відповідає", 2: "відмінна"}
NORMALIZE = {3: 0}  # «зовсім інший знак» → підкатегорія «невизначено»


def read_coding(path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        rid, _img, _letter, code, comment = row
        if rid is None:
            continue
        if code is None:
            raise SystemExit(f"{path}: {rid} без коду")
        code = NORMALIZE.get(code, code)
        if code not in LABELS:
            raise SystemExit(f"{path}: {rid} код {code} поза схемою 0/1/2")
        out[rid] = {"code": code, "comment": comment}
    return out


def cohens_kappa(a, b, labels):
    n = len(a)
    po = sum(a[i] == b[i] for i in range(n)) / n
    pa = Counter(a)
    pb = Counter(b)
    pe = sum((pa[l] / n) * (pb[l] / n) for l in labels)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return po, pe, kappa


def confusion(a, b, labels):
    m = {l1: {l2: 0 for l2 in labels} for l1 in labels}
    for x, y in zip(a, b):
        m[x][y] += 1
    return m


def main():
    f1, f2 = Path(sys.argv[1]), Path(sys.argv[2])
    name1, name2 = f1.stem.replace("кодування_форм_", ""), f2.stem.replace("кодування_форм_", "")
    c1, c2 = read_coding(f1), read_coding(f2)
    key = {r["id"]: r for r in csv.DictReader(open(KEY, encoding="utf-8"))}

    ids = sorted(set(c1) & set(c2), key=lambda i: int(i[1:]))
    missing = (set(key) - set(c1)) | (set(key) - set(c2))
    if missing:
        print(f"Увага: {len(missing)} ID відсутні в одному з файлів: {sorted(missing)[:10]}")

    a = [c1[i]["code"] for i in ids]
    b = [c2[i]["code"] for i in ids]
    po, pe, kappa = cohens_kappa(a, b, [0, 1, 2])
    conf = confusion(a, b, [0, 1, 2])

    # Розбіжності за шрифтом
    disagree = [i for i in ids if c1[i]["code"] != c2[i]["code"]]
    by_font = Counter(key[i]["font"] for i in disagree)
    by_letter = Counter(key[i]["letter"] for i in disagree)
    by_group = Counter(key[i]["group"] for i in disagree)
    group_totals = Counter(key[i]["group"] for i in ids)

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "step6_coding.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "font_id", "font", "group", "letter", name1, name2, "збіг"])
        for i in ids:
            w.writerow([i, key[i]["font_id"], key[i]["font"], key[i]["group"], key[i]["letter"],
                       c1[i]["code"], c2[i]["code"], "так" if c1[i]["code"] == c2[i]["code"] else "ні"])

    lines = [
        "# Крок 6: надійність кодування форм 9 літер",
        "",
        f"Кодувальники: **{name1}** і **{name2}**, незалежно, на повному наборі 531 зображення "
        "(9 літер × 59 шрифтів). Код 3 («зовсім інший знак/малюнок») прирівняно до 0 («невизначено») "
        "за інструкцією.",
        "",
        f"- Відсоток збігу (po): **{po:.3f}**",
        f"- Очікуваний збіг за випадковості (pe): {pe:.3f}",
        f"- Каппа Коена: **{kappa:.3f}**",
        f"- Розбіжностей: {len(disagree)} з {len(ids)} ({len(disagree) / len(ids):.1%})",
        "",
        "## Таблиця спряженості",
        "",
        "| " + name1 + " \\ " + name2 + " | " + " | ".join(LABELS[l] for l in (0, 1, 2)) + " |",
        "|---|---|---|---|",
    ]
    for l1 in (0, 1, 2):
        lines.append(f"| {LABELS[l1]} | " + " | ".join(str(conf[l1][l2]) for l2 in (0, 1, 2)) + " |")

    lines += ["", "## Розбіжності за групою шрифтів", "",
             "| Група | Розбіжностей | Усього | Частка |", "|---|---|---|---|"]
    for g, total in sorted(group_totals.items(), key=lambda x: -by_group.get(x[0], 0)):
        lines.append(f"| {g} | {by_group.get(g, 0)} | {total} | {by_group.get(g, 0) / total:.1%} |")

    lines += ["", "## Розбіжності за літерою", "", "| Літера | Розбіжностей |", "|---|---|"]
    for ch, n in sorted(by_letter.items(), key=lambda x: -x[1]):
        lines.append(f"| {ch} | {n} |")

    lines += ["", "## Розбіжності за шрифтом (топ-15)", "", "| Шрифт | Розбіжностей |", "|---|---|"]
    for f, n in by_font.most_common(15):
        lines.append(f"| {f} | {n} |")

    (OUT / "step6_agreement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"po={po:.3f}  pe={pe:.3f}  kappa={kappa:.3f}  розбіжностей {len(disagree)}/{len(ids)}")
    print(f"→ {OUT / 'step6_agreement.md'}")
    print(f"→ {OUT / 'step6_coding.csv'}")


if __name__ == "__main__":
    main()
