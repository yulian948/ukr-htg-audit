"""Спільне для зондів рівнів 1–2 (стаття 1, крок 3).

Зонд виконує справжній код репозиторію методу: кодувальник алфавіту чи токенізатор
(рівень 1) і функції підготовки тексту (рівень 2). Нейромережі не потрібні: там, де шлях
тексту доходить до моделі, зонд підставляє заглушку, що лише записує отримані дані.

Статуси символу:
  ok     — символ пройшов без змін;
  lossy  — пройшов, але змінився (інший символ, інший регістр, розклад тощо);
  lost   — мовчки вилучений (фільтр, заміна на порожнє місце);
  error  — виняток (KeyError тощо); where — файл і рядок у репозиторії.
"""

import contextlib
import io
import json
import os
import pickle
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "inventory"))
from load import load_inventory  # noqa: E402

# Код методів, ваги й шрифти (усе відтворюване) — поза текою проєкту
WORK = Path(os.environ.get("AUDIT_WORK", Path.home() / ".cache" / "ukr-htg-audit" / "work"))
REPOS = WORK / "repos"
RESULTS = ROOT / "results" / "level12"


class Captured(Exception):
    """Заглушка моделі кидає це, щоб зупинити шлях і повернути те, що до неї дійшло."""

    def __init__(self, payload):
        super().__init__("captured")
        self.payload = payload


class Site:
    """Місце в коді, де символ губиться без винятку. Перевіряємо, що рядок справді такий."""

    def __init__(self, repo_dir, file, line, contains):
        self.file, self.line = file, line
        text = (Path(repo_dir) / file).read_text(encoding="utf-8").splitlines()[line - 1]
        if contains not in text:
            raise AssertionError(f"{file}:{line} не містить {contains!r}: {text.strip()!r}")
        self.code = text.strip()

    @classmethod
    def find(cls, repo_dir, file, contains):
        """Те саме, але рядок шукаємо: у різних версіях репозиторію він зсувається."""
        lines = (Path(repo_dir) / file).read_text(encoding="utf-8").splitlines()
        hits = [i for i, text in enumerate(lines, start=1) if contains in text]
        if len(hits) != 1:
            raise AssertionError(f"{file}: {contains!r} знайдено {len(hits)} разів")
        return cls(repo_dir, file, hits[0], contains)

    def ref(self):
        return f"{self.file}:{self.line}"


def where_in_repo(exc, repo_dir):
    """Останній кадр трасування, що лежить у репозиторії методу."""
    repo_dir = str(Path(repo_dir).resolve())
    frames = [f for f in traceback.extract_tb(exc.__traceback__)
              if str(Path(f.filename).resolve()).startswith(repo_dir)]
    if not frames:
        return None
    f = frames[-1]
    return {"ref": f"{Path(f.filename).resolve().relative_to(repo_dir)}:{f.lineno}", "code": f.line}


@contextlib.contextmanager
def in_repo(repo_dir):
    """Репозиторії відкривають файли відносними шляхами, тож працюємо з їхнього кореня.

    Різні репозиторії мають однакові назви пакетів (util, models, train), тому після виходу
    вивантажуємо все, що імпортовано з цього репозиторію.
    """
    old_cwd, old_path = os.getcwd(), list(sys.path)
    root = str(Path(repo_dir).resolve())
    os.chdir(repo_dir)
    sys.path.insert(0, str(repo_dir))
    try:
        yield
    finally:
        os.chdir(old_cwd)
        sys.path[:] = old_path
        for name, mod in list(sys.modules.items()):
            f = getattr(mod, "__file__", None) or ""
            if f and str(Path(f).resolve()).startswith(root):
                del sys.modules[name]


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def safe_unpickle(path):
    """Читає pickle гліфів, дозволяючи лише класи numpy (перевірено pickletools)."""
    import numpy as np

    allowed = {("numpy", "ndarray"), ("numpy", "dtype"),
               ("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct")}

    class Restricted(pickle.Unpickler):
        def find_class(self, module, name):
            if (module, name) not in allowed:
                raise pickle.UnpicklingError(f"заборонено {module}.{name}")
            if name == "_reconstruct":
                return np._core.multiarray._reconstruct if hasattr(np, "_core") else np.core.multiarray._reconstruct
            return getattr(np, name)

    with open(path, "rb") as f:
        return Restricted(f).load()


def _error_row(exc, repo_dir):
    """Виняток у коді репозиторію — результат методу; поза ним — збій самого зонда."""
    where = where_in_repo(exc, repo_dir)
    return {"status": "error" if where else "probe_error",
            "error": f"{type(exc).__name__}: {exc}"[:200], "where": where}


def run_chars(entries, fn, repo_dir):
    """fn(char) -> (status, output, site|None). Винятки ловимо й прив'язуємо до рядка коду."""
    out = {}
    for e in entries:
        ch = e["char"]
        try:
            status, value, site = fn(ch)
            row = {"status": status, "output": value}
            if site is not None:
                row["where"] = {"ref": site.ref(), "code": site.code}
        except Exception as exc:  # noqa: BLE001 — саме виняток і є результатом
            row = _error_row(exc, repo_dir)
        out[e["id"]] = row
    return out


def compare(src, dst):
    """Що з src не дійшло до dst (посимвольно, з урахуванням порядку)."""
    import difflib
    sm = difflib.SequenceMatcher(a=src, b=dst, autojunk=False)
    lost, changed = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "delete":
            lost.append(src[i1:i2])
        elif op == "replace":
            changed.append([src[i1:i2], dst[j1:j2]])
    return lost, changed


def run_strings(strings, fn, repo_dir):
    """fn(text) -> (output_text, site|None) — проводимо тестові рядки через підготовку тексту."""
    out = {}
    for key, text in strings.items():
        try:
            result, site = fn(text)
            lost, changed = compare(text, result)
            row = {"input": text, "output": result, "lost": lost, "changed": changed,
                   "status": "ok" if not lost and not changed else "lost" if not changed else "lossy"}
            if site is not None and (lost or changed):
                row["where"] = {"ref": site.ref(), "code": site.code}
        except Exception as exc:  # noqa: BLE001
            row = {"input": text, **_error_row(exc, repo_dir)}
        out[key] = row
    return out


def test_strings(inv):
    return {k: v for k, v in inv["test_strings"].items() if k != "all_chars"}


def save(method, payload):
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{method}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def pinned(name):
    data = json.loads((ROOT / "versions" / "pinned.json").read_text(encoding="utf-8"))
    for key in ("git", "huggingface"):
        for row in data[key]:
            if row.get("name") == name or row.get("id") == name:
                return row
    raise KeyError(name)


def inventory():
    return load_inventory()
