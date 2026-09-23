# B4 kandidat 1 — præregistrering: signaloptælling

**Skrevet:** 2026-09-22, før kørslen. Committes før kørslen (metoderegel 13).
**Grundlag:** `research/output/b4_hypoteser.md`, kandidat 1, kernen. Beslutningsreglen er
godkendt af ejeren 2026-09-22.

---

## 1. Hvad kørslen er, og hvad den ikke er

Kørslen **tæller signaler**. Den svarer på ét spørgsmål: hvor mange handelsdage har mindst
ét signal fra kernen? Svaret afgør mindste detekterbare forskel (MDE) for edge-testen.

Kørslen **ser ikke på udfald.** Den må ikke beregne eller gemme noget om prisen efter
berøringen: ingen gevinst eller tab, ingen MFE/MAE, intet om hvorvidt målet eller stoppet
blev ramt først. Derfor lægger den intet til tælleren for den deflaterede tærskel.

Én kørsel. Ingen justering af definitionerne undervejs.

## 2. Data

| emne | valg |
|---|---|
| Serie | `data.holdout.load_in_sample("NQ.v.0")` — 2016-01-01 til 2023-12-31, 1m, UTC |
| 15m | `data.resample.aggregate(df, 15)` |
| RTH | `data.sessions.rth_mask` (NYSE-kalenderen, halve dage med) |
| Zoner | Dannes på hele døgnserien |
| Prisniveau | Højder i procent, omregnet til point ved NQ 29.138 |

Koden ligger i `research/b4_k1_optaelling.py` og henter pris **kun** gennem
`data/holdout.py`. `tests/test_holdout.py` håndhæver det.

## 3. Definitioner

- **Basislys og udbrudslys:** to på hinanden følgende 15m-lys. Demand: basislyset har
  close < open, og udbrudslyset har close > basislysets high. Supply: basislyset har
  close > open, og udbrudslyset har close < basislysets low. Lys med close = open er
  hverken rødt eller grønt og kan ikke være basislys.
- **Zone:** basislysets high til low, væger medregnet. Gyldig fra udbrudslysets lukning.
- **Berøring:** første 15m-lys efter udbrudslyset hvor demand: low ≤ zonens high, supply:
  high ≥ zonens low. Berøres zonen, dør den — uanset tidspunkt.
- **Kontraktskift:** skifter `instrument_id` mellem zonens basislys og et senere lys, dør
  zonen ved skiftet uden berøring.
- **Signal:** en berøring hvor lysets åbningstid ligger i vinduet 08:30 ≤ t < 14:30 CT
  (15:30-21:30 dansk tid) på en RTH-dag, og zonehøjden er ≤ 0,429% af basislysets close.
  På halve dage slutter vinduet 30 minutter før RTH lukker.
- En berøring uden for vinduet er **ikke** et signal, men zonen er stadig brugt.
- Demand og supply tælles begge. Flere signaler samme dag tælles hver for sig, men
  beslutningen hviler på dage med mindst ét.

## 4. Rapport

Kompakt tabel i chatten. Hver andel med Wilson 95%-CI.

| kolonne | formel |
|---|---|
| RTH_dage_n | antal RTH-dage in-sample |
| dage_med_signal_n | dage med ≥ 1 signal |
| dage_med_signal_pct | dage_med_signal_n / RTH_dage_n |
| signaler_pr_dag_p50, _p90 | fordelingen over RTH-dage |
| zoner_dannet_n | alle zoner, demand og supply hver for sig |
| zoner_doede_ved_kontraktskift_n | — |
| zoner_aldrig_beroert_pct | censureret ved in-sample-slut |
| beroeringer_uden_for_vindue_pct | — |
| afvist_af_stoploft_pct | signaler i vinduet med zonehøjde > 0,429% |
| zonehoejde_pt_p10/_p50/_p90 | højde% × 29.138, kun signaler |
| kontrakter_p10/_p50/_p90 | `floor(250 / (zonehoejde_pt × 2))` |
| omk_R_brutto / omk_R_netto | 0 / `2,627 / (2 × zonehoejde_pt)`, p10/p50/p90 |
| be_WR_pct_brutto / _netto | 33,33 / `(1 + omk_R_netto) / 3 × 100` ved p50 |
| zonealder_timer_p50/_p90 | fra udbrudslysets lukning til berøringen |
| dannet_uden_for_RTH_pct | andel af signalerne |

Og én tabel pr. år, 2016-2023: `dage_med_signal_pct` med CI, så stabiliteten kan ses.

## 5. Beslutningsregel

Godkendt af ejeren 2026-09-22 som andele af dagene, regnet på 1.173 dage (vinduet fra
2019). Med in-sample fra 2016 er der 2.012 dage, så reglen står her i **antal dage med
signal** — det er det tal MDE hviler på. Logikken er uændret: 390 handler skal til for at
skelne 40% fra 33,97% win rate (α 0,05 ensidet, 80% styrke), og 590 giver plads til en
filtersøgning.

| dage_med_signal_n | andel af 2.012 dage | betyder | vi gør |
|---|---|---|---|
| ≥ 590 | ≥ 29,3% | Testbar, også med filtersøgning | Edge-testen præregistreres |
| 390-589 | 19,4-29,3% | Kernen alene er testbar | Kun kernen testes, ingen filtersøgning |
| < 390 | < 19,4% | For få handler til at se 40% WR | Kandidaten parkeres |

**Krydser konfidensintervallet en grænse, er resultatet uafgjort mellem to kategorier, og
den laveste gælder.**

## 6. Forventning, skrevet før kørslen

Ikke et kriterium, men et tjek af om definitionerne opfører sig som tænkt. Pivot-zoner på
15m uden filtre er almindelige. **Forventningen er at langt de fleste RTH-dage har et
signal — over 70%.** Ligger tallet langt under, er det et tegn på at en definition er
strammere end ment, og det læses sammen før noget ændres.

## 7. Efter kørslen

Stop. Tabellen i chatten, ingen ændring af definitioner, ingen forslag. Resultatet læses
sammen med ejeren.
