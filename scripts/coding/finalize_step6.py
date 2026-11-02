"""Крок 6: підсумкове кодування форм 9 літер.

Де кодувальники збіглися — їхній код; де розійшлися — код зі стовпця «Консенсус»
заповненого бланка coding_kit/returned/консенсус_форм.xlsx. Результат —
results/fonts/step6_final.csv, який бере build_matrix.py для вимоги Г2.

Запуск: python3 scripts/coding/finalize_step6.py [консенсус_форм.xlsx]
"""

import csv
import sys
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
CODING = ROOT / "results" / "fonts" / "step6_coding.csv"
OUT = ROOT / "results" / "fonts" / "step6_final.csv"


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "coding_kit" / "returned" / "консенсус_форм.xlsx"
    ws = openpyxl.load_workbook(path, data_only=True).active
    header = [c.value for c in ws[1]]
    col = next(i for i, h in enumerate(header) if h and str(h).startswith("Консенсус"))
    consensus = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        code = r[col]
        if code not in (0, 1, 2):
            raise SystemExit(f"{r[0]}: консенсус {code!r} поза схемою 0/1/2")
        consensus[r[0]] = str(code)

    rows = list(csv.DictReader(open(CODING, encoding="utf-8")))
    coders = [k for k in rows[0] if k not in ("id", "font_id", "font", "group", "letter", "збіг")]
    disagree = {r["id"] for r in rows if r["збіг"] == "ні"}
    if disagree != set(consensus):
        raise SystemExit(f"бланк консенсусу не збігається з розбіжностями: бракує {sorted(disagree - set(consensus))[:10]}, "
                         f"зайві {sorted(set(consensus) - disagree)[:10]}")

    out, source = [], Counter()
    for r in rows:
        if r["id"] in consensus:
            final, src = consensus[r["id"]], "консенсус"
        else:
            final, src = r[coders[0]], "збіг"
        source[src] += 1
        out.append({k: r[k] for k in ("id", "font_id", "font", "group", "letter")} | {"підсумок": final, "джерело": src})
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    moved = Counter((r[coders[0]], consensus[r["id"]]) for r in rows if r["id"] in consensus)
    print(f"{len(out)} рядків → {OUT}; {dict(source)}")
    print(f"консенсус збігся з {coders[0]}: {sum(r[coders[0]] == consensus[r['id']] for r in rows if r['id'] in consensus)}, "
          f"з {coders[1]}: {sum(r[coders[1]] == consensus[r['id']] for r in rows if r['id'] in consensus)} з {len(consensus)}")


if __name__ == "__main__":
    main()
