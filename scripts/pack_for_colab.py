"""Пакує проєкт (без .venv, work/ і кешів) у ukr-htg-audit.zip для Google Drive.

Запуск: python3 scripts/pack_for_colab.py → ../ukr-htg-audit.zip
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".venv", "work", "__pycache__", ".git"}
OUT = ROOT.parent / "ukr-htg-audit.zip"

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    n = 0
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if p.is_file() and not SKIP.intersection(rel.parts):
            z.write(p, Path("ukr-htg-audit") / rel)
            n += 1
print(f"{OUT}: {n} файлів, {OUT.stat().st_size / 2**20:.1f} МБ")
