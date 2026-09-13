# Fase 1 — efterskrift

**Skrevet:** 2026-09-13 af fasesessionen, efter at fasen var afsluttet.

**Hvad det er:** den viden om repoet og apparatet som fase 1 gav, men som ikke stod i nogen
fil: ikke i `datakilder.md`, `atr_fordeling.md`, `ANTAGELSER.md`, docstrings eller
commit-beskeder. Punkterne er ordnet efter konsekvens.

**Hvad det ikke er:** ingen tal i fasens rapporter er ændret, ingen kode er rettet, og der
er ingen forslag. Punkt 1-4 er efterprøvet igen 2026-09-13. Resten stammer fra
fasesessionen 2026-09-11.

---

## 1. Fejl og fælder i koden

### 1.1 Backtesten regner dyrere end $2,47

`backtest/costs.py` trækker slippage pr. side som `max(0, N(0,5; 0,5))` tick. Afskæringen er
dokumenteret, men ikke konsekvensen: **middelværdien bliver 0,54 tick pr. side, ikke 0,50.**

| grundlag | slippage_ticks_pr_side | omk_usd_rundtur | omk_R_netto ved 15m RTH p50 |
|---|---|---|---|
| middel i `config.yaml` (§4, `atr_fordeling.omk_usd_rundtur`) | 0,50 | 2,47 | 0,0183 |
| hvad `apply_costs` faktisk trækker | 0,5417 | 2,51 | 0,0186 |
| faktisk slippage + målt MNQ-spread, RTH (1,73 tick) | 0,5417 | 2,63 | 0,0194 |
| faktisk slippage + målt MNQ-spread, uden for RTH (2,17 tick) | 0,5417 | 2,84 | 0,0210 |

Middelværdien er beregnet analytisk, E[max(0, X)] = μΦ(μ/σ) + σφ(μ/σ), og bekræftet med 2 mio.
træk (0,5419). R er regnet ved 15m RTH-ATR p50 0,2319% (2016-2026) og NQ 29.138.

**Konsekvens:** §4's række "som koden faktisk regner" ($2,47) er ikke hvad koden trækker.
`backtest.costs.cost_summary` rapporterer også middelværdien før afskæring.

### 1.2 NYSE-kalenderen følger kørselsdatoen

`exchange_calendars` bygger XNYS fra **20 år før til ét år efter den dag koden kører**. Kørt
2026-09-13: første session 2006-09-13, sidste 2027-09-13.

Uden for vinduet giver `data.sessions.rth_mask` `False` uden fejl. Hver bar bliver ETH.
Efterprøvet: fredag 2006-09-08 15:00 UTC, en almindelig handelsdag, markeres ETH.

**Konsekvens:** RTH-serien mister stille sine ældste barer, når 2010-dataene falder uden for
vinduet — første gang omkring juni 2030. Live-brug rammer det samme ét år frem.

### 1.3 Budgetvagten kan nulstilles ved et uheld

`data.src_databento.spent_usd` læser `data/cache/databento/udtraek.jsonl`. Filen ligger i den
git-ignorerede cache, og findes den ikke, returneres $0.

- Slettes `data/cache/`, eller klones repoet et andet sted, starter forbruget forfra, og loftet
  på $40 gælder igen fra nul.
- Loggen indeholder **Databentos estimater** fra `metadata.get_cost`, ikke den faktiske regning.
  $27,31 er summen af estimater. Saldoen i Databento-portalen er ikke tjekket.

### 1.4 To moduler i apparatet kan ikke importeres

Efterprøvet 2026-09-13 i `.venv`:

| modul | fejl |
|---|---|
| `research/bias_engine.py` | `ModuleNotFoundError: research.daily_bias` |
| `research/diagnostics.py` | samme — og importerer desuden `bias_engine` |

`research/daily_bias.py` findes ikke i repoet. Kun `diagnostics.py` er nævnt som ubrugelig, i
docstringen til `research/fase1_verifikation.py`.

`diagnostics.py` og `research/daily_series.py` peger desuden på filer der ikke findes:
`data/historical/{6B,6E,BTCUSDT,ES,ETHUSDT,GC,NQ,SOLUSDT}_1d.csv` og
`data/historical_xau/XAU_1d_data.csv`. `daily_series.py` importerer, men dens `load()` fejler.

**Testene er grønne fordi ingen af dem rører disse moduler eller filer.**

### 1.5 To påstande om det gamle repo er ikke efterprøvet

- **`data/ohlcv.py`** skriver at kontrakten er "den samme som `data/fetcher._validate_ohlcv` i det
  gamle repo". Den fil er aldrig set. Valideringen er skrevet ud fra PRD'ens beskrivelse (§4.3).
- **`STRATEGI_PROPFIRM.md` §6** skriver at apparatet er kopieret "byte-identisk".

Det gamle repo (`REAL TRADING BOT`) ligger ikke under `~/Documents/GitHub` på Macen. Andre
steder er ikke søgt.

### 1.6 Databentos dataformat er antaget, ikke slået op

Databentos dokumentation er JavaScript-renderet og kunne hverken læses med WebFetch eller curl.
Tre ting er derfor antagelser:

| antagelse | status |
|---|---|
| `ts_event` på ohlcv-1m er barens **åbning** | **Bekræftet indirekte:** 390 af 390 RTH-1m-barer er identiske med Yahoos, som mærker barer med åbningstid |
| Et bbo-1m-snapshot ved t beskriver minuttet **før** t | Ikke bekræftet. Tidsstemplerne ligger præcis på minutgrænsen (mikrosekund 0). Bruges i `fase1_verifikation.spread` til RTH/ETH-mærkning |
| Et bbo-1s-sekund uden record betyder **uændret quote** | Ikke bekræftet. 7.056.604 records for 92 dage af 7.617.600 mulige sekunder: **7,4% uden record**. `spread_stikproeve` fremfører quoten højst 60 s |

Spreadtallene i `spread_mnq.md` hviler på de to sidste.

---

## 2. Reproducerbarhed

| forhold | konsekvens |
|---|---|
| Yahoo-udtrækket (`data/cache/yahoo/NQ=F/*/hentet_2026-09-10.parquet`) kan ikke hentes igen — Yahoos vindue ruller (15m: 60 dage, 1m: 30 dage) | K2 kan kun genkøres fra den lokale cache |
| Cachen er 162 MB og ikke i git (Databento 80 MB, stikprøve 82 MB, Yahoo 1 MB) | En ny maskine skal hente Databento igen for ca. $27 |
| Databento-cachen er delt i kalenderår | Forlænges 2026 med en ny slutdato, betales hele årsbidden igen (ca. $0,90), ikke kun det nye stykke |
| `.venv`: Python 3.14.4 med pandas 3.0.5, numpy 2.5.3, pyarrow 25.0.1, yfinance 1.7.0, exchange_calendars 4.13.2, databento 0.86.0, python-dotenv, pytest, PyYAML. **Ingen scipy.** Resten af `requirements.txt` (ccxt, chromadb, alembic …) er ikke installeret | Ingen versionslås. `requirements.txt` siger stadig "Python 3.12 required" øverst; noten om 3.14 står nederst |
| Macen har hverken brew, uv, pyenv eller gh | — |
| Reglen i `research/fase1_data.planer` der rykker NQ's startår frem ved et estimat over $20 | Aldrig udløst (estimatet var $17,83) og ingen test |

---

## 3. Forløb

### 3.1 En commit på branchen er ikke fasesessionens

`32a85ae "starten"` (kvistmads, 2026-09-11 02:09) blev lavet uden for fasesessionen, mens den
arbejdede. Den indeholder et udkast af `datakilder.md` med pladsholdere og
`fase1_verifikation_yahoo.json`. Sessionen så den og nævnte den ikke.

### 3.2 Præregistreringen kan ikke bevises med git alene

`research/atr_fordeling.py` blev skrevet **før** sessionen kiggede på Yahoos 60-dages ATR (RTH
p50 0,227% mod døgn 0,165%) — men committet **efter** (`14ab83f`). Kigget var på Yahoo, ikke på
Databento, så docstringens "før kørslen på Databento-data" holder. Det hviler dog kun på
rækkefølgen i sessionen, ikke på commit-historikken.

### 3.3 To NQ-niveauer giver to risikotal for den samme ATR

| tabel i `atr_fordeling.md` | NQ-niveau | risiko_pct_af_MLL_netto_p90, 15m RTH, 2016-2026 |
|---|---|---|
| hovedtabellerne | 29.138,00 (RTH-luk 2026-09-10) | 13,49 |
| §5 genberegnet | 29.639,50 (§5's niveau) | 13,72 |

Begge er korrekte for deres niveau, og forskellen står i rapporten. Fasesessionens afsluttende
besked blandede dem: tabellen brugte 13,49, svaret på spørgsmål 2 brugte 13,72.

### 3.4 Arbejdsregler der kun lå uden for repoet

Mads' regler fra 2026-09-11, som hidtil kun stod i Claudes hukommelse:

- Én branch pr. fase. Commit undervejs i logiske commits. Overbliksfiler committes for sig.
- Push til fasebranchen. Rør ikke `main`, merge ikke, opret ikke PR.
- `git --no-optional-locks` på alle git-kald.
- `git push` fra Claude Codes shell fejler ("could not read Username for 'https://github.com'"),
  også uden sandbox. Mads pusher selv.

Databento-betingelserne og RTH-mod-døgn-reglen står allerede i `datakilder.md` §2 og
`ANTAGELSER.md` §2.

---

## 4. Uden for dette efterskrift

Fasesessionen har ikke læst ændringerne i `STRATEGI_PROPFIRM.md` efter 2026-09-11 eller
`PRD_FASE2_RUINMODEL.md`.
