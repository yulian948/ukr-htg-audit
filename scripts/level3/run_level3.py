"""Крок 7: рівень 3 — генерація слів інвентарю моделями з відкритими вагами.

Кожне слово з level3/words.json (по 2 на символ) — у 2 стилях (level3/styles/). Зображення
й журнал пишуться в LEVEL3_OUT (у Colab — тека на Google Drive), тож перерваний запуск
продовжується з місця зупинки. Модель, що не завантажилась, отримує статус «не перевірено».
Статуси зображень у log.jsonl: ok | empty (модель нічого не згенерувала) | error.

Запуск: python3 scripts/level3/run_level3.py <модель> [--limit N]
Моделі: ukr_diffusionpen, diffusionpen, emuru, eruku, vatr_extended, all

Віддалений код Emuru й Eruku (trust_remote_code) не сумісний із transformers 5.x, тому їх
запускаємо з окремих середовищ із версіями з requirements.txt їхніх репозиторіїв
(у Colab — /content/venv_emuru і /content/venv_eruku, див. блокнот).
"""

import argparse
import json
import os
import random
import sys
import time
import traceback
import zlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

# Завантаження через xet іноді обривається («CAS Client Error»); звичайне HTTP — надійніше
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from generators import DEVICE, LOADERS, ROOT  # noqa: E402

OUT = Path(os.environ.get("LEVEL3_OUT", ROOT / "results" / "level3"))


def seed_for(model, unit, style):
    s = zlib.crc32(f"{model}|{unit}|{style}".encode())
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    return s


def run(model, limit=None):
    words = json.loads((ROOT / "level3" / "words.json").read_text(encoding="utf-8"))["units"]
    meta = json.loads((ROOT / "level3" / "styles" / "styles.json").read_text(encoding="utf-8"))
    styles = [{"id": k, "dir": ROOT / "level3" / "styles" / k, **v} for k, v in meta["styles"].items()]
    out = OUT / model
    out.mkdir(parents=True, exist_ok=True)
    log = out / "log.jsonl"
    info_path = out / "model_info.json"
    jobs = [(u, s) for u in words for s in styles][:limit]

    try:
        loader = LOADERS[model]
        extra = "".join(u["word"] for u in words)
        generate, info = loader(extra) if model == "vatr_extended" else loader()
    except Exception as exc:  # noqa: BLE001 — «не перевірено» теж результат
        info_path.write_text(json.dumps({"model": model, "status": "не перевірено",
                                         "error": f"{type(exc).__name__}: {exc}",
                                         "traceback": traceback.format_exc()[-3000:]}, ensure_ascii=False, indent=1))
        print(f"{model}: модель не завантажилась — не перевірено ({type(exc).__name__}: {exc})")
        return
    import diffusers
    import transformers
    info.update(model=model, status="loaded", device=DEVICE, torch=torch.__version__,
                transformers=transformers.__version__, diffusers=diffusers.__version__, python=sys.executable,
                started=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")

    # Порожній результат не має файлу; з тим самим зерном він повториться, тож не генеруємо його вдруге
    empty = {r["file"] for r in map(json.loads, log.read_text(encoding="utf-8").splitlines())
             if r["status"] == "empty"} if log.exists() else set()
    done = ok = 0
    for unit, style in jobs:
        path = out / f"{unit['unit']}_s{style['id']}.png"
        if path.exists() or path.name in empty:
            continue
        seed = seed_for(model, unit["unit"], style["id"])
        t0 = time.time()
        row = {"unit": unit["unit"], "entry_id": unit["entry_id"], "char": unit["char"], "word": unit["word"],
               "style": style["id"], "seed": seed, "file": path.name}
        try:
            img = generate(unit["word"], style)
            if min(img.size) == 0:  # модель одразу завершила генерацію (Emuru: зріз після зразка стилю порожній)
                row["status"] = "empty"
            else:
                img.save(path)
                row["status"] = "ok"
                ok += 1
        except Exception as exc:  # noqa: BLE001
            row.update(status="error", error=f"{type(exc).__name__}: {exc}"[:300])
        row["seconds"] = round(time.time() - t0, 2)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        done += 1
        if done % 20 == 0 or done == 1:
            print(f"{model}: {done}/{len(jobs)} ({row['seconds']} с/зобр.)", flush=True)
    print(f"{model}: готово, нових {done}, успішних {ok}; тека {out}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("model", choices=[*LOADERS, "all"])
    p.add_argument("--limit", type=int, default=None, help="лише перші N зображень (перевірка)")
    a = p.parse_args()
    for m in (LOADERS if a.model == "all" else [a.model]):
        run(m, a.limit)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
