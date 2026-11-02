"""Завантажує код методів на зафіксованих ревізіях (versions/pinned.json) у work/repos.

- git-репозиторії методів: лише потрібний коміт (git fetch --depth 1);
- Space української DiffusionPen: код і по 2 зображення з кожної теки punct_bank;
- файли гліфів unifont.pickle моделі VATr++ з Hugging Face і One-DM з архіву даних
  на Google Drive (з архіву читається лише цей файл).
Ваги моделей не завантажуються: для рівнів 1–2 вони не потрібні.
Токенізатори CANINE і ByT5 завантажує transformers на зафіксованих ревізіях під час зондування.

Запуск: python3 scripts/level12/fetch_sources.py
"""

import hashlib
import io
import re
import zipfile
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPOS, pinned  # noqa: E402

import json  # noqa: E402

PINNED = json.loads((Path(__file__).resolve().parents[2] / "versions" / "pinned.json").read_text(encoding="utf-8"))


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name.replace("+", "plus")).strip("-")


def fetch_git(row):
    dest = REPOS / slug(row["name"])
    sha = row["commit"]
    if (dest / ".git").exists() and subprocess.run(
            ["git", "-C", dest, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() == sha:
        return dest, "вже є"
    dest.mkdir(parents=True, exist_ok=True)
    run = lambda *a: subprocess.run(["git", "-C", dest, *a], check=True, capture_output=True)
    if not (dest / ".git").exists():
        run("init", "-q")
        run("remote", "add", "origin", f"https://github.com/{row['repo']}.git")
    run("fetch", "-q", "--depth", "1", "origin", sha)
    run("-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD")
    return dest, "завантажено"


def hf_file(repo, kind, sha, path, dest, lfs_sha256=None):
    prefix = "spaces/" if kind == "space" else ""
    url = f"https://huggingface.co/{prefix}{repo}/resolve/{sha}/{path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        if dest.exists():
            break
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read()
            dest.write_bytes(data)
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    if lfs_sha256:
        got = hashlib.sha256(dest.read_bytes()).hexdigest()
        if got != lfs_sha256:
            raise RuntimeError(f"{path}: SHA-256 {got} ≠ {lfs_sha256}")


def fetch_space():
    row = next(h for h in PINNED["huggingface"]
               if h["id"] == "kdonitz/diffusionpen-ukrainian" and h["kind"] == "space")
    dest = REPOS / "UkrDiffusionPen-space"
    bank = defaultdict(list)
    for f in row["files"]:
        p = f["path"]
        if p.endswith(".py") or p in ("README.md", "requirements.txt"):
            hf_file(row["id"], "space", row["sha"], p, dest / p, f["lfs_sha256"])
        elif p.startswith("punct_bank/") and p.endswith(".png"):
            bank[p.split("/")[1]].append(f)
    for files in bank.values():
        for f in sorted(files, key=lambda x: x["path"])[:2]:
            hf_file(row["id"], "space", row["sha"], f["path"], dest / f["path"], f["lfs_sha256"])
    (dest / "PINNED_SHA").write_text(row["sha"] + "\n")
    return dest, f"{row['sha'][:12]}, punct_bank: {', '.join(sorted(bank))}"


def fetch_vatrpp_glyphs():
    row = next(h for h in PINNED["huggingface"] if h["id"] == "blowing-up-groundhogs/vatrpp")
    f = next(x for x in row["files"] if x["path"] == "files/unifont.pickle")
    dest = REPOS / "vatrpp-hf" / "files" / "unifont.pickle"
    hf_file(row["id"], "model", row["sha"], f["path"], dest, f["lfs_sha256"])
    return dest, f"{row['sha'][:12]}, {f['size'] / 2**20:.1f} МБ"


class RangeFile(io.RawIOBase):
    """Файл на HTTP-сервері, який читаємо діапазонами байтів (Range): zipfile бере лише потрібне."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        self.pos = {io.SEEK_SET: offset, io.SEEK_CUR: self.pos + offset, io.SEEK_END: self.size + offset}[whence]
        return self.pos

    def read(self, n=-1):
        end = self.size if n is None or n < 0 else min(self.size, self.pos + n)
        if self.pos >= end:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end - 1}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        self.pos += len(data)
        return data


# One-DM: файл гліфів лежить лише в архіві даних на Google Drive (README, розділ Datasets)
ONEDM_ZIP = "https://drive.usercontent.google.com/download?id=10BMCU38cBJfLebzrS3LVl47RtBrRdxOz&export=download&confirm=t"


def fetch_onedm_glyphs():
    dest = REPOS / "onedm-data" / "unifont.pickle"
    info = dest.with_suffix(".source.json")
    if not dest.exists():
        with zipfile.ZipFile(RangeFile(ONEDM_ZIP)) as z:
            member = next(n for n in z.namelist() if n.endswith("unifont.pickle"))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(member))
            info.write_text(json.dumps({
                "archive": "English_data.zip (Google Drive 10BMCU38cBJfLebzrS3LVl47RtBrRdxOz)",
                "member": member, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
            }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    meta = json.loads(info.read_text(encoding="utf-8"))
    return dest, f"{meta['member']}, sha256 {meta['sha256'][:12]}"


def main():
    REPOS.mkdir(parents=True, exist_ok=True)
    for row in PINNED["git"]:
        if row["role"] in ("method", "related", "synthesis_tool") and row["status"] == "ok":
            dest, msg = fetch_git(row)
            print(f"{row['name']:<38} {row['commit'][:12]} {msg}", flush=True)
    for fn, label in ((fetch_space, "Space української DiffusionPen"), (fetch_vatrpp_glyphs, "VATr++ unifont.pickle"),
                      (fetch_onedm_glyphs, "One-DM unifont.pickle")):
        dest, msg = fn()
        print(f"{label:<38} {msg}")


if __name__ == "__main__":
    main()
