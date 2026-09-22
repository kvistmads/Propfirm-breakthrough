# B4 kandidat 1 — tillæg til præregistreringen af signaloptællingen

**Skrevet:** 2026-09-22, før kørslen. Committes før kørslen, sammen med koden.
**Hører til:** `research/prereg/b4_k1_optaelling.md` (commit 11d68f2).

Tillægget ændrer ingen definition. Det fastlægger implementeringsdetaljer der ikke står i
præregistreringen. Ét punkt kan i princippet flytte et signal, nemlig nabolys over et hul i
tid (§2). Dér er valget den bogstavelige læsning, og omfanget rapporteres.

---

## 1. Strukturtjek før kørslen, uden signaler

Serien er tjekket med `load_in_sample`, `aggregate(df, 15)` og `rth_mask`. Der er ikke
beregnet zoner, berøringer eller signaler.

| emne | fund |
|---|---|
| 1m-barer | 2.787.275, fra 2016-01-03 23:00 til 2023-12-29 21:59 UTC |
| 15m-barer | 187.558. 5,4% er bygget af færre end 15 1m-barer |
| Kontraktskift | 32, alle kl. 00:00 UTC (18:00 CST / 19:00 CDT) midt i Globex-sessionen, med 15 min mellem sidste gamle og første nye lys. Intet `instrument_id` vender tilbage |
| RTH-dage | 2.012 XNYS-dage. Åbner 08:30 CT alle dage. Lukker 15:00 CT (1.997 dage) eller 12:00 CT (15 halve dage) |
| RTH-dækning | Alle 2.012 dage har RTH-lys i data: 26 pr. dag, 14 på halve dage |
| Huller | 3.378 nabopar med mere end 15 min fra åbning til åbning. Heraf har 2.040 mindst en time fra det ene lys' lukning til det næstes åbning (dagligt stop, weekend, helligdag) |

## 2. Basislys og udbrudslys

- **"To på hinanden følgende 15m-lys" er to naboer i 15m-døgnserien.** `data.resample.aggregate`
  udelader tomme bins, så et hul i tid (dagligt stop, weekend, helligdag, en bin uden handel)
  bryder ikke naboskabet. Sådan viser et diagram serien, og §3 nævner kun kontraktskiftet
  som brud. Rapporten angiver hvor mange zoner og signaler der kommer fra par med et hul
  imellem.
- Lys bygget af færre end 15 1m-barer bruges som de er.
- **Basislys og udbrudslys i hver sin kontrakt:** parret opfylder definitionen og tælles i
  `zoner_dannet_n`, men zonen dør ved skiftet, altså ved udbrudslyset, før den bliver gyldig.
  Den tælles i `zoner_doede_ved_kontraktskift_n`. Antallet rapporteres, og det er højst 32.
  Intet signal kan komme fra et sådant par.

## 3. Zonens forløb

- **Kontraktskift:** zonen dør på det første lys efter basislyset hvis `instrument_id`
  afviger fra basislysets. Det lys vurderes ikke som berøring.
- Hver zone ender i præcis ét af tre forløb: berørt, død ved kontraktskift, eller åben ved
  in-sample-slut.
- **Berøringens tidspunkt** er berøringslysets åbningstid. **Signalets dag** er den dato
  i New York-tid, som i RTH er den samme som datoen i CT.
- **Dannet uden for RTH:** udbrudslyset er ikke et RTH-lys (`rth_mask`). Zonen findes fra
  udbrudslysets lukning, så det er udbrudslyset der afgør det. Basislys 08:15 CT og udbrudslys
  08:30 CT er dannet i RTH.
- **Zonealder:** fra udbrudslysets lukning (åbning + 15 min) til berøringslysets åbning, i
  timer på uret, weekender med. Kun signaler. Et berøringslys lige efter udbruddet giver 0.

## 4. Vinduet

Et lys er i vinduet når `rth_mask(t, 15)`, 08:30 ≤ t_CT < 14:30 og t < XNYS-luk − 30 min.
På almindelige dage siger de tre det samme. På halve dage slutter vinduet 11:30 CT. Tiden
regnes i America/Chicago.

## 5. Stoploftet og sizing

- `zonehoejde_pct` = (high − low) / basislysets close × 100, afrundet til 10 decimaler og
  holdt op mod ≤ 0,429. Afrundingen sikrer at en zone på præcis 0,429% i hele tick, fx 107,25
  point ved 25.000, ikke afvises på grund af afrundingsfejl i flydende tal.
- `zonehoejde_pt` = zonehoejde_pct / 100 × 29.138.
- `kontrakter` = floor(250 / (zonehoejde_pt × 2)), afrundet til 9 decimaler før floor, så
  62,5 point giver 2. Mellem 125/29.138 = 0,42899% og 0,429% giver formlen 0 kontrakter.
  Formlen bruges som skrevet, og antallet af sådanne signaler rapporteres.
- `omk_R_netto` = 2,627 / (2 × zonehoejde_pt). $2,627 er fase 2's rundtur for 1 MNQ i RTH.
  En test holder tallet op mod `config.yaml` via `backtest.costs`.
- `be_WR_pct_netto` = `research.stats.breakeven_win_rate(2, 1, omk_R_netto)` × 100, som er
  (1 + omk_R_netto) / 3 × 100. Regnes ved p50, som præregistreret, og desuden ved p90.

## 6. Nævnere

| andel | tæller | nævner |
|---|---|---|
| `dage_med_signal_pct` | RTH-dage med mindst ét signal | `RTH_dage_n` |
| `zoner_doede_ved_kontraktskift_pct` | zoner døde ved skift | `zoner_dannet_n` |
| `zoner_aldrig_beroert_pct` | zoner åbne ved in-sample-slut (censurerede) | `zoner_dannet_n` |
| `beroeringer_uden_for_vindue_pct` | berøringer uden for vinduet | alle berøringer |
| `afvist_af_stoploft_pct` | berøringer i vinduet med zonehøjde > 0,429% | berøringer i vinduet |
| `dannet_uden_for_RTH_pct` | signaler hvis udbrudslys ikke er et RTH-lys | signaler |

Zonerne der døde ved kontraktskift er også aldrig berørt. De står i egen række med samme
nævner, så begge læsninger af `zoner_aldrig_beroert` kan aflæses.

Hver andel får Wilson 95%-CI fra `research.stats.wilson_interval`. Rapporten viser én
decimal; csv'en har fuld præcision.

## 7. Percentiler

`numpy.percentile` med lineær interpolation, hver størrelse for sig. Derfor hører
`omk_R_netto_p90` til de mindste zoner. Zonehøjde, kontrakter, omk_R og zonealder regnes
kun over signaler. `signaler_pr_dag` regnes over alle RTH-dage, også dage uden signal.

## 8. RTH-dage og år

`RTH_dage_n` er XNYS-sessionerne dateret 2016-01-01 til 2023-12-31. Året i tabellen pr. år
er RTH-dagens år.

## 9. Beslutningsreglen

CI'et i dage er Wilson-grænserne × `RTH_dage_n`. Kategorien er den laveste CI'et rører,
altså kategorien for CI'ets nedre grænse. Rapporten siger om CI'et krydser en grænse.

## 10. Kørslen

- **Kun fra committet kode.** `main` stopper hvis en af disse ikke er committet eller er
  ændret: modulet, testene, præregistreringen, tillægget eller datalaget (`data/holdout.py`,
  `data/resample.py`, `data/sessions.py`, `research/stats.py`). Commit-hashes står i rapporten.
- **Én kørsel:** `.venv/bin/python -m research.b4_k1_optaelling --zoner <scratchpad>/b4_k1_zoner.parquet`.
- **Zonelisten** har én række pr. zone med tider, zonens kanter og forløb. Den skrives uden
  for repoet til gennemgangen, fordi den indeholder prisniveauer, og den committes ikke. Den
  indeholder ingen pris efter berøringslyset.
- **Output:** `research/output/b4_k1_optaelling.md` og `research/output/b4_k1_optaelling.csv`.
  CSV'en har hele perioden med alle nøgletal pr. side og hvert år med dagtallene pr. side.

## 11. Gennemgang efter kørslen

Resultatet gennemgås uden at ændre noget og uden at køre optællingen igen:

- De interne summer skal gå op. Forløbene summer til `zoner_dannet_n`, årene til helheden,
  og demand plus supply til alle.
- CI'erne regnes efter.
- En stikprøve af zoner holdes op mod 15m-lysene, kun fra basislyset til og med slutlyset.
