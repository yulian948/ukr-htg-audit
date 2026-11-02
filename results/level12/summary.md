# Рівні 1–2: зведення

Частка символів інвентарю зі статусом ok за групами. Повні дані — symbol_x_method.csv і <метод>.json.

| Метод | Шлях | alphabet | apostrophe | punctuation | historical | Де губиться |
|---|---|---|---|---|---|---|
| GANwriting | tt.test_single_writer.4_scenarios.py → label_padding | 0/66 | 0/3 | 0/24 | 4/38 | load_data.py:171 |
| HiGAN+ | networks/model.py eval_style/eval_rand → strLabelConverter.encode | 0/66 | 1/3 | 11/24 | 4/38 | lib/alphabet.py:65 |
| HWT | mytext.txt → util/models/model.py:520 → strLabelConverter.encode | 0/66 | 1/3 | 11/24 | 4/38 | util/models/OCR_network.py:261 |
| VATr | generator.py → netconverter.encode | 0/66 | 1/3 | 11/24 | 4/38 | models/OCR_network.py:265 |
| VATr | mytext.txt → models/model.py:410 → netconverter.encode | 0/66 | 1/3 | 11/24 | 4/38 | models/model.py:410 |
| VATr | гліфи files/unifont.pickle | 66/66 | 3/3 | 24/24 | 38/38 |  |
| VATr++ | generate.py → generate/writer.py:70 → netconverter.encode | 0/66 | 1/3 | 11/24 | 4/38 | generate/writer.py:70 |
| VATr++ | гліфи blowing-up-groundhogs/vatrpp: files/unifont.pickle | 66/66 | 3/3 | 24/24 | 38/38 |  |
| One-DM | test.py → ContentData.get_content | 0/66 | 1/3 | 11/24 | 4/38 | data_loader/loader.py:260 |
| One-DM | гліфи English_data.zip: unifont.pickle | 66/66 | 3/3 | 24/24 | 38/38 |  |
| WordStylist | sampling.py → train.py:189 label_padding | 0/66 | 0/3 | 0/24 | 4/38 | train.py:32 |
| DiffusionPen | train.py --train_mode sampling → Diffusion.sampling → CanineTokenizer | 66/66 | 3/3 | 24/24 | 38/38 |  |
| Українська DiffusionPen | CanineTokenizer (кодування окремого символу) | 66/66 | 3/3 | 24/24 | 38/38 |  |
| Українська DiffusionPen | app.py:246 generate → punct_bank / CANINE | 66/66 | 2/3 | 16/24 | 38/38 | app.py:324 |
| Emuru | models/emuru.py generate → tokenizer(style_text + ' ' + gen_text) | 66/66 | 3/3 | 24/24 | 38/38 |  |
| Eruku | eruku_continuous_inf.py generate → tokenizer(f'{style}<sog>{gen}') | 66/66 | 3/3 | 24/24 | 38/38 |  |
| Eruku (aimagelab, версія пропозиції) | eruku_continuous_inf.py generate → tokenizer(f'{style}<sog>{gen}') | 66/66 | 3/3 | 24/24 | 38/38 |  |
