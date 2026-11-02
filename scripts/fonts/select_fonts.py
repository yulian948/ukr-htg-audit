"""Крок 5а: відбір рукописних шрифтів Google Fonts з кирилицею на зафіксованому коміті.

Критерій пропозиції: category = HANDWRITING і subsets містить cyrillic; окремо — сімейства,
у яких HANDWRITING є лише в полі classifications. Завантажує з google/fonts тільки
METADATA.pb (sparse checkout), а потім — файли шрифтів відібраних сімейств.

Запуск: python3 scripts/fonts/select_fonts.py
Результат: results/fonts/selection.json
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "level12"))
from common import WORK, pinned  # noqa: E402

GF = WORK / "repos" / "google-fonts"
OUT = ROOT / "results" / "fonts" / "selection.json"


def git(*args):
    subprocess.run(["git", "-C", GF, *args], check=True, capture_output=True)


def sparse_checkout(patterns):
    sha = pinned("google/fonts")["commit"]
    GF.mkdir(parents=True, exist_ok=True)
    if not (GF / ".git").exists():
        git("init", "-q")
        git("remote", "add", "origin", "https://github.com/google/fonts.git")
    git("sparse-checkout", "set", "--no-cone", *patterns)
    git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", sha)
    git("-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD")
    return sha


def parse_metadata(path):
    text = path.read_text(encoding="utf-8")
    field = lambda name: re.findall(rf'^{name}: "([^"]*)"', text, flags=re.M)
    fonts = re.findall(r'^\s*filename: "([^"]+)"', text, flags=re.M)
    return {
        "family": (field("name") or [path.parent.name])[0],
        "dir": str(path.parent.relative_to(GF)),
        "license_dir": path.parent.parent.name,
        "category": field("category"),
        "classifications": field("classifications"),
        "subsets": field("subsets"),
        "files": fonts,
    }


def main():
    meta_patterns = ["/*/*/METADATA.pb"]
    sha = sparse_checkout(meta_patterns)
    families = [parse_metadata(p) for p in sorted(GF.glob("*/*/METADATA.pb"))]
    hw_category = [f for f in families if "HANDWRITING" in f["category"]]
    hw_cyr = [f for f in hw_category if "cyrillic" in f["subsets"]]
    hw_class_only = [f for f in families if "HANDWRITING" in f["classifications"]
                     and "HANDWRITING" not in f["category"] and "cyrillic" in f["subsets"]]
    selected = hw_cyr + hw_class_only

    # Завантажуємо файли шрифтів лише відібраних сімейств
    sparse_checkout(meta_patterns + [f"/{f['dir']}/*" for f in selected])
    for f in selected:
        f["paths"] = [str(Path(f["dir"]) / name) for name in f["files"] if (GF / f["dir"] / name).exists()]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "google_fonts_commit": sha,
        "criterion": "category = HANDWRITING і subsets ∋ cyrillic; додатково classifications ∋ HANDWRITING",
        "n_families_total": len(families),
        "n_handwriting_category": len(hw_category),
        "n_handwriting_cyrillic": len(hw_cyr),
        "handwriting_cyrillic": [f["family"] for f in hw_cyr],
        "classifications_only_cyrillic": [f["family"] for f in hw_class_only],
        "selected": selected,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"google/fonts {sha[:12]}: сімейств {len(families)}, HANDWRITING {len(hw_category)}, "
          f"з них із кирилицею {len(hw_cyr)}")
    print("  " + ", ".join(f["family"] for f in hw_cyr))
    print(f"лише в classifications (з кирилицею): {', '.join(f['family'] for f in hw_class_only) or '—'}")
    print(f"файлів шрифтів: {sum(len(f['paths']) for f in selected)}")


if __name__ == "__main__":
    main()
