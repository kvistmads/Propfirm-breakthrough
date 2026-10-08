# B4 kandidat 4 — EMT, læst: kandidat 4 parkeres

**Skrevet:** 2026-10-08 af overblikssessionen, efter kørslen og læst sammen med ejeren.
Tallene står i `b4_k4_emt.md` og `.csv` (commit 0291052, kørt fra 3d9c62f). Intet er
kørt igen.

## 1. Kan vi stole på tallene?

| tjek | resultat |
|---|---|
| Rækkefølgen af commits | præregistrering ce84560 → kode b9fb769 → optælling a24834a → tillæg 39cdc48 → N-tid-rettelse 3d9c62f → kørsel 0291052 |
| Kodeændring efter optællingen | kun N-tid's matching i `b4_k4_emt.py` og tests til den, som tillægget tillod |
| Regressionstjek | OK. Hele testsuiten: 1.032 bestået, 6 sprunget over |
| N-tid's tidsprofil efter rettelsen | median kl. 09:45–10:55 CT mod modellens 09:40–10:55. 0 handler blev matchet til en nabotime |
| Tvetydige minutter og censurering | 0–2 tvetydige pr. variant, 0 censurerede. I bedste fald gælder samme række |
| Code's egen fejl i §8-tabellen | Code læste først intervallets øvre grænse som den nedre og rettede det selv. Højeste CI-nedre er −0,188 |

## 2. Afgørelsen efter §8: række 4, kandidat 4 parkeres

| variant | handler_n | RR_p50 | middel_R_brutto | middel_R_netto | CI95_netto | win_rate_pct_netto | maal_stop_tid_pct | N_tid_p50_R_netto | p_FWE |
|---|---|---|---|---|---|---|---|---|---|
| k = 1,5 · 1/dag | 1.104 | 2,68 | −0,006 | −0,092 | [−0,188; +0,004] | 30,9 | 30 / 69 / 2 | −0,130 | 0,30 |
| k = 1,5 · 2/dag | 1.988 | 3,02 | −0,077 | −0,170 | [−0,245; −0,096] | 27,4 | 25 / 72 / 3 | −0,200 | 0,29 |
| k = 2,0 · 1/dag | 1.049 | 3,07 | −0,028 | −0,117 | [−0,219; −0,014] | 28,4 | 27 / 71 / 3 | −0,146 | 0,53 |
| k = 2,0 · 2/dag | 1.809 | 3,52 | −0,111 | −0,205 | [−0,283; −0,126] | 24,7 | 22 / 74 / 4 | −0,222 | 0,72 |
| k = 3,0 · 1/dag | 840 | 4,23 | −0,058 | −0,150 | [−0,275; −0,025] | 24,9 | 20 / 74 / 6 | −0,204 | 0,19 |
| k = 3,0 · 2/dag | 1.349 | 4,65 | −0,139 | −0,236 | [−0,336; −0,137] | 21,6 | 16 / 77 / 7 | −0,233 | 1,00 |

- **Alle 6 varianter er negative netto.** Ingen har CI-nedre over 0, og ingen slår et
  tilfældigt strakt lys i samme time signifikant.
- **Brutto ligger modellen mellem −0,01 og −0,14 R.** Selv før omkostninger er der intet.

## 3. Tilbage eller videre (N-mod)

| variant | N_mod_middel_R_netto | forskel_N_mod_minus_model [Welch-CI95] |
|---|---|---|
| k = 1,5 · 1/dag | −0,054 | +0,038 [−0,125; +0,201] |
| k = 1,5 · 2/dag | −0,091 | +0,080 [−0,051; +0,210] |
| k = 2,0 · 1/dag | −0,008 | +0,109 [−0,067; +0,284] |
| k = 2,0 · 2/dag | −0,069 | +0,135 [−0,008; +0,279] |
| k = 3,0 · 1/dag | +0,041 | +0,190 [−0,028; +0,409] |
| k = 3,0 · 2/dag | −0,006 | +0,231 [+0,047; +0,415] |

- **At handle med strækket er bedre end at handle imod det i alle 6 varianter,** og mere
  jo større strækket er.
- **Det er ikke et in-sample-fund efter §8.** N-mod's eget interval krydser 0 i alle
  varianter, og N-mod ligger selv omkring 0.
- **Retningen passer med Zarattini og Aziz:** prisen fortsætter væk fra VWAP oftere, end
  den vender tilbage.

## 4. Hvad vi lærte — til de næste kandidater, ikke til at redde denne

- **Elastikken holder ikke på MNQ 5m.** Ved et stræk på 1,5–3 ATR fra VWAP rammes stoppet
  bag udmattelseslyset i 69–77% af handlerne, og VWAP-målet nås i 16–30%.
- **Vægen betyder lidt, men ikke nok:** udmattelseslyset slog et tilfældigt strakt lys i
  samme time med t = 0,8–1,8, ikke signifikant, og begge er negative.
- **Dagens anden handel trækker ned:** 2/dag-varianterne er 0,08–0,09 R ringere end
  1/dag.
- **Long er bedre end short** (0,05–0,19 R). Short-siden taber mest, hvilket passer med en
  stigende Nasdaq i perioden.
- **Fire kandidater peger samme vej.** Når prisen har bevæget sig kraftigt og når et niveau
  igen, eller er strakt væk fra gennemsnittet, går den lidt oftere videre end tilbage.
  - Kandidat 1: strukturbrud trak ned.
  - Kandidat 2: lys uden væge brydes.
  - Kandidat 4: N-mod er bedre end modellen.
  - Det er ingen edge i sig selv, for alt ligger omkring 0 netto. Men det taler for at
    teste fortsættelse frem for tilbageløb, og det er det, kandidat 5 gør.

## 5. Status

| emne | status |
|---|---|
| Kandidat 4 | **Parkeret** 2026-10-08 |
| Tælleren | 37 forsøg; følger med til næste kandidat |
| Holdout (2024 →) | uåbnet og ukøbt for MNQ |
| Kandidat 5 | udkast klar (`research/prereg/b4_k5_vwap_trend_udkast.md`), afventer ejerens svar |
