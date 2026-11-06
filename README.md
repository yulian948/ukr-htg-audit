# Аудит генерації українського рукописного тексту

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23942113.svg)](https://doi.org/10.5281/zenodo.23942113)

Код, зафіксовані версії й повні результати дослідження «Аудит методів генерації українського рукописного тексту та рукописних шрифтів» (Н. Е. Кунанець, Ю. Р. Баранецький).

Аудит перевіряє, на якому з чотирьох рівнів одинадцять реалізацій методів генерації рукописного тексту
(HTG) і 59 рукописних шрифтів утрачають символи сучасного українського та історичного письма:

1. **Кодування** — чи приймає модель символ (алфавіт, токенізатор).
2. **Конвеєр** — чи не вилучає символ код підготовки тексту.
3. **Впізнавана літера** — чи читається згенероване зображення як потрібна літера (сліпа оцінка).
4. **Форма за прописами** — чи відповідає форма літери шкільним прописам (для шрифтів).

*English summary.* Audit of Ukrainian handwritten text generation: at which of four levels
(encoding, text pipeline, recognisable letter, copybook letter form) eleven HTG implementations and 59
handwriting fonts lose characters of modern Ukrainian and historical Cyrillic script. All versions are pinned;
scripts point to the file and line of code where a character is lost.

## Основні результати

| Модель (рівень 3) | Сучасний алфавіт | Апостроф | ы ъ ѣ ѳ ѵ | Комбіновані знаки |
|---|---|---|---|---|
| Українська DiffusionPen | 90,9% | 83,3% | 12,5% | 72,9% |
| VATr з розширеним алфавітом | 44,7% | 33,3% | 10,0% | 27,1% |
| DiffusionPen (IAM) | 22,7% | 58,3% | 5,0% | 43,8% |
| Emuru | 0% | 0% | 0% | 0% |
| Eruku | 0,4% | 0% | 0% | 0% |

Частка зображень, оцінених як потрібна літера (428 зображень на модель). Сім із 11 реалізацій не приймають
кириличного тексту вже на рівнях 1–2. Повні зведення: `results/level12/summary.md`,
`results/level3/blind_summary.md`, `results/fonts/README.md`, `results/matrix/matrix.md`,
`results/matrix/recommendations.md`.

## Структура

| Тека | Що в ній |
|---|---|
| `inventory/` | Інвентар символів (131 запис): алфавіт, апострофи, розділові знаки, історичні літери |
| `versions/` | Що фіксуємо (`manifest.json`) і зафіксовані коміти й ревізії (`pinned.json`, станом на 23.10.2026) |
| `scripts/level12/` | Завантаження коду методів і зонди рівнів 1–2 |
| `scripts/level3/` | Слова, стилі, генерація п'ятьма моделями, контроль «латиниця/кирилиця», сліпий набір |
| `scripts/fonts/` | Відбір шрифтів Google Fonts, покриття інвентарю, OpenType-варіанти Kobzar KS |
| `scripts/coding/` | Комплекти для кодування й сліпої оцінки, каппа Коена, консенсус, зведення рівня 3 |
| `scripts/build_matrix.py` | Матриця «вимога × метод/шрифт» за правилами Р1–Р8 |
| `checkpoints/` | На чому навчено кожен checkpoint (з посиланнями на джерела) |
| `coding_kit/` | Інструкції для кодувальників і ключі (номер → шрифт/модель) |
| `level3/` | Слова (`words.json`) і метадані стилів (`styles/styles.json`) |
| `results/` | Повні результати всіх кроків |
| `notebooks/ukr_htg_audit_colab.ipynb` | Увесь код у вигляді блокнота Google Colab (крок 7 — на GPU) |

## Відтворення

Python 3.12, залежності — `requirements-audit.txt`. Код методів, ваги й шрифти скрипти завантажують самі в
`~/.cache/ukr-htg-audit/work` (змінна `AUDIT_WORK`) на зафіксованих ревізіях.

```bash
pip install -r requirements-audit.txt
python3 inventory/build_inventory.py          # крок 1
python3 scripts/level12/fetch_sources.py      # код методів на зафіксованих комітах
python3 scripts/level12/run_level12.py        # крок 3: рівні 1–2 (CPU)
python3 scripts/render_training_data.py       # крок 4
python3 scripts/fonts/select_fonts.py && python3 scripts/fonts/fetch_fonts.py
python3 scripts/fonts/audit_fonts.py && python3 scripts/fonts/kobzar_opentype.py   # крок 5
python3 scripts/build_matrix.py               # крок 8
```

Крок 7 (рівень 3) потребує GPU: відкрийте `notebooks/ukr_htg_audit_colab.ipynb` у Google Colab (T4) і
виконайте клітинки за порядком. Emuru й Eruku запускаються з окремих середовищ із версіями бібліотек з їхніх
репозиторіїв (transformers 4.5x); для Eruku довжину генерації обмежено 64 кроками (відхилення описано в
`scripts/level3/generators.py`). Початкове значення генератора випадкових чисел зафіксовано для кожного
зображення.

## Що не входить до репозиторію

- **Шрифти та зображення їхніх гліфів.** Ліцензія Kobzar KS забороняє модифікацію й розбір шрифту, а її п. 3.2
  про використання ШІ неоднозначний; шрифти ukrainian-handwriting-synth і doc_gen ліцензій не мають. Скрипти завантажують шрифти з
  першоджерел і звіряють контрольні суми.
- **Ваги моделей і згенеровані зображення.** Ваги завантажуються з Hugging Face і Google Drive на зафіксованих
  ревізіях; у ваг української DiffusionPen ліцензії немає.
- **Зразки почерку UkrHandwritten** — `scripts/level3/prepare_styles.py` завантажує їх зі Space
  `kdonitz/diffusionpen-ukrainian`.
- **Сторінки прописів** (авторське право) і бланки з вбудованими зображеннями; оцінки подано у CSV:
  `results/fonts/step6_coding.csv`, `results/fonts/step6_final.csv`, `results/level3/blind_rows.csv`.
- **Текст статті** — до публікації.

## Ліцензії

- Код — MIT (`LICENSE`).
- Інвентар, результати, матриця, інструкції й оцінки — CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
- Сторонні матеріали (код методів, ваги, шрифти, набори даних) — на умовах їхніх власників; ліцензії
  зафіксовано у `versions/pinned.json` і `results/fonts/README.md`.

## Автори

Наталія Кунанець, Юліан Баранецький — Національний університет «Львівська політехніка».
