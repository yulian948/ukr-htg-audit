"""Крок 7: два спільні стилі для всіх моделей → level3/styles/.

Джерело — стильові зразки Space української DiffusionPen (UkrHandwritten): автори 0000 і 0002,
по 5 зображень слів. Транскрипції прочитано вручну. Для кожного стилю зберігаємо:
- words/*.png — окремі слова (DiffusionPen, українська DiffusionPen);
- vatr15/*.png — ті самі 5 слів, кожне тричі: VATr бере рівно 15 зразків без повторень;
- line.png + transcription — слова, складені в рядок (Emuru, Eruku).

Запуск: python3 scripts/level3/prepare_styles.py
"""

import json
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "level3" / "styles"
PINNED = json.loads((ROOT / "versions" / "pinned.json").read_text(encoding="utf-8"))
SPACE = next(h for h in PINNED["huggingface"]
             if h["id"] == "kdonitz/diffusionpen-ukrainian" and h["kind"] == "space")

# Транскрипції в порядку імен файлів (переглянуто вручну)
STYLES = {
    "0000": ["був", "Трохи", "але", "й", "принципів"],
    "0002": ["правописам", "у", "за", "потяга", "їх"],
}


def writer_index(writer):
    """Індекс автора в app.py: позиція в упорядкованому списку тек style_refs/ (308 авторів)."""
    dirs = SPACE.get("style_ref_dirs") or sorted(  # скорочений pinned_colab.json має готовий список
        {f["path"].split("/")[1] for f in SPACE["files"] if f["path"].startswith("style_refs/")})
    return dirs.index(writer), len(dirs)


def fetch(path, dest):
    if not dest.exists():
        url = f"https://huggingface.co/spaces/{SPACE['id']}/resolve/{SPACE['sha']}/{path}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(urllib.request.urlopen(url, timeout=60).read())


def make_line(images, gap=24, height=64):
    scaled = [im.resize((max(1, im.width * height // im.height), height)) for im in images]
    line = Image.new("L", (sum(i.width for i in scaled) + gap * (len(scaled) + 1), height), 255)
    x = gap
    for im in scaled:
        line.paste(im, (x, 0))
        x += im.width + gap
    return line


def main():
    meta = {"source": f"hf space {SPACE['id']}@{SPACE['sha']}: style_refs/", "styles": {}}
    for writer, words in STYLES.items():
        files = sorted(f["path"] for f in SPACE["files"] if f["path"].startswith(f"style_refs/{writer}/"))
        if len(files) != len(words):
            sys.exit(f"автор {writer}: {len(files)} файлів, а транскрипцій {len(words)}")
        wdir = OUT / writer
        images = []
        for i, path in enumerate(files):
            dest = wdir / "words" / f"{i}.png"
            fetch(path, dest)
            images.append(Image.open(dest).convert("L"))
            for k in range(3):
                (wdir / "vatr15").mkdir(parents=True, exist_ok=True)
                shutil.copyfile(dest, wdir / "vatr15" / f"{i}_{k}.png")
        make_line(images).save(wdir / "line.png")
        idx, n = writer_index(writer)
        meta["styles"][writer] = {"files": files, "words": words, "transcription": " ".join(words),
                                  "ukr_writer_index": idx, "ukr_num_writers": n}
        print(f"стиль {writer}: {len(files)} слів, індекс автора {idx}/{n}, рядок «{' '.join(words)}»")
    (OUT / "styles.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
