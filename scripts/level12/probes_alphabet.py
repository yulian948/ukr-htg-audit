"""Зонди методів із закритим алфавітом: GANwriting, HiGAN+, HWT, VATr, VATr++, One-DM, WordStylist.

Кожен зонд імпортує кодувальник із репозиторію й викликає його так, як це робить шлях
генерації методу. Посилання на рядки коду перевіряє Site: якщо код зміниться, зонд упаде.
"""

import shutil
import types

from common import Captured, REPOS, Site, in_repo, quiet, run_chars, run_strings, safe_unpickle


def _roundtrip(encode, decode):
    def fn(ch):
        ids = encode(ch)
        back = decode(ids)
        return ("ok" if back == ch else "lossy"), back, None
    return fn


def probe_ganwriting(entries, strings):
    repo = REPOS / "GANwriting"
    with in_repo(repo), quiet():
        import load_data as ld
        ds = ld.IAM_words({}, oov=False)

        def encode(text):  # load_data.py:171 — той самий label_padding, що й у тестовому скрипті
            return ds.label_padding(text, ld.num_tokens)

        def decode(ids):
            body = ids[ids.index(ld.tokens["GO_TOKEN"]) + 1: ids.index(ld.tokens["END_TOKEN"])]
            return "".join(ld.index2letter[i - ld.num_tokens] for i in body)

        level1 = run_chars(entries, _roundtrip(encode, decode), repo)
        # Тестовий скрипт tt.test_single_writer.4_scenarios.py ділить корпус за пробілами
        # (рядок 31: _f.read().split()) і кодує кожне слово label_padding.
        level2 = run_strings(strings, lambda t: (" ".join(decode(encode(w)) for w in t.split()), None), repo)
    return {
        "encoder": "load_data.labelDictionary: 52 латинські літери (string.ascii_lowercase + ascii_uppercase)",
        "paths": {"tt.test_single_writer.4_scenarios.py → label_padding": {"level1": level1, "level2": level2}},
        "notes": ["Алфавіт без цифр і розділових знаків", f"MAX_CHARS = {ld.MAX_CHARS}: довші слова виходять за OUTPUT_MAX_LEN"],
    }


def probe_higan(entries, strings):
    repo = REPOS / "HiGANplus"
    src = repo / "HiGAN+"
    with in_repo(src), quiet():
        from lib.alphabet import Alphabets, strLabelConverter
        conv = strLabelConverter("all")

        def encode(text):  # networks/model.py:469/473 — encode(texts), texts = text.split(' ')
            labels, _ = conv.encode([text, text])  # список із >1 слова: шлях із pad_sequence
            return labels[0].tolist()[: len(text)]

        decode = lambda ids: "".join(conv.alphabet[i] for i in ids)
        level1 = run_chars(entries, _roundtrip(encode, decode), src)
        level2 = run_strings(strings, lambda t: (" ".join(decode(encode(w)) for w in t.split(" ") if w), None), src)
    return {
        "encoder": f"lib/alphabet.py Alphabets['all']: {len(Alphabets['all'])} символів (IAM)",
        "paths": {"networks/model.py eval_style/eval_rand → strLabelConverter.encode": {"level1": level1, "level2": level2}},
        "notes": ["word_capitalize (lib/alphabet.py:155) переводить першу літеру в ASCII через NFKD — лише для випадкових слів лексикону"],
    }


def probe_hwt(entries, strings):
    repo = REPOS / "HWT"
    with in_repo(repo), quiet():
        from params import ALPHABET
        from util.models.OCR_network import strLabelConverter
        conv = strLabelConverter(ALPHABET)

        def encode(text):  # util/models/model.py:520 — encode(self.text), слова в bytes
            ids, _ = conv.encode([text.encode()])
            return ids[0].tolist()

        decode = lambda ids: "".join(conv.alphabet[i - 1] for i in ids)
        level1 = run_chars(entries, _roundtrip(encode, decode), repo)
        site = Site(repo, "util/models/model.py", 520, "self.text = [j.encode() for j in sum([i.split(' ')")
        level2 = run_strings(strings, lambda t: (" ".join(decode(encode(w)) for w in t.split(" ") if w), site), repo)
    return {
        "encoder": f"params.py ALPHABET: {len(ALPHABET)} символів (IAM)",
        "paths": {"mytext.txt → util/models/model.py:520 → strLabelConverter.encode": {"level1": level1, "level2": level2}},
    }


def _vatr_glyphs(pickle_path, entries):
    symbols = {s["idx"][0] for s in safe_unpickle(pickle_path)}
    out = {}
    for e in entries:
        missing = [f"U+{ord(c):04X}" for c in e["char"] if ord(c) not in symbols]
        out[e["id"]] = {"status": "ok" if not missing else "missing", "missing": missing}
    return out, len(symbols)


def probe_vatr(entries, strings):
    repo = REPOS / "VATr"
    with in_repo(repo), quiet():
        from generator import FakeArgs
        from models.OCR_network import strLabelConverter
        args = FakeArgs()
        conv = strLabelConverter(args.alphabet + args.special_alphabet)  # models/model.py:363

        def gen_encode(text):  # generator.py:103 — netconverter.encode(text.split())
            ids, _, _ = conv.encode([text])
            return ids[0].tolist()

        decode = lambda ids: "".join(conv.alphabet[i - 1] for i in ids)
        gen1 = run_chars(entries, _roundtrip(gen_encode, decode), repo)
        gen2 = run_strings(strings, lambda t: (" ".join(decode(gen_encode(w)) for w in t.split()), None), repo)

        # Шлях mytext.txt: фільтр у models/model.py:410 виконуємо як є — збираємо модель
        # (без ваг) з тестовим mytext.txt і читаємо self.text.
        from models.model import VATr
        from models.unifont_module import UnifontModule
        # models/model.py:128 створює UnifontModule без device, а типове значення — 'cuda'.
        # Щоб зібрати модель на CPU, міняємо лише це типове значення.
        UnifontModule.__init__.__defaults__ = ("cpu",) + UnifontModule.__init__.__defaults__[1:]
        site = Site(repo, "models/model.py", 410, "''.join(c for c in self.text if c in (self.args.alphabet + self.args.special_alphabet))")
        args.device = "cpu"
        mytext = repo / "mytext.txt"
        original = mytext.read_bytes()

        def mytext_path(text):
            mytext.write_text(text, encoding="utf-8")
            try:
                model = VATr(args)
            finally:
                mytext.write_bytes(original)
            return " ".join(w.decode() for w in model.text), site

        def mytext_char(ch):
            out, s = mytext_path(f"a{ch}a")
            got = out[1:-1] if out.startswith("a") and out.endswith("a") else out
            return ("ok" if got == ch else "lost" if got == "" else "lossy"), got, (s if got != ch else None)

        my1 = run_chars(entries, mytext_char, repo)
        my2 = run_strings(strings, mytext_path, repo)
        glyphs, n = _vatr_glyphs(repo / "files" / "unifont.pickle", entries)
    return {
        "encoder": f"generator.py FakeArgs: alphabet {len(args.alphabet)} (IAM) + special_alphabet {len(args.special_alphabet)} (грецька)",
        "paths": {
            "generator.py → netconverter.encode": {"level1": gen1, "level2": gen2},
            "mytext.txt → models/model.py:410 → netconverter.encode": {"level1": my1, "level2": my2},
        },
        "glyphs": {"file": "files/unifont.pickle", "n_symbols": n, "entries": glyphs},
    }


def probe_vatrpp(entries, strings):
    repo = REPOS / "VATrplusplus"
    with in_repo(repo), quiet():
        from util.misc import FakeArgs
        from models.OCR_network import strLabelConverter
        from generate.writer import Writer
        args = FakeArgs()
        conv = strLabelConverter(args.alphabet + args.special_alphabet)  # models/model.py:219
        site = Site(repo, "generate/writer.py", 70, 'text = "".join([c for c in text if c in self.model.args.alphabet])')

        def model_stub(*a, **k):
            raise Captured(a)

        fake = types.SimpleNamespace(model=types.SimpleNamespace(
            args=args, netconverter=conv, _generate_fakes=model_stub))

        def writer_path(text):  # generate/writer.py:70–78, виконується справжня create_fake_sentence
            try:
                Writer.create_fake_sentence(fake, None, text)
            except Captured as c:
                text_encode, len_text = c.payload[1], c.payload[2]
                flat = [i for i in text_encode[0].flatten().tolist() if i]  # без нулів доповнення
                return " ".join(_split_words(flat, len_text.tolist(), conv)), site
            raise AssertionError("модель не викликано")

        def char(ch):
            out, s = writer_path(f"a{ch}a")
            got = out[1:-1] if out.startswith("a") and out.endswith("a") else out
            return ("ok" if got == ch else "lost" if got == "" else "lossy"), got, (s if got != ch else None)

        lvl1 = run_chars(entries, char, repo)
        lvl2 = run_strings(strings, writer_path, repo)
    glyphs, n = _vatr_glyphs(REPOS / "vatrpp-hf" / "files" / "unifont.pickle", entries)
    return {
        "encoder": f"util/misc.py FakeArgs: alphabet {len(args.alphabet)} (IAM) + special_alphabet {len(args.special_alphabet)}",
        "paths": {"generate.py → generate/writer.py:70 → netconverter.encode": {"level1": lvl1, "level2": lvl2}},
        "glyphs": {"file": "blowing-up-groundhogs/vatrpp: files/unifont.pickle", "n_symbols": n, "entries": glyphs},
    }


def _split_words(flat_ids, lengths, conv):
    words, pos = [], 0
    for n in lengths:
        words.append("".join(conv.alphabet[i - 1] for i in flat_ids[pos:pos + n]))
        pos += n
    return words


def probe_onedm(entries, strings):
    repo = REPOS / "One-DM"
    glyph_file = REPOS / "onedm-data" / "unifont.pickle"  # з English_data.zip, див. fetch_sources.py
    target = repo / "data" / "unifont.pickle"
    if not target.exists():
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(glyph_file, target)
    safe_unpickle(target)  # той самий набір класів numpy, що й у VATr; інакше впаде тут
    with in_repo(repo), quiet():
        from data_loader.loader import ContentData, letters
        cd = ContentData()  # loader.py:254 — читає data/unifont.pickle
        index2letter = {v: k for k, v in cd.letter2index.items()}

        def encode(text):  # test.py:96 → loader.py:259
            cd.get_content(text)
            return [cd.letter2index[c] for c in text]

        decode = lambda ids: "".join(index2letter[i] for i in ids)
        lvl1 = run_chars(entries, _roundtrip(encode, decode), repo)
        lvl2 = run_strings(strings, lambda t: (" ".join(decode(encode(w)) for w in t.split()), None), repo)
    glyphs, n = _vatr_glyphs(target, entries)
    return {
        "encoder": f"data_loader/loader.py:25 letters: {len(letters)} символів (IAM)",
        "paths": {"test.py → ContentData.get_content": {"level1": lvl1, "level2": lvl2}},
        "glyphs": {"file": "English_data.zip: unifont.pickle", "n_symbols": n, "entries": glyphs,
                   "note": "Файл байт у байт збігається з files/unifont.pickle VATr"},
    }


def probe_wordstylist(entries, strings):
    repo = REPOS / "WordStylist"
    with in_repo(repo), quiet():
        import train  # на рівні модуля лише будує словник (train.py:59) і пише letter2index.json

        def encode(text):  # sampling.py → Diffusion.sampling → train.py:189 label_padding
            return train.label_padding(text, train.num_tokens)

        def decode(ids):  # label_padding доповнює PAD_TOKEN до OUTPUT_MAX_LEN
            body = [i for i in ids if i != train.tokens["PAD_TOKEN"]]
            return "".join(train.index2letter[i - train.num_tokens] for i in body)

        lvl1 = run_chars(entries, _roundtrip(encode, decode), repo)
        lvl2 = run_strings(strings, lambda t: (" ".join(decode(encode(w)) for w in t.split()), None), repo)
    return {
        "encoder": f"train.py:19 c_classes: {len(train.c_classes)} латинських літер",
        "paths": {"sampling.py → train.py:189 label_padding": {"level1": lvl1, "level2": lvl2}},
    }


PROBES = {
    "GANwriting": probe_ganwriting,
    "HiGAN+": probe_higan,
    "HWT": probe_hwt,
    "VATr": probe_vatr,
    "VATr++": probe_vatrpp,
    "One-DM": probe_onedm,
    "WordStylist": probe_wordstylist,
}
