"""Крок 5: збирає перелік шрифтів для аудиту → results/fonts/font_list.json.

Джерела (усі на зафіксованих версіях, versions/pinned.json):
- Google Fonts: відбір select_fonts.py (рукописні з кирилицею + Shantell Sans), по одному файлу на сімейство;
- Kobzar KS: архів з Wayback Machine, звірка SHA-256 (файл не поширюємо);
- шрифти інструментів синтетики: ukrainian-handwriting-synth (fonts/) і doc_gen (корінь).

Спершу: python3 scripts/fonts/select_fonts.py і python3 scripts/level12/fetch_sources.py
Запуск: python3 scripts/fonts/fetch_fonts.py
"""

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "level12"))
from common import REPOS, WORK  # noqa: E402

PINNED = json.loads((ROOT / "versions" / "pinned.json").read_text(encoding="utf-8"))
SELECTION = ROOT / "results" / "fonts" / "selection.json"
OUT = ROOT / "results" / "fonts" / "font_list.json"
FONT_EXT = (".ttf", ".otf", ".TTF", ".OTF")


def pick_file(paths):
    """Один файл на сімейство: змінний шрифт (типовий екземпляр) або Regular, інакше перший."""
    for key in ("[", "-Regular", "Regular"):
        for p in paths:
            if key in Path(p).name and "Italic" not in Path(p).name:
                return p
    return sorted(paths)[0]


def google_fonts():
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    rows = []
    for fam in sel["selected"]:
        path = pick_file(fam["paths"])
        rows.append({"name": fam["family"], "source": "google_fonts",
                     "group": "google_fonts" if fam["family"] in sel["handwriting_cyrillic"] else "google_fonts_classification",
                     "path": str((REPOS / "google-fonts" / path).relative_to(WORK)), "license": fam["license_dir"].upper(),
                     "ref": f"google/fonts@{sel['google_fonts_commit'][:12]}:{path}"})
    return rows


def kobzar():
    ext = next(e for e in PINNED["external"] if e["name"] == "Kobzar KS")
    dest = WORK / "kobzar" / ext["file"]
    if not dest.exists():
        data = urllib.request.urlopen(ext["url"], timeout=120).read()
        if hashlib.sha256(data).hexdigest() != ext["sha256_zip"]:
            raise RuntimeError("Kobzar KS: SHA-256 архіву не збігається")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(zipfile.ZipFile(io.BytesIO(data)).read(ext["file"]))
    if hashlib.sha256(dest.read_bytes()).hexdigest() != ext["sha256_file"]:
        raise RuntimeError("Kobzar KS: SHA-256 файлу не збігається")
    return [{"name": "Kobzar KS", "source": "kobzar", "group": "kobzar", "path": str(dest.relative_to(WORK)),
             "license": "Київстар (безоплатна, з обмеженнями)", "ref": f"Wayback 2015-01-23: {ext['file']}"}]


def tool_fonts(repo_slug, subdir, tool):
    root = REPOS / repo_slug / subdir
    sha = next(g["commit"] for g in PINNED["git"] if g["name"] == tool)
    return [{"name": p.stem, "source": tool, "group": tool, "path": str(p.relative_to(WORK)), "license": "не вказано",
             "ref": f"{tool}@{sha[:12]}:{p.relative_to(REPOS / repo_slug)}"}
            for p in sorted(root.iterdir()) if p.suffix in FONT_EXT]


def main():
    fonts = (google_fonts() + kobzar()
             + tool_fonts("ukrainian-handwriting-synth", "fonts", "ukrainian-handwriting-synth")
             + tool_fonts("doc-gen", ".", "doc_gen"))
    for i, f in enumerate(fonts, start=1):
        f["id"] = f"F{i:03d}"
        f["sha256"] = hashlib.sha256((WORK / f["path"]).read_bytes()).hexdigest()
    OUT.write_text(json.dumps({"fonts": fonts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    groups = {}
    for f in fonts:
        groups[f["group"]] = groups.get(f["group"], 0) + 1
    print(f"{OUT.relative_to(ROOT)}: {len(fonts)} шрифтів", groups)


if __name__ == "__main__":
    main()
