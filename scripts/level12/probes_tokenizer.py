"""Зонди методів із відкритим токенізатором: DiffusionPen, українська DiffusionPen (CANINE),
Emuru, Eruku (ByT5). Токенізатори завантажуються на ревізіях із versions/pinned.json.
"""

import ast
import types

import numpy as np

from common import Captured, REPOS, Site, in_repo, pinned, quiet, run_chars, run_strings


def _hf_revision(model_id):
    return pinned(model_id)["sha"]


def _canine():
    from transformers import CanineTokenizer
    return CanineTokenizer.from_pretrained("google/canine-c", revision=_hf_revision("google/canine-c"))


def _byt5():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained("google/byt5-small", revision=_hf_revision("google/byt5-small"))


def _tok_roundtrip(tok, call, max_len=None):
    def fn(ch):
        ids = call(ch)
        back = tok.decode(ids, skip_special_tokens=True)
        status = "ok" if back == ch else "lossy"
        return status, back, None
    return fn


def probe_diffusionpen(entries, strings):
    repo = REPOS / "DiffusionPen"
    tok = _canine()
    site = Site(repo, "train.py", 263, 'tokenizer(text_features, padding="max_length", truncation=True, return_tensors="pt", max_length=40)')

    def encode(text):  # train.py:263 — ті самі параметри, що в Diffusion.sampling
        return tok(text, padding="max_length", truncation=True, return_tensors="pt", max_length=40).input_ids[0].tolist()

    lvl1 = run_chars(entries, _tok_roundtrip(tok, encode), repo)
    # Режим paragraph (train.py:757): lines.strip().split(' '), кожне слово окремо в sampling.
    lvl2 = run_strings(strings, lambda t: (" ".join(tok.decode(encode(w), skip_special_tokens=True)
                                                     for w in t.strip().split(" ")), site), repo)
    return {
        "encoder": "CANINE (google/canine-c): кодові точки Unicode; max_length=40 разом зі службовими токенами",
        "paths": {"train.py --train_mode sampling → Diffusion.sampling → CanineTokenizer": {"level1": lvl1, "level2": lvl2}},
        "notes": ["Слова, довші за 38 кодових точок, обрізаються (truncation=True, train.py:263)"],
    }


def _load_space_function(path, name, namespace):
    """Виконує одну функцію з файлу як є, не імпортуючи сам файл (app.py при імпорті вантажить моделі)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    node.decorator_list = []  # @spaces.GPU лише виділяє GPU в Hugging Face Spaces
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name], node.lineno


def probe_ukr_diffusionpen(entries, strings):
    repo = REPOS / "UkrDiffusionPen-space"
    tok = _canine()
    with in_repo(repo), quiet():
        import generate_sentence as gs
        captured = {}

        def generate_single_word(word, tokenizer, text_max_len, **_):
            # generate_sentence.py:1216 encode_text_context: ті самі параметри токенізатора
            ids = tokenizer(word, padding="max_length", truncation=True, return_tensors="pt",
                            max_length=text_max_len).input_ids[0].tolist()
            captured.setdefault("words", []).append(tokenizer.decode(ids, skip_special_tokens=True))
            return gs.Image.new("L", (8, 64), 255)

        real_sample = gs.sample_punctuation

        def sample_punctuation(ch, *a, **k):
            arr = real_sample(ch, *a, **k)
            captured.setdefault("punct", []).append((ch, arr is not None))
            return arr

        def compose_sentence_geometry(**kw):
            raise Captured(kw)

        ns = {
            **{k: getattr(gs, k) for k in ("PUNCTUATION", "split_word_for_generation", "crop_whitespace")},
            "np": np, "torch": __import__("torch"), "random": __import__("random"), "time": __import__("time"),
            "sample_punctuation": sample_punctuation, "generate_single_word": generate_single_word,
            "compose_sentence_geometry": compose_sentence_geometry,
            "normalize_ink_brightness": lambda imgs: imgs,
            "MODEL": {"unet": types.SimpleNamespace(to=lambda d: None), "vae": types.SimpleNamespace(to=lambda d: None),
                      "style_extractor": types.SimpleNamespace(to=lambda d: None),
                      "tokenizer": tok, "noise_scheduler": None},
            "_random_writer": lambda lucky=False: "0000", "WRITER_ID_MAP": {"0000": 0},
            "_load_writer_style_ref": lambda w, d: None, "_load_recent_table": lambda: None,
            "PUNCT_BANK_DIR": str(repo / "punct_bank"), "IMG_HEIGHT": 64, "IMG_WIDTH": 256,
            "TEXT_MAX_LEN": 40, "CANVAS_HEIGHT": 104,
        }
        generate, lineno = _load_space_function(repo / "app.py", "generate", ns)
        site_bank = Site(repo, "app.py", 324, "word_images.append(ch_arr if ch_arr is not None else np.full((IMG_HEIGHT, 6), 255")

        def app_path(text):
            """Справжня app.generate по одному слову; результат — те, що реально потрапляє на зображення."""
            out_words = []
            for word in text.split():
                captured.clear()
                try:
                    generate(word, 0)
                except Captured as c:
                    kw = c.payload
                    punct_ok = iter(captured.get("punct", []))
                    gen_words = iter(captured.get("words", []))
                    parts = []
                    for w, is_p in zip(kw["expanded_words"], kw["punct_flags"]):
                        if is_p:
                            ch, has_img = next(punct_ok)
                            parts.append(ch if has_img else "")
                        else:
                            parts.append(next(gen_words))
                    out_words.append("".join(parts))
                else:
                    out_words.append("")
            return " ".join(out_words), site_bank

        def char(ch):
            out, s = app_path(f"а{ch}")  # знак у кінці слова: так його обробляє app.generate
            got = out[1:] if out.startswith("а") else out
            return ("ok" if got == ch else "lost" if got == "" else "lossy"), got, (s if got != ch else None)

        lvl1 = run_chars(entries, _tok_roundtrip(tok, lambda ch: tok(ch).input_ids), repo)
        lvl2_chars = run_chars(entries, char, repo)
        lvl2 = run_strings(strings, app_path, repo)
        bank = sorted(p.name for p in (repo / "punct_bank").iterdir() if p.is_dir())
    return {
        "encoder": "CANINE (google/canine-c); розділові знаки в кінці слова — із банку зображень punct_bank",
        "paths": {
            "CanineTokenizer (кодування окремого символу)": {"level1": lvl1},
            f"app.py:{lineno} generate → punct_bank / CANINE": {"level1": lvl2_chars, "level2": lvl2},
        },
        "notes": [
            f"Теки punct_bank: {', '.join(bank)}; _PUNCT_SUBDIR (generate_sentence.py:902) зіставляє з ними , . ? ! : ; -",
            "Знак із PUNCTUATION (generate_sentence.py:40) у кінці слова без теки в банку замінюється порожнім полем 6 пікс.",
            "app.generate виконано з файлу app.py без імпорту модуля (при імпорті він вантажить моделі й будує інтерфейс)",
        ],
    }


def probe_emuru(entries, strings):
    repo = REPOS / "Emuru"
    tok = _byt5()
    site = Site(repo, "models/emuru.py", 154, "texts = [style_text + ' ' + gen_text]")

    def encode(text):  # models/emuru.py:154 і :228
        return tok([text], return_tensors="pt", padding=True).input_ids[0].tolist()

    lvl1 = run_chars(entries, _tok_roundtrip(tok, encode), repo)
    lvl2 = run_strings(strings, lambda t: (tok.decode(encode("style" + " " + t), skip_special_tokens=True)[len("style "):], site), repo)
    utf8 = {e["id"]: len(e["char"].encode("utf-8")) for e in entries}
    return {
        "encoder": "ByT5 (google/byt5-small): байти UTF-8",
        "paths": {"models/emuru.py generate → tokenizer(style_text + ' ' + gen_text)": {"level1": lvl1, "level2": lvl2}},
        "utf8_bytes": utf8,
        "notes": ["Кирилична літера — 2 байти UTF-8, ꙋ і ʼ — 2–3: кодується без втрат, але як послідовності байтів, яких у латинському навчанні не було"],
    }


def probe_eruku(entries, strings, repo_name="Eruku"):
    repo = REPOS / repo_name
    tok = _byt5()
    tok.add_tokens(["<sog>"])  # eruku_continuous_inf.py: self.tokenizer.add_tokens(["<sog>"])
    Site.find(repo, "eruku_continuous_inf.py", 'self.tokenizer.add_tokens(["<sog>"])')
    site = Site.find(repo, "eruku_continuous_inf.py", 'for style, gen in zip(style_text,gen_text)')

    def encode(text):
        return tok([text], padding=True, return_tensors="pt").input_ids[0].tolist()

    def gen_path(text):  # eruku_continuous_inf.py:365 — f"{style}<sog>{gen}"
        decoded = tok.decode(encode(f"style<sog>{text}"), skip_special_tokens=False)
        return decoded.split("<sog>", 1)[1].replace("</s>", ""), site

    lvl1 = run_chars(entries, _tok_roundtrip(tok, encode), repo)
    lvl2 = run_strings(strings, gen_path, repo)
    return {
        "encoder": "ByT5 (google/byt5-small) + токен <sog>",
        "paths": {"eruku_continuous_inf.py generate → tokenizer(f'{style}<sog>{gen}')": {"level1": lvl1, "level2": lvl2}},
    }


PROBES = {
    "DiffusionPen": probe_diffusionpen,
    "Українська DiffusionPen": probe_ukr_diffusionpen,
    "Emuru": probe_emuru,
    "Eruku": probe_eruku,
    "Eruku (aimagelab, версія пропозиції)": lambda e, s: probe_eruku(e, s, "Eruku-aimagelab"),
}
