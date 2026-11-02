"""Фіксує версії коду й моделей для аудиту (стаття 1, крок 2).

Читає versions/manifest.json і записує versions/pinned.json:
- git: перевіряє, що кожен коміт є на GitHub (git завантажує лише об'єкт коміту,
  без дерева файлів), бере його дату й заголовок, порівнює з поточним HEAD;
- Hugging Face: поточна ревізія (sha) моделі чи Space, ліцензія, список файлів з SHA-256.
Потрібні лише git і стандартна бібліотека Python: працює і локально, і в Colab.
Ліцензії репозиторіїв беруться з GitHub API (без токена — 60 запитів/год; GITHUB_TOKEN знімає ліміт).

Запуск: python3 scripts/pin_versions.py
"""

import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "versions" / "manifest.json"
OUT = ROOT / "versions" / "pinned.json"


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "ukr-htg-audit", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, str(e.reason)


def github_license(repo):
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    info, err = get_json(f"https://api.github.com/repos/{repo}", headers)
    if err:
        return None, err
    return (info.get("license") or {}).get("spdx_id"), None


def git(*args, cwd=None):
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300)
    return out.stdout.strip() if out.returncode == 0 else None


def pin_git(item):
    repo, sha = item["repo"], item["commit"]
    url = f"https://github.com/{repo}.git"
    row = dict(item)
    with tempfile.TemporaryDirectory() as tmp:
        git("init", "-q", "--bare", tmp)
        fetched = git("fetch", "-q", "--depth", "1", "--filter=tree:0", url, sha, cwd=tmp)
        if fetched is None:
            return row | {"status": "error", "error": f"коміт {sha} не завантажується з {url}"}
        fmt = git("log", "-1", "--format=%H%n%cI%n%P%n%s", sha, cwd=tmp).split("\n", 3)
    full, date, parents, subject = (fmt + [""] * 4)[:4]
    if full != sha:
        return row | {"status": "error", "error": f"очікували {sha}, отримали {full}"}
    row["pinned"] = {"sha": full, "committer_date": date,
                     "is_merge": len(parents.split()) > 1, "subject": subject}
    head = (git("ls-remote", url, "HEAD") or "").split()
    row["head_at_check"] = head[0] if head else None
    row["head_moved"] = bool(head) and head[0] != sha
    row["license"], err = github_license(repo)
    if err:
        row["license_error"] = err
    row["status"] = "ok"
    return row


def pin_hf(item):
    kind, rid = item["kind"], item["id"]
    row = dict(item)
    data, err = get_json(f"https://huggingface.co/api/{kind}s/{rid}?blobs=true")
    if err:
        return row | {"status": "unavailable", "error": err}
    card = data.get("cardData") or {}
    row.update(
        status="ok",
        resolved_id=data.get("id"),
        sha=data.get("sha"),
        last_modified=data.get("lastModified"),
        license=card.get("license"),
        gated=data.get("gated"),
        disabled=data.get("disabled"),
        runtime_stage=(data.get("runtime") or {}).get("stage"),
        files=[
            {"path": s["rfilename"], "size": s.get("size"),
             "lfs_sha256": (s.get("lfs") or {}).get("sha256")}
            for s in data.get("siblings", [])
        ],
    )
    return row


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": [pin_git(x) for x in manifest["git"]],
        "huggingface": [pin_hf(x) for x in manifest["huggingface"]],
        "weights_outside_hf": manifest["weights_outside_hf"],
        "external": manifest.get("external", []),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for g in out["git"]:
        if g["status"] != "ok":
            print(f"GIT  {g['name']:<30} ПОМИЛКА {g['error']}")
            continue
        p = g["pinned"]
        notes = [n for n, on in (("злиття", p["is_merge"]), ("HEAD пішов далі", g["head_moved"])) if on]
        print(f"GIT  {g['name']:<30} {p['sha'][:12]} {p['committer_date'][:10]} "
              f"{g['license'] or g.get('license_error')} {', '.join(notes)}")
    for h in out["huggingface"]:
        if h["status"] != "ok":
            print(f"HF   {h['kind']:<6} {h['id']:<45} НЕДОСТУПНО {h['error']}")
            continue
        size = sum(f["size"] or 0 for f in h["files"]) / 2**20
        flags = " ".join(f for f, on in (("gated", h["gated"]), ("disabled", h["disabled"])) if on)
        stage = f" runtime={h['runtime_stage']}" if h["runtime_stage"] else ""
        moved = f" -> {h['resolved_id']}" if h["resolved_id"] != h["id"] else ""
        print(f"HF   {h['kind']:<6} {h['id']:<45} {h['sha'][:12]} {h['last_modified'][:10]} "
              f"{h['license']} {size:.0f} МБ {flags}{stage}{moved}")
    errors = [g for g in out["git"] if g["status"] != "ok"]
    print(f"\n{OUT.relative_to(ROOT)}: git {len(out['git']) - len(errors)}/{len(out['git'])}, "
          f"HF {sum(h['status'] == 'ok' for h in out['huggingface'])}/{len(out['huggingface'])}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
