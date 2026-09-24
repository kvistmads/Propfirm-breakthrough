# B4 kandidat 1 — trin 2, tillæg: implementeringsvalg og betingelser før kørslen

**Skrevet:** 2026-09-24 af overblikssessionen, efter Code's trin 1 (bygning, regressionstjek
og tidsmåling, commit ab05233) og **før** den rigtige kørsel. §1-§12 i `b4_k1_trin2.md` er
uændrede.

## 1. Code's syv læsninger — godkendt

Præregistreringen fastlagde ikke disse detaljer. Code valgte, oplyste og spurgte.

| nr | læsning | status |
|---|---|---|
| 1 | Westfall-Young: gentagelse r på spor A parres med gentagelse r på spor B, maksimum over de otte | Godkendt. Sporene har hver sit lysgitter, så parring efter gentagelsesnummer er den naturlige fælles fordeling |
| 2 | "Tvetydig" = stoppet ramt i en 1m-bar hvor også målet eller BE-triggeren kunne nås | Godkendt, det er §8's ordlyd |
| 3 | Bedste fald beholder motorrettelse 1: i fyldningsbaren tjekkes kun stoppet | Godkendt. §8 handler kun om regel 4 |
| 4 | Bedste fald vender også +1R om for `holder_pct` | Godkendt, det er en diagnose |
| 5 | N1's filtre regnes mod seriens egne strukturer; kun zonen er flyttet | Godkendt, det er §5's "samme kode på samme serie" |
| 6 | Klyngerobust = Liang-Zeger CR1 med G − 1 frihedsgrader | Godkendt |
| 7 | §7's tre rækker er udtømmende, så sætningen om den laveste kategori afgør intet | **Godkendt med præcisering:** række 2's egen CI-betingelse — CI-nedre > 0 — er den der gælder. Grænsen +0,20 R gælder punktestimatet. Hovedtestens p ≤ 0,025 én-sidet svarer til at det én-sidede 97,5%-interval for β ligger over 0 |

## 2. Fejl fundet af Code — trin A's resultater er uberørte

`research/b4_k1_trinA.py`'s `handler_for_variant` har berøringsbarens længde hårdkodet til
15 minutter (`k1.BAR`). Brugt på 5m-lys ville den lede efter fyldningen op til tre lys
frem — et kig frem. Trin A kørte kun 15m og er ikke påvirket. Trin 2 bruger sin egen vej,
`gennemloeb(..., bar_min)`, og rører ikke trin A's modul. En vagt i trin A's modul
tilføjes efter trin 2, ikke før.

## 3. Betingelser før den rigtige kørsel

1. **En test på 5m-lys.** Alle trin 2's tests kører på 15m. Spor B er halvdelen af testen,
   og netop berøringsbarens længde var fejlen. Testen skal vise på en syntetisk 5m-serie:
   (a) en gennemhandling i berøringslysets fem minutter giver fyldning; (b) en
   gennemhandling i sjette minut — det næste lys — fylder **ikke** denne berøring.
2. **Koden står fast.** Den rigtige kørsel sker fra ab05233 plus den nye test. Ændres noget
   i `research/*.py`, køres de tre regressionstjek i §10 igen, og ændringen oplyses i
   rapporten.
3. **Røgtesten oplyses.** Code kørte en røgtest med 5 gentagelser efter tidsmålingen.
   Rapporten skal sige om den skrev eller viste udfaldstal. De bruges ikke, og den rigtige
   kørsel ændres ikke på grundlag af dem.

## 4. Tidsmålingen — godkendt

R = 500. Forventet ca. 1,7 time på 4 arbejdere. Godkendt af ejeren og overblikssessionen.
