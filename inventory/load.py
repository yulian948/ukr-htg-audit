"""Спільний завантажувач інвентарю для скриптів аудиту."""

import json
from pathlib import Path

PATH = Path(__file__).with_name("charset_inventory.json")


def load_inventory(groups=None, path=PATH):
    """Повертає (метадані, записи).

    groups — набір груп (alphabet, apostrophe, punctuation, historical) або None для всіх.
    """
    inv = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = [e for e in inv["entries"] if groups is None or e["group"] in groups]
    return inv, entries
