# Antagelsesregister

**Formål:** ét sted hvor hvert tal i projektet står med sin kilde, sin status og hvad der
vælter hvis det er forkert. Registeret findes fordi vi allerede har fanget én fejl af
netop denne type: 0,023 R var regnet på Tradovate Free, ikke på den kanal botten bruger.
Den fejl kostede ingenting, fordi den blev fanget. Den næste gør måske.

**Opdateret:** 2026-09-11 — fase 1: ATR og MNQ-spread målt, datakilde valgt. Tal og metode i
`research/output/atr_fordeling.md` og `research/output/datakilder.md`.

## Statuskoder

| kode | betyder |
|---|---|
| **V** | Verificeret hos primærkilden for den kanal vi faktisk bruger |
| **M** | Målt af os, med kendt metode og kendt stikprøve |
| **S** | Skøn. Ikke målt, ikke verificeret |
| **A** | Antagelse i en model. Vi har valgt tallet, virkeligheden har ikke bekræftet det |

---

## 1. Kontrakt og omkostninger

| tal | værdi | status | kilde | vælter hvis forkert |
|---|---|---|---|---|
| MNQ indeksmultiplikator | $2/point | **V** | CME contract specs | Alt. Hele dollarregnestykket |
| MNQ ticksize | 0,25 point = $0,50 | **V** | CME contract specs | Spread- og slippagetal |
| Gebyr, rundtur | $1,22 | **V** | TopstepX Commissions and Fees, 2026-09-09 | omk_R og be_WR — men kun med ~0,003 R |
| **Spread MNQ, RTH** | **1,73 tick** i snit (p50 2, p90 2; 34% af tiden på 1 tick) = $0,87 pr. rundtur | **M** | Databento MNQ.v.0 bbo-1s, stratificeret stikprøve af 92 Globex-dage 2019-2026, rolige og volatile. `research/output/spread_mnq.md` | omk_R. Volatile dage 1,94 tick, rolige 1,55 |
| **Spread MNQ, uden for RTH** | **2,17 tick** i snit (p50 2, p90 3; 16% på 1 tick) = $1,08 pr. rundtur | **M** | samme. Genåbningen 18:00 ET 2,91 tick. Steget hvert år siden 2023 (1,74 → 2,58) | omk_R ved døgndrift |
| Spread i `config.yaml` | 1,5 tick = $0,75 | **S** | Overtaget fra `venue_costs.md`. **Uændret** — fase 1 ændrer ingen konfiguration | Alle omkostningstal i §4-§5 bruger stadig skønnet |
| Slippage | 0,5 tick pr. side | **S** | `backtest/costs.py`-default. Ingen offentlig statistik at slå op | omk_R. Stop i hurtige bevægelser fylder værre |
| **omk_R netto ved 1 ATR, 15m RTH** | **p50 0,0180 · p90 0,0321** | **S** | Afledt: $2,47 / R ved målt RTH-ATR 2016-2026 og §5's NQ-niveau. ATR-leddet er nu M; omkostningen er stadig skønnet (§5 regnede 0,0248) | be_WR og hele §5-gitteret |
| be_WR ved 2:1, 15m RTH | p50 33,93% · p90 34,40% | **V** | Beregnet af `research/stats.breakeven_win_rate` (§5: 34,16%) | — (følger af ovenstående) |

**Bemærk:** gebyret er verificeret, og spreadet er nu målt — skønnet på 1,5 tick er for lavt i
begge sessioner (RTH +16%, uden for RTH +44%). Med målt spread bliver rundturen $2,59 i RTH og
$2,80 uden for RTH mod $2,47. På 15m RTH flytter det omk_R_netto_p50 fra 0,0180 til 0,0188 og
be_WR_pct_netto_p90 fra 34,40% til 34,46%. Slippage er stadig skøn. **`config.yaml` er ikke
ændret** — omkostningstallene i §4-§5 bruger stadig 1,5 tick.

---

## 2. Volatilitet

| tal | værdi | status | kilde | vælter hvis forkert |
|---|---|---|---|---|
| **ATR 15m NQ, RTH** | p10 0,130 · **p50 0,232 · p90 0,459%** | **M** | Databento NQ.v.0 1m, K3-beståede år 2016-2026, 69.610 barer | §5-gitteret. **Go/no-go på p90** |
| **ATR 15m NQ, døgn** | p10 0,062 · p50 0,132 · p90 0,296% | **M** | samme, 251.176 barer | Døgndrift |
| ATR 5m / 3m / 1m, RTH | p50 0,132 / 0,101 / 0,057% · p90 0,271 / 0,210 / 0,123% | **M** | samme | Timeframe-valget |
| ATR 5m / 3m / 1m, døgn | p50 0,071 / 0,053 / 0,029% · p90 0,179 / 0,140 / 0,081% | **M** | samme. 1m døgn fejler K4 (2,0% flade barer) | — |
| ATR 15m, §5's basis | 0,168% — **erstattet** | **M** | `venue_costs.md` linje 313: 60 dage Yahoo. **Målt på døgnserien, ikke RTH** — samme vindue giver døgn p50 0,165% og RTH p50 0,227% | Erstattet af rækkerne ovenfor |
| Kvadratrods-skalering af ATR | ATR_T = ATR_15m × √(T/15) | **M** | Ikke længere en antagelse — hver timeframe er målt. Formen holder inden for −2 til −6% i RTH og −7 til −15% i døgn; de lave timeframes har *lavere* ATR end √T forudsiger. §5b's niveau var forkert fordi basis var døgn | Ingen |
| NQ-prisniveau | 29.138,00 | **V** | RTH-luk 2026-09-10, CME via Databento (NQU6). §5 regnede ved 29.639,50 (2026-09-07) | Skalerer alle dollartal lineært |

### ATR efter fase 1

**Status: M med kendt stikprøve** — 10,7 år NQ 1m fra CME, i de år hvor RTH-dækningen er komplet.
2010-2015 er målt men består ikke K3 og indgår ikke i go/no-go-grundlaget.

Genberegnet ved §5's NQ-niveau (29.639,50) og $2,47 pr. rundtur. Kun ATR er skiftet:

| 1 MNQ, 1-ATR-stop, 15m | risiko_pct_af_MLL_netto_p50 | risiko_pct_af_MLL_netto_p90 | omk_R_netto_p50 | omk_R_netto_p90 | be_WR_pct_netto_p90 |
|---|---|---|---|---|---|
| §5 (0,168%, én værdi) | 5,10 | 5,10 | 0,0248 | 0,0248 | 34,16 |
| **målt RTH** | **7,00** | **13,72** | 0,0180 | 0,0321 | 34,40 |
| målt døgn | 4,05 | 8,90 | 0,0315 | 0,0675 | 35,58 |

**Sessionen er den største enkeltfaktor.** RTH ligger 75% over døgn på medianen og 55% på p90.
§5's 0,168% ligger mellem de to: 28% under RTH-medianen og 27% over døgn-medianen.

**Regimet er den næststørste.** risiko_pct_af_MLL_netto_p90 på 15m RTH spænder fra 6,19% (2017)
til 19,37% (2020) ved dagens NQ-niveau; 2022 18,18%, 2025 13,09%, 2026 hidtil 11,31%.

**Retningen er stadig tosidet:** højere ATR gør handlen dyrere i MLL-andel og billigere i R. Den
bindende begrænsning er fortsat at 1 MNQ er udelelig.

---

## 3. Topsteps regler

Alle verificeret 2026-09-09/10 hos help.topstep.com og topstep.com. **Regler ændrer sig —
slå dem op igen før noget bygges.**

| tal | værdi | status |
|---|---|---|
| Combine $50K: profitmål | $3.000 | **V** |
| Combine $50K: MLL | $2.000, trailer på dagsslutsaldo, låser ved startsaldo | **V** |
| Combine $50K: DLL | $1.000, valgfri | **V** |
| Combine: konsistens | bedste dag ≤ 50% af profitmål, ellers hæves målet | **V** |
| Combine: min. handelsdage | 2 | **V** |
| Combine $50K: pris | $49/md +$149 aktivering, eller $95/md | **V** |
| API-adgang | $29/md, $14,50 med koden `topstep` | **V** |
| Level 1-markedsdata | gratis i Combine og XFA | **V** |
| Level 2-markedsdata | $38/md — unødvendig på 15m | **V** |
| XFA $50K: MLL | $2.000, trailer på højeste dagsslutsaldo, låser ved $0 | **V** |
| XFA: payout-krav | 5 vindende dage à $150+ net | **V** |
| XFA: payout-loft | 50% af saldo, maks $5.000, min $125 | **V** |
| LFA: MLL | **$1.000, fast — trailer IKKE** | **V** |
| LFA: payout | 5 benchmark-dage, 50% indtil 30 dage, derefter 100% dagligt | **V** |
| Profitdeling | 90/10 | **V** |
| **LFA: markedsdatapris** | **ukendt** | — |

---

## 4. Modelantagelser i ruinmodellen

Disse er **A** — vi har valgt dem. §5's tal gælder kun i det omfang de holder.

| antagelse | valgt værdi | hvorfor den kan være forkert |
|---|---|---|
| Gevinst/tab-forhold | 2:1 | Det gamle projekt gik til 1,5:1 fordi prisen ofte lige akkurat missede TP. Ved 1,5:1 er be_WR ~40%, ikke 34,2% |
| Handler pr. dag | 1-3, ligefordelt | Fri antagelse. Påvirker hvor hurtigt både mål og ruin nås |
| Win rate | 34/37/40/45% i gitteret | Ingen strategi har leveret nogen af dem på MNQ |
| **Handler er uafhængige** | ja | **Rigtige strategier klynger deres tab.** Uafhængighed gør ruin pænere end virkeligheden. De 10,1% er sandsynligvis optimistiske |
| Fast kontraktantal | ja | ATR svinger dagligt, så dollarrisikoen svinger med. Dynamisk sizing er ikke testet |
| Stoppet rammes præcist | ja | Slippage på stops er ikke målt |
| Horisont | 200 handelsdage | Ved lav risiko er censureringen stor (41,6% i den forsigtigste celle) |
| Målfunktion | "nå $3.000 før ruin" | Gælder kun Combine. XFA og LFA har en anden målfunktion: fem dage à $150+ |
| **ATR-input** | **0,168% (15m)** | **Målt på døgnserien.** Målt 15m RTH 2016-2026: p50 0,232%, p90 0,459% — 7,00% og 13,72% af MLL pr. handel mod modellens 5,10%. Modellen er ikke genkørt |

**Rettelse besluttet 2026-09-10:** når der findes en strategi, skal ruinmodellen ikke
trække uafhængige handler, men **bootstrappe fra strategiens egen handelssekvens** (blok-
bootstrap, så klyngningen bevares). Det er den eneste måde at få tallet til at afspejle
strategien frem for antagelsen.

---

## 5. Hvad vi slet ikke ved endnu

| spørgsmål | konsekvens |
|---|---|
| Findes der en edge på indeksfutures på 15m eller lavere? | Uden den er alt ovenstående ligegyldigt |
| Hvor meget afviger backtest-serien fra TopstepX' feed? | Guld-lektionen: 20% forskel i ATR mellem to kilder. Yahoo og Databento er identiske bar for bar, men TopstepX er ikke sammenlignet (C7) |
| Slippage på stops | Spread er målt; fyldet i en hurtig bevægelse er ikke (C4) |
| Hvad koster markedsdata på LFA? | Løbende omkostning i det eneste live-trin |

### Besvaret i fase 1

| spørgsmål | svar |
|---|---|
| Rækker en gratis kildes futureshistorik? | **Nej, ikke uden konto.** Yahoo har 60 dage på 15m. Databento via gratis kredit: 16,3 år NQ 1m, heraf 10,7 år (2016-2026) med komplet RTH |
| Kan spread overhovedet måles fra de data vi kan få? | **Ja** — fra Databentos bid/ask, ikke fra OHLC. Se spread-rækkerne i §1 |
| Stemmer barerne overens på tværs af kilder? | **Ja.** Yahoo og Databento har identiske 1m- og 15m-barer, samme bar-grænser og tidszone (K2) |
