"""Крок 7: контроль для Emuru й Eruku — чи справна обгортка, якщо модель провалює кирилицю.

Той самий виклик, що в run_level3.py, у трьох умовах:
- наші стилі (кириличні зразки з кириличною транскрипцією) × латинський і кириличний gen_text;
- для Eruku ще й без транскрипції стилю (style_text необов'язковий, картка моделі);
- зразок стилю з картки Emuru (sample.png, транскрипція 'THE JOLLY IS "U"') × приклад із картки
  ('EMURU'), латиниця й кирилиця — перевіряє середовище й відокремлює вплив кириличного стилю
  від впливу кириличного gen_text.
Уже зроблені випадки (за controls.jsonl) не повторюються.

Запуск: python3 scripts/level3/control_latin.py <emuru|eruku>
Результат: LEVEL3_OUT/controls/<модель>/*.png і controls.jsonl
"""

import json
import os
import shutil
import sys
import time
import zlib
from pathlib import Path

import torch

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from generators import LOADERS, ROOT, hf  # noqa: E402

OUT = Path(os.environ.get("LEVEL3_OUT", ROOT / "results" / "level3")) / "controls"
CARD_STYLE_TEXT = 'THE JOLLY IS "U"'  # картка blowing-up-groundhogs/emuru, приклад використання
CASES = [  # (назва, gen_text, чи передавати транскрипцію стилю, стилі: ours | card)
    ("latin_mama", "mama", True, "ours"),
    ("latin_hello", "hello", True, "ours"),
    ("cyr_mama", "мама", True, "ours"),
    ("card_EMURU", "EMURU", True, "card"),
    ("card_latin_mama", "mama", True, "card"),
    ("card_cyr_mama", "мама", True, "card"),
]
CASES_ERUKU_EXTRA = [
    ("latin_mama_nostyletext", "mama", False, "ours"),
    ("cyr_mama_nostyletext", "мама", False, "ours"),
]


def card_style():
    sdir = OUT / "card_style"
    if not (sdir / "line.png").exists():
        sdir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(hf("blowing-up-groundhogs/emuru", "sample.png"), sdir / "line.png")
    return {"id": "card", "dir": sdir, "transcription": CARD_STYLE_TEXT}


def main():
    model = sys.argv[1]
    meta = json.loads((ROOT / "level3" / "styles" / "styles.json").read_text(encoding="utf-8"))
    ours = [{"id": k, "dir": ROOT / "level3" / "styles" / k, **v} for k, v in meta["styles"].items()]
    out = OUT / model
    out.mkdir(parents=True, exist_ok=True)
    log = out / "controls.jsonl"
    done = {(r["case"], r["style"]) for r in map(json.loads, log.read_text(encoding="utf-8").splitlines())} \
        if log.exists() else set()
    cases = CASES + (CASES_ERUKU_EXTRA if model == "eruku" else [])
    todo = [(c, s) for c in cases for s in (ours if c[3] == "ours" else [card_style()]) if (c[0], s["id"]) not in done]
    if not todo:
        print(f"{model}: усі контрольні випадки вже зроблено")
        return
    generate, info = LOADERS[model]()
    for (name, text, with_style_text, _), style in todo:
        st = style if with_style_text else {**style, "transcription": ""}
        torch.manual_seed(zlib.crc32(f"{model}|{name}|{style['id']}".encode()))
        t0 = time.time()
        img = generate(text, st)
        row = {"case": name, "text": text, "style": style["id"], "style_text": st["transcription"],
               "size": list(img.size), "seconds": round(time.time() - t0, 1)}
        if min(img.size) > 0:
            img.save(out / f"{name}_s{style['id']}.png")
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(row, flush=True)


if __name__ == "__main__":
    main()
