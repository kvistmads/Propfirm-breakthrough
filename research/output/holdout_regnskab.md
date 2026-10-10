# Holdout-regnskab — hvad er set, og hvad er stadig rent

**Oprettet:** 2026-10-10 af overblikssessionen (ejerens svar 2A). Opdateres ved hver åbning
af holdout og hver gang nye data købes.

**Reglen:** hver ny præregistrering skriver, hvilke data den tester på, og hvorfor de er
rene for netop den idé, med henvisning til dette dokument. "Set" betyder, at resultater fra
perioden er rapporteret for en bestemt slags idé. Dataene er ikke ødelagte. De kan bare
ikke længere bevise noget for idéer, der ligner det, vi har set.

**Skillelinjen** (`data/holdout.py`): in-sample 2016-01-01 → 2023-12-31, holdout fra
2024-01-01. Fase 1 og 2 brugte 2016–2026 til ATR-fordelingen og spreadet. Det var
beskrivende målinger uden signaler eller udfald.

## 1. Holdout 2024 og frem

| data | lokalt | åbnet | hvad er set | ikke længere rent for | stadig brugbart til |
|---|---|---|---|---|---|
| **MNQ.v.0** 1m | 2024-01-01 → 2026-10-01 | 1 gang, 2026-10-08, `b4_k5_holdout.md` | Kun RTH: VWAP-retningen (1m · uden middag), brutto pr. halve time i RTH, altid-long i RTH, long mod short | VWAP-trend og intradag-momentum i RTH. Retning og drift i RTH pr. halve time på MNQ og NQ (samme kurs) | Natten. Andre RTH-idéer med en note om, hvad der er set |
| **NQ.v.0** 1m | 2024-01-01 → 2026-10-01 | 1 gang, 2026-10-10, `b4_k6_holdout.md` | Kun natten: long 00:30–02:30 CT efter salgsdage (V2 · salg), tilfældige 2-timersvinduer på salgsnætter (nulmodellen), pr. år og koncentration (april 2025). RTH-tallene fra kandidat 5 gælder også NQ (samme kurs) | Natdrift efter salgsdage og natdrift i 2-timersvinduer på salgsnætter. Som MNQ for RTH | Natidéer på bestemte nætter (fx før optionsudløb eller FOMC), med en note. Long hele natten og nætter uden salg er ikke rapporteret |
| **ES.v.0** 1m | 2024-01-01 → 2026-10-01 | 1 gang, 2026-10-10, `b4_k7_holdout.md` | T's resultat over Topstep-dagen, long hele Topstep-dagen, brutto nat og RTH for T, urolige måneder, ES' dagsafkast mod næste dag (reversal) | Rebalancering, kortsigtet reversal, drift over hele dagen og natdrift på ES generelt | Idéer på bestemte dage eller begivenheder (fx optionsudløb, FOMC), med en note |
| **ZN.v.0** 1m | 2024-01-01 → 2026-10-01 | 1 gang, sammen med ES | Kun brugt til T's signal og som kontrol i reversal-regressionen | Aktie-mod-obligations-signaler | ZN's egne mønstre, med en note |

## 2. Data, ingen har set

| data | status | pris, cirka |
|---|---|---|
| Alle instrumenter **før 2016** (Databento fra 2010-06-06) | ikke købt, aldrig set | $1,3–1,7 pr. år pr. instrument i ohlcv-1m |
| **Andre markeder**: MGC (guld), MCL (olie), M6E (euro), YM, RTY | ikke købt | som ovenfor |
| **Ny data fra 2026-10-01 og frem** | ren for alt | gratis at vente på, men langsom |

## 3. In-sample 2016–2023

Set mange gange. Hvert forsøg står i tælleren (47 pr. 2026-10-10). In-sample bruges til at
finde og måle, aldrig som bevis for en edge.

## 4. Log over åbninger

Den maskinelle log står i `research/output/holdout_log.md`. Én åbning kan give flere
linjer, én pr. symbol.

| dato | frosset hypotese | symboler | udfald |
|---|---|---|---|
| 2026-10-08 | `b4_k5_holdout.md` (VWAP-trend) | MNQ.v.0 | række 4, parkeret |
| 2026-10-10 | `b4_k7_holdout.md` (rebalancering, T) | ES.v.0, ZN.v.0 | række 4, parkeret |
| 2026-10-10 | `b4_k6_holdout.md` (overnight drift efter salgsdage) | NQ.v.0 | række 4, parkeret for godt |
