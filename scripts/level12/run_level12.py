"""Рівні 1–2 для всіх методів: запускає зонди й зводить таблицю «символ × метод».

Спершу: python3 scripts/level12/fetch_sources.py
Запуск:  python3 scripts/level12/run_level12.py [назва методу ...]
Результати: results/level12/<метод>.json, symbol_x_method.csv, summary.md
"""

import csv
import json
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RESULTS, inventory, pinned, save, test_strings  # noqa: E402
import probes_alphabet  # noqa: E402
import probes_tokenizer  # noqa: E402

PROBES = {**probes_alphabet.PROBES, **probes_tokenizer.PROBES}
SOURCE = {"Українська DiffusionPen": "kdonitz/diffusionpen-ukrainian"}
GROUPS = ("alphabet", "apostrophe", "punctuation", "historical")


def version_of(method):
    if method in SOURCE:
        row = next(h for h in pinned_all() if h.get("id") == SOURCE[method] and h["kind"] == "space")
        return {"source": f"hf space {row['id']}", "revision": row["sha"]}
    row = pinned(method)
    return {"source": f"github {row['repo']}", "revision": row["commit"]}


def environment():
    import platform
    from importlib.metadata import PackageNotFoundError, version
    env = {"python": platform.python_version(), "platform": platform.platform()}
    for pkg in ("torch", "transformers", "numpy"):
        try:
            env[pkg] = version(pkg)
        except PackageNotFoundError:
            env[pkg] = None
    return env


def pinned_all():
    from common import ROOT
    return json.loads((ROOT / "versions" / "pinned.json").read_text(encoding="utf-8"))["huggingface"]


def main(selected):
    inv, entries = inventory()
    strings = test_strings(inv)
    table = {}
    for method, probe in PROBES.items():
        if selected and method not in selected:
            continue
        try:
            payload = probe(entries, strings)
            payload["status"] = "ok"
        except Exception as exc:  # noqa: BLE001 — зонд, що впав, теж результат
            payload = {"status": "probe_failed", "error": f"{type(exc).__name__}: {exc}",
                       "traceback": traceback.format_exc()[-2000:]}
        payload.update(method=method, inventory_version=inv["inventory_version"], environment=environment(),
                       checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), **version_of(method))
        save(method, payload)
        report(method, payload, entries)
    # Зведення — з усіх збережених результатів, тож методи можна запускати й окремо
    for method in PROBES:
        path = RESULTS / f"{method}.json"
        if path.exists():
            table[method] = json.loads(path.read_text(encoding="utf-8"))
    write_table(table, entries)


def report(method, payload, entries):
    if payload["status"] != "ok":
        print(f"\n== {method}: ЗОНД НЕ ВИКОНАНО — {payload['error']}")
        return
    print(f"\n== {method} [{payload['revision'][:12]}] — {payload['encoder']}")
    by_id = {e["id"]: e for e in entries}
    for path, res in payload["paths"].items():
        if "level1" in res:
            c = Counter((by_id[i]["group"], r["status"]) for i, r in res["level1"].items())
            parts = []
            for g in GROUPS:
                n = sum(v for (gg, _), v in c.items() if gg == g)
                ok = c.get((g, "ok"), 0)
                parts.append(f"{g} {ok}/{n}")
            sites = Counter(r["where"]["ref"] for r in res["level1"].values() if r.get("where"))
            print(f"  {path}\n    рівень 1: {', '.join(parts)}" + (f"; втрати: {dict(sites)}" if sites else ""))
        if "level2" in res:
            for k, r in res["level2"].items():
                if r["status"] != "ok":
                    detail = r.get("error") or f"втрачено {r['lost']} змінено {r['changed']}"
                    where = f" @ {r['where']['ref']}" if r.get("where") else ""
                    print(f"    рівень 2 [{k}]: {r['status']} — {detail[:150]}{where}")


def write_table(table, entries):
    cols = []
    for method, p in table.items():
        if p["status"] != "ok":
            cols.append((method, None, None))
            continue
        for path, res in p["paths"].items():
            if "level1" in res:
                cols.append((method, path, res["level1"]))
        if "glyphs" in p and "entries" in p["glyphs"]:
            cols.append((method, "гліфи " + p["glyphs"]["file"], p["glyphs"]["entries"]))
    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(RESULTS / "symbol_x_method.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "char", "codepoints", "group"] + [f"{m} | {p}" if p else m for m, p, _ in cols])
        for e in entries:
            row = [e["id"], e["char"], " ".join(e["codepoints"]), e["group"]]
            for _, _, res in cols:
                if res is None:
                    row.append("probe_failed")
                else:
                    r = res[e["id"]]
                    row.append(r["status"] + (f" @ {r['where']['ref']}" if r.get("where") else ""))
            w.writerow(row)

    lines = ["# Рівні 1–2: зведення", "",
             "Частка символів інвентарю зі статусом ok за групами. Повні дані — symbol_x_method.csv і <метод>.json.", "",
             "| Метод | Шлях | " + " | ".join(GROUPS) + " | Де губиться |", "|---|---|" + "---|" * (len(GROUPS) + 1)]
    for m, p, res in cols:
        if res is None:
            lines.append(f"| {m} | — | " + " | ".join("зонд не виконано" for _ in GROUPS) + " | |")
            continue
        cells = []
        for g in GROUPS:
            ids = [e["id"] for e in entries if e["group"] == g]
            ok = sum(res[i]["status"] == "ok" for i in ids)
            cells.append(f"{ok}/{len(ids)}")
        sites = sorted({r["where"]["ref"] for r in res.values() if r.get("where")})
        lines.append(f"| {m} | {p} | " + " | ".join(cells) + f" | {', '.join(sites)} |")
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{RESULTS / 'symbol_x_method.csv'}\n{RESULTS / 'summary.md'}")


if __name__ == "__main__":
    main(sys.argv[1:])
