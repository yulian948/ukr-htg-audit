"""Будує єдиний інвентар символів для аудиту (стаття 1).

Результат: inventory/charset_inventory.json — його читають усі скрипти аудиту.
Запуск: python3 inventory/build_inventory.py
"""

import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

OUT = Path(__file__).with_name("charset_inventory.json")
INVENTORY_VERSION = "0.3.0"

# --- 1. Алфавіт ---------------------------------------------------------------
# 33 літери сучасної абетки (з ґ). Окремого параграфа з абеткою правопис 2019 р.
# не має; ґ згадано в передмові як відновлену.
ALPHABET_LOWER = [
    "а", "б", "в", "г", "ґ", "д", "е", "є", "ж", "з", "и", "і", "ї", "й",
    "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч",
    "ш", "щ", "ь", "ю", "я",
]

# Літери, рукописна форма яких (за прописами) відрізняється від друкованої.
# Позначено мінускули: саме їх кодуємо за прописами на рівні 4.
KEY_HANDWRITTEN = ["т", "д", "и", "п", "ш", "г", "б", "в", "з"]

# --- 2. Апостроф: три кодування ---------------------------------------------
# Правопис (§ 7, 138, 151) визначає вживання апострофа, але не кодову точку.
APOSTROPHES = [
    (chr(0x02BC), "primary", "Літера-модифікатор апостроф; рекомендоване кодування українського апострофа"),
    (chr(0x2019), "alternative", "Права одинарна лапка; типографська заміна апострофа"),
    (chr(0x0027), "alternative", "Машинописний апостроф ASCII; клавіатурна заміна"),
]

# --- 3. Розділові знаки (правопис 2019, розд. V, § 155–168) -------------------
# Перелік основних знаків — у вступі до розд. V; скісна риска — «крім них» (§ 165).
# (символ, нормативна назва, роль, параграф, примітка)
PUNCTUATION = [
    (".", "крапка", "primary", "§ 155", None),
    ("?", "знак питання", "primary", "§ 156", None),
    ("!", "знак оклику", "primary", "§ 157", None),
    (",", "кома", "primary", "§ 158", None),
    (";", "крапка з комою", "primary", "§ 159", None),
    (":", "двокрапка", "primary", "§ 160", None),
    (chr(0x2014), "тире", "primary", "§ 161", "Довге тире: так набрано заголовок § 161 «ТИРЕ (—)»"),
    (chr(0x2013), "тире", "alternative", "§ 161", "Коротке тире: поширена типографська заміна; так набрано § 161 у змісті видання"),
    (chr(0x2026), "три крапки", "primary", "§ 162", "Один знак U+2026; заголовок § 162 подає «(...)», тому варіант із трьох U+002E — у test_strings"),
    ("(", "дужки круглі", "primary", "§ 163", "Відкривна"),
    (")", "дужки круглі", "primary", "§ 163", "Закривна"),
    ("[", "дужки квадратні", "primary", "§ 163", "Відкривна"),
    ("]", "дужки квадратні", "primary", "§ 163", "Закривна"),
    ("<", "дужки кутові", "primary", "§ 163", "Відкривна; у правописі «кутові, або ламані (< >)», зокрема <…> для пропуску в цитаті"),
    (">", "дужки кутові", "primary", "§ 163", "Закривна"),
    (chr(0x00AB), "лапки", "primary", "§ 164", "Відкривні «лапки-ялинки» — рекомендовані зовнішні"),
    (chr(0x00BB), "лапки", "primary", "§ 164", "Закривні «лапки-ялинки»"),
    (chr(0x201E), "лапки", "primary", "§ 164", "Відкривні в парах „ “ і „ ”"),
    (chr(0x201C), "лапки", "primary", "§ 164", "Відкривні в парі “ ”, закривні в парі „ “ — «лапки-лапки», рекомендовані внутрішні"),
    (chr(0x201D), "лапки", "primary", "§ 164", "Закривні в парах “ ” і „ ”; форма „…” — традиційна в рукописних текстах (§ 164, п. 3)"),
    (chr(0x0022), "лапки", "alternative", "§ 164", "Прямі лапки ASCII, клавіатурна заміна"),
    ("-", "дефіс", "primary", "§ 37", "Як розділовий знак — у синтаксичних сполученнях (вступ до розд. V); U+002D — фактичне кодування"),
    (chr(0x2010), "дефіс", "alternative", "§ 37", "Типографський дефіс U+2010"),
    ("/", "скісна риска", "primary", "§ 165", "Розділовий знак (вступ до розд. V, § 165)"),
]

# --- 4. Історичні знаки XIX — поч. XX ст. -------------------------------------
# status: "core" — названі в пропозиції; "attested" — засвідчені в правописних
# системах XIX — поч. XX ст. Сторінки (с.) — за хрестоматією Німчука (2004, див.
# SOURCES_HISTORICAL); «Вікіпедія» — лише там, де в хрестоматії підтвердження не знайдено.
HISTORICAL = [
    ("ы", "core", "Єри; абетки Шевченка 1861 (с. 69) і Куліша 1857 (с. 75), Павловський 1818 (с. 40)"),
    ("ъ", "core", "Єр; абетки Шевченка 1861 (с. 69) і Куліша 1857 (с. 75), Павловський 1818 (с. 40)"),
    ("ѣ", "core", "Ять; абетки Шевченка і Куліша (с. 69, 75), Максимович (с. 89)"),
    ("ѳ", "core", "Фіта; абетки Шевченка 1861 (с. 69) і Куліша 1857 (с. 75)"),
    ("ѵ", "core", "Іжиця; абетки Шевченка і Куліша (с. 69, 75); Павловський: ще вживана на письмі (с. 40)"),
    ("ё", "attested", "Куліш, «Граматка» 1857: «сёго», «Ёго» (с. 75); слобожанський правопис (прим. упорядника, с. 68)"),
    ("э", "attested", "Абетки Шевченка 1861 (с. 69) і Куліша 1857 (с. 75)"),
    ("j", "attested", "Драгоманівка: латинська j для йотованих — ja, je, jy, ji (с. 161)"),
    ("ѯ", "attested", "Павловський 1818: «употребляютъ буквы Кси, Пси, Ижицу» (с. 40)"),
    ("ѱ", "attested", "Павловський 1818: «употребляютъ буквы Кси, Пси, Ижицу» (с. 40)"),
    ("ꙋ", "attested", "Гатцук, «Українська абетка» 1861: ук-монограф на місці у (с. 83); система не поширилася"),
    ("ѧ", "attested", "Гатцук 1861: юс малий на місці я (с. 83); система не поширилася"),
    # Максимовичівка: п'ять знаків для [і] — ѣ, ô, ê, ŷ, û (с. 89). Кириличних складених
    # символів немає, тому це послідовність «літера + U+0302».
    ("о" + chr(0x0302), "attested", "Максимович: [і] з етимологічного о, «нôсъ» (с. 89)"),
    ("е" + chr(0x0302), "attested", "Максимович: [і] з етимологічного е, «мêдъ» (с. 89)"),
    ("у" + chr(0x0302), "attested", "Максимович: [і] з етимологічного у, «замŷжъ» (с. 89)"),
    ("и" + chr(0x0302), "attested", "Максимович: [і] з етимологічного и, «добрû» (с. 89)"),
    # Знаки наголосу в текстах XIX ст.; носій — «а», бо важить сам комбінований знак.
    ("а" + chr(0x0301), "attested", "Наголос (акут, U+0301): Павловський 1818 (с. 40), Шевченко 1861 (с. 69), Куліш 1857 (с. 75)"),
    ("а" + chr(0x0300), "attested", "Наголос (гравіс, U+0300): Шевченко, «Буквар» 1861 (с. 69)"),
    ("g", "attested", "Кулішівка 1856–57: латинська g на позначення ґ (Вікіпедія; у переглянутих сторінках хрестоматії не знайдено)"),
]

# Кандидати попередніх версій, вилучені з інвентарю, з причиною.
EXCLUDED_HISTORICAL = {
    "ѕ ѡ ѫ ѹ": "Гатцук 1861 перелічує їх серед вилучених із церковної абетки (с. 83); у системах XIX ст. не вживаються",
    "ј (кирилична)": "Драгоманівка вживала латинську j (с. 161) — див. запис j",
    "а̂ і̂": "Максимович: серед знаків для [і] не названі (с. 89)",
    "надрядкові знаки Гатцука": "Система 1861 р. мала багато надрядкових знаків і не поширилася (с. 82); до інвентарю взято лише ꙋ і ѧ",
}

SOURCES_HISTORICAL = [
    "Німчук В. В., Пуряєва Н. В. (упор.) Історія українського правопису: XVI–XX століття. Хрестоматія. К.: Наукова думка, 2004. "
    "Електронна копія: Електронна бібліотека Інституту історії України НАН України, resource.history.org.ua/item/0007903",
    "Вікіпедія: Кулішівка (латинська g; переглянуто 23.10.2026)",
]

QUICK_TEST = "ґєії" + chr(0x02BC) + " ыъѣ"
PANGRAM = "Чуєш їх, доцю, га? Кумедна ж ти, прощайся без ґольфів!"


def codepoints(s):
    return [f"U+{ord(c):04X}" for c in s]


def names(s):
    return [unicodedata.name(c, "<unnamed>") for c in s]


def describe(s):
    """Поля, однакові для всіх записів: кодові точки й поведінка нормалізації."""
    nfd = unicodedata.normalize("NFD", s)
    nfc = unicodedata.normalize("NFC", s)
    return {
        "char": s,
        "codepoints": codepoints(s),
        "unicode_names": names(s),
        "n_codepoints": len(s),
        "nfc_equal": nfc == s,
        "nfd_codepoints": codepoints(nfd) if nfd != s else None,
    }


def letter_pair(lower, group, extra):
    rows = []
    upper = lower.upper()
    for ch, case, pair in ((lower, "lower", upper), (upper, "upper", lower)):
        row = describe(ch)
        row.update(group=group, case=case, case_pair=pair)
        row.update(extra(ch, case))
        rows.append(row)
    return rows


def build():
    entries = []

    for i, lo in enumerate(ALPHABET_LOWER, start=1):
        entries += letter_pair(
            lo, "alphabet",
            lambda ch, case, i=i, lo=lo: {
                "alphabet_index": i,
                "key_handwritten_form": case == "lower" and lo in KEY_HANDWRITTEN,
            },
        )

    for ch, role, note in APOSTROPHES:
        row = describe(ch)
        row.update(group="apostrophe", case=None, role=role, note=note)
        entries.append(row)

    for ch, name, role, section, note in PUNCTUATION:
        row = describe(ch)
        row.update(group="punctuation", case=None, mark_name=name, role=role,
                   pravopys_section=section, note=note)
        entries.append(row)

    for lo, status, note in HISTORICAL:
        entries += letter_pair(
            lo, "historical",
            lambda ch, case, status=status, note=note: {
                "status": status, "note": note,
            },
        )

    for n, row in enumerate(entries, start=1):
        row["id"] = f"C{n:03d}"

    return {
        "inventory_version": INVENTORY_VERSION,
        "built": date.today().isoformat(),
        "unicode_version": unicodedata.unidata_version,
        "sources": {
            "alphabet": "Сучасна українська абетка, 33 літери",
            "apostrophe_punctuation": "Український правопис (2019): § 7, 138, 151 (апостроф); розд. V, § 155–168 (розділові знаки)",
            "historical": SOURCES_HISTORICAL,
            "key_handwritten_form": "Чинні прописи для 1 класу (обраний еталон)",
        },
        "groups": {
            "alphabet": "33 літери в обох регістрах (66 знаків)",
            "apostrophe": "Апостроф у трьох кодуваннях",
            "punctuation": "Розділові знаки правопису 2019; role=alternative — поширені кодові заміни",
            "historical": "status=core — названі в пропозиції; attested — засвідчені в системах XIX — поч. XX ст. (сторінки хрестоматії Німчука в note)",
        },
        "excluded_historical": EXCLUDED_HISTORICAL,
        "test_strings": {
            "quick": QUICK_TEST,
            "pangram": PANGRAM,
            "apostrophe_variants": " ".join(f"п{a}ять м{a}ята" for a, _, _ in APOSTROPHES),
            "punctuation_line": (
                "Він сказав: «Іди сюди — „зараз“ (не завтра)!» Що?! Ну… Ну... "
                "Добре, так; гаразд-гаразд [див. <…>] і/або “інше” „рукописне”."
            ),
            "historical_line": "сынъ свѣтъ ѳеодоръ ѵпостась ёго эхо jак ѱалтирь ꙋкраїна ѧкъ мо" + chr(0x0302) + "й до" + chr(0x0301) + "бре",
            "all_chars": "".join(e["char"] for e in entries),
        },
        "entries": entries,
    }


def validate(inv):
    e = inv["entries"]
    by = lambda g: [x for x in e if x["group"] == g]
    alpha = by("alphabet")
    assert len(alpha) == 66, len(alpha)
    assert len({x["char"] for x in alpha}) == 66
    assert all(len(x["char"]) == 1 for x in alpha)
    assert sum(x["key_handwritten_form"] for x in alpha) == len(KEY_HANDWRITTEN) == 9
    assert len(by("apostrophe")) == 3
    assert inv["test_strings"]["quick"][4] == chr(0x02BC)
    chars = [x["char"] for x in e]
    assert len(chars) == len(set(chars)), "дублікати в інвентарі"
    missing = set(ALPHABET_LOWER) - set(inv["test_strings"]["pangram"].lower())
    assert not missing, f"панграма не покриває: {missing}"
    punct = {x["char"] for x in by("punctuation")}
    missing = punct - set(inv["test_strings"]["punctuation_line"]) - {chr(0x2013), chr(0x2010), chr(0x0022)}
    assert not missing, f"рядок розділових знаків не покриває: {missing}"
    for x in e:  # кожен символ має назву в базі Unicode
        assert "<unnamed>" not in x["unicode_names"], x


if __name__ == "__main__":
    inv = build()
    validate(inv)
    OUT.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for x in inv["entries"]:
        key = x["group"] + (f"/{x['status']}" if x["group"] == "historical" else "")
        counts[key] = counts.get(key, 0) + 1
    print(f"{OUT.name}: {len(inv['entries'])} записів", counts, file=sys.stderr)
