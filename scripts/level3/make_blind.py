"""Крок 7: набір для сліпої оцінки рівня 3.

Збирає всі успішні зображення з LEVEL3_OUT/<модель>/, перемішує з фіксованим зерном і
копіює під анонімними номерами в LEVEL3_OUT/blind/. Оцінювач бачить лише номер, слово й
цільовий символ; модель і стиль — у ключі key.csv, який відкриваємо після оцінки.

Категорії: потрібна літера / інша літера / невпізнавано.

Запуск: python3 scripts/level3/make_blind.py
"""

import csv
import json
import os
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("LEVEL3_OUT", ROOT / "results" / "level3"))
BLIND = OUT / "blind"
SEED = 20261024
# Лише основні прогони; controls/ і *_512tokens/ (пробні запуски з іншими налаштуваннями) не входять
MODELS = ["ukr_diffusionpen", "diffusionpen", "emuru", "eruku", "vatr_extended"]


def main():
    rows = []
    for model_dir in (OUT / m for m in MODELS):
        log = model_dir / "log.jsonl"
        if not log.exists():
            continue
        for line in log.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["status"] == "ok" and (model_dir / r["file"]).exists():
                rows.append({**r, "model": model_dir.name, "path": model_dir / r["file"]})
    random.Random(SEED).shuffle(rows)
    (BLIND / "images").mkdir(parents=True, exist_ok=True)
    with open(BLIND / "rating.csv", "w", newline="", encoding="utf-8") as fr, \
         open(BLIND / "key.csv", "w", newline="", encoding="utf-8") as fk:
        rate, key = csv.writer(fr), csv.writer(fk)
        rate.writerow(["blind_id", "word", "target", "rating (потрібна / інша / невпізнавано)", "коментар"])
        key.writerow(["blind_id", "model", "unit", "entry_id", "style", "file"])
        for i, r in enumerate(rows, start=1):
            bid = f"B{i:04d}"
            shutil.copyfile(r["path"], BLIND / "images" / f"{bid}.png")
            rate.writerow([bid, r["word"], r["char"], "", ""])
            key.writerow([bid, r["model"], r["unit"], r["entry_id"], r["style"], r["file"]])
    models = sorted({r["model"] for r in rows})
    print(f"{len(rows)} зображень від {len(models)} моделей ({', '.join(models)}) → {BLIND}")
    print("Оцінюйте rating.csv; key.csv не відкривайте до кінця оцінки.")


if __name__ == "__main__":
    main()
