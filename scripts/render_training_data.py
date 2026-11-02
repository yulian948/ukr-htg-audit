"""Таблиця кроку 4 з checkpoints/training_data.json → checkpoints/training_data.md."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "checkpoints" / "training_data.json"
OUT = SRC.with_suffix(".md")


def cell(value):
    if isinstance(value, list):
        return "<br>".join(value)
    return (value or "—").replace("|", "\\|")


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    lines = ["# Крок 4. На чому навчено кожен checkpoint", "", data["about"], "",
             "| Метод | Checkpoint | Навчальні дані | Мова | Етапи навчання | Зразки стилю | Джерела |",
             "|---|---|---|---|---|---|---|"]
    notes = []
    for m in data["methods"]:
        lines.append("| " + " | ".join(cell(m.get(k)) for k in
                     ("method", "checkpoint", "datasets", "language", "stages", "style_refs", "sources")) + " |")
        for key, label in (("conflicts", "Розбіжність"), ("gaps", "Не з'ясовано"), ("punctuation", "Розділові знаки"),
                           ("historical_letters", "Історичні літери"), ("data_filters", "Фільтри даних"),
                           ("text_encoder_pretraining", "Текстовий енкодер"), ("text_representation", "Подання тексту"),
                           ("content_text", "Текст для генерації")):
            if m.get(key):
                notes.append(f"- **{m['method']} — {label}:** {cell(m[key]).replace('<br>', '; ')}")
    lines += ["", "## Примітки", ""] + notes
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
