# Крок 5: покриття інвентарю шрифтами

ok — символ є в cmap і має гліф; missing — немає в cmap (рендериться .notdef); empty_glyph — у cmap є, але гліф порожній. Повні дані — coverage.json/csv, аркуші — sheets/.

| ID | Шрифт | Джерело | alphabet | apostrophe | punctuation | historical | ґєії | ʼ U+02BC | Не ok |
|---|---|---|---|---|---|---|---|---|---|
| F001 | Amatic SC | google_fonts | 66/66 | 3/3 | 23/24 | 24/38 | 8/8 | так | ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F002 | Bad Script | google_fonts | 66/66 | 3/3 | 23/24 | 30/38 | 8/8 | так | ‐ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F003 | Caveat | google_fonts | 66/66 | 3/3 | 24/24 | 30/38 | 8/8 | так | ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F004 | Comforter | google_fonts | 66/66 | 3/3 | 24/24 | 24/38 | 8/8 | так | ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F005 | Comforter Brush | google_fonts | 66/66 | 3/3 | 24/24 | 24/38 | 8/8 | так | ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F006 | Great Vibes | google_fonts | 66/66 | 3/3 | 24/24 | 26/38 | 8/8 | так | ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F007 | Hachi Maru Pop | google_fonts | 58/66 | 2/3 | 23/24 | 12/38 | 0/8 | ні | ґ Ґ є Є і І ї Ї ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ … (+12) |
| F008 | Klee One | google_fonts | 58/66 | 3/3 | 24/24 | 24/38 | 0/8 | так | ґ Ґ є Є і І ї Ї ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F009 | LXGW WenKai TC | google_fonts | 66/66 | 3/3 | 24/24 | 30/38 | 8/8 | так | ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F010 | Marck Script | google_fonts | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F011 | Neucha | google_fonts | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F012 | Pacifico | google_fonts | 66/66 | 3/3 | 23/24 | 30/38 | 8/8 | так | ‐ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F013 | Pangolin | google_fonts | 66/66 | 3/3 | 24/24 | 30/38 | 8/8 | так | ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F014 | Playpen Sans | google_fonts | 66/66 | 3/3 | 23/24 | 24/38 | 8/8 | так | ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F015 | Yomogi | google_fonts | 58/66 | 3/3 | 23/24 | 24/38 | 0/8 | так | ґ Ґ є Є і І ї Ї ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F016 | Shantell Sans | google_fonts_classification | 66/66 | 3/3 | 24/24 | 30/38 | 8/8 | так | ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ |
| F017 | Kobzar KS | kobzar | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F018 | Abram | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F019 | AdventureC - AdventureC - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F020 | AllegrettoScriptOneC - Allegretto Script OneC - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F021 | AllegrettoScriptTwoC - Allegretto Script TwoC - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F022 | AllegroScript - AllegroScript - Italic | ukrainian-handwriting-synth | 66/66 | 2/3 | 22/24 | 12/38 | 8/8 | ні | ʼ ? ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F023 | AnastasiaScript - AnastasiaScript - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 22/24 | 12/38 | 8/8 | ні | ʼ ? ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F024 | AnastasiaScriptC - AnastasiaScriptC - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 22/24 | 12/38 | 8/8 | ні | ʼ ? ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F025 | Anselmo | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F026 | Benvolio | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F027 | Blink-Script | ukrainian-handwriting-synth | 66/66 | 1/3 | 15/24 | 24/38 | 8/8 | ні | ʼ ’ — – … « » „ “ ” ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ … (+1) |
| F028 | Capuletty | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F029 | Celestina | ukrainian-handwriting-synth | 66/66 | 3/3 | 23/24 | 12/38 | 8/8 | так | ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ а́ … (+3) |
| F030 | Djiovanni | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 8/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ j J ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ … (+8) |
| F031 | EnglishScript - English Script - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 24/24 | 12/38 | 8/8 | ні | ʼ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ а́ … (+3) |
| F032 | Eskal | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F033 | Gogol - Gogol - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 15/24 | 9/38 | 8/8 | ні | ʼ ? ( ) < > « » " ‐ Ѣ ѳ Ѳ ѵ Ѵ j J ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ … (+15) |
| F034 | Gogol | ukrainian-handwriting-synth | 66/66 | 2/3 | 15/24 | 9/38 | 8/8 | ні | ʼ ? ( ) < > « » " ‐ Ѣ ѳ Ѳ ѵ Ѵ j J ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ … (+15) |
| F035 | Gregory | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F036 | Lemon-Tuesday | ukrainian-handwriting-synth | 66/66 | 3/3 | 23/24 | 12/38 | 8/8 | так | ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ а́ … (+3) |
| F037 | Lorenco | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F038 | LudvigvanBethoveen - Ludvig van Bethoveen - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 24/24 | 12/38 | 8/8 | ні | ʼ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ а́ … (+3) |
| F039 | Merkucio | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F040 | Montekky | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F041 | NinaC | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F042 | NinaCTT - NinaCTT - Normal | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F043 | PFScandalPro-Reg | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F044 | Pag | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F045 | Paris | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F046 | Pinata-Celestina | ukrainian-handwriting-synth | 66/66 | 3/3 | 23/24 | 12/38 | 8/8 | так | ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ а́ … (+3) |
| F047 | Samson | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 8/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ j J ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ … (+8) |
| F048 | ShellyAllegroC - ShellyAllegroC - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 22/24 | 12/38 | 8/8 | ні | ʼ ? ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F049 | StudioScriptC | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F050 | Tibalt | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 11/38 | 8/8 | ні | ʼ ‐ Ъ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ … (+5) |
| F051 | UkrainianChance - UkrainianChance - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F052 | WolfgangAmadeusMozart - Wolfgang Amadeus Mozart - Regular | ukrainian-handwriting-synth | 66/66 | 2/3 | 23/24 | 12/38 | 8/8 | ні | ʼ / ѣ Ѣ ѳ Ѳ ѵ Ѵ ѯ Ѯ ѱ Ѱ ꙋ Ꙋ ѧ Ѧ о̂ О̂ е̂ Е̂ у̂ У̂ и̂ И̂ … (+4) |
| F053 | Finding_Beauty | doc_gen | 0/66 | 3/3 | 23/24 | 4/38 | 0/8 | так | а А б Б в В г Г ґ Ґ д Д е Е є Є ж Ж з З и И і І … (+77) |
| F054 | LITERPLA | doc_gen | 58/66 | 2/3 | 23/24 | 10/38 | 0/8 | ні | ґ Ґ є Є і І ї Ї ʼ ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ ё Ё ѯ Ѯ ѱ Ѱ ꙋ Ꙋ … (+14) |
| F055 | Melon_Font_-_Free_Trial | doc_gen | 0/66 | 1/3 | 17/24 | 4/38 | 0/8 | ні | а А б Б в В г Г ґ Ґ д Д е Е є Є ж Ж з З и И і І … (+85) |
| F056 | comic | doc_gen | 0/66 | 2/3 | 19/24 | 4/38 | 0/8 | ні | а А б Б в В г Г ґ Ґ д Д е Е є Є ж Ж з З и И і І … (+82) |
| F057 | gtw | doc_gen | 58/66 | 1/3 | 18/24 | 23/38 | 0/8 | ні | ґ Ґ є Є і І ї Ї ʼ ’ — – … « » ‐ ѣ Ѣ ѳ Ѳ ѵ Ѵ Ё ѯ … (+7) |
| F058 | koala | doc_gen | 0/66 | 1/3 | 23/24 | 4/38 | 0/8 | ні | а А б Б в В г Г ґ Ґ д Д е Е є Є ж Ж з З и И і І … (+79) |
| F059 | luckytw | doc_gen | 0/66 | 2/3 | 21/24 | 4/38 | 0/8 | ні | а А б Б в В г Г ґ Ґ д Д е Е є Є ж Ж з З и И і І … (+80) |
