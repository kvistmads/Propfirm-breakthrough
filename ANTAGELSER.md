# Antagelsesregister

**Formål:** ét sted hvor hvert tal i projektet står med sin kilde, sin status og hvad der
vælter hvis det er forkert. Registeret findes fordi vi allerede har fanget én fejl af
netop denne type: 0,023 R var regnet på Tradovate Free, ikke på den kanal botten bruger.
Den fejl kostede ingenting, fordi den blev fanget. Den næste gør måske.

**Opdateret:** 2026-09-13 — fase 2: målt spread i `config.yaml`, omkostningen dekomponeret med
realiseret slippage, ruinmodellen regnet på den målte ATR-fordeling. Tal og metode i
`research/output/mll_ruin_v2.md` og `research/prereg/fase2_valgregel.md`. Fase 1:
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
| **Spread MNQ, RTH** | **1,73 tick** i snit (p50 2, p90 2; 34% af tiden på 1 tick) = $0,865 pr. rundtur | **M** | Databento MNQ.v.0 bbo-1s, stratificeret stikprøve af 92 Globex-dage 2019-2026, rolige og volatile. `research/output/spread_mnq.md`. Hviler på fortolkningen af bbo (§6) | omk_R. Volatile dage 1,94 tick, rolige 1,55 |
| **Spread MNQ, uden for RTH** | **2,17 tick** i snit (p50 2, p90 3; 16% på 1 tick) = $1,085 pr. rundtur | **M** | samme. Genåbningen 18:00 ET 2,91 tick. Steget hvert år siden 2023 (1,74 → 2,58) | omk_R ved døgndrift |
| Spread i `config.yaml` | **1,73 tick** (`spread_ticks`, RTH) og 2,17 tick (`spread_ticks_uden_for_rth`) | **M** | Sat 2026-09-13 i fase 2 (tidligere 1,5 tick, S). `apply_costs` kender ikke sessionen og bruger kun RTH-værdien — botten handler i RTH | Alle omkostningstal fra backtesten |
| **Slippage** | Parameter N(0,5; 0,5) tick pr. side, afskåret ved 0 → **realiseret 0,5417 tick pr. side** = $0,542 pr. rundtur | **S — stadig.** Nu det største uverificerede led | `backtest/costs.py`. Ingen offentlig statistik at slå op. Afskæringen løfter middelværdien fra 0,50 til 0,5417, og den **tillader aldrig gunstig slippage**. `config.yaml` erklærer den realiserede værdi; en test holder den op mod koden | omk_R. Stop i hurtige bevægelser fylder værre. **Fase 2: ved 1,0 tick pr. side bliver den valgte celles K2-tærskel uafgjort → C4 er blokerende** |
| **Rundtur, 1 MNQ** | **$2,627 i RTH** · $2,847 uden for RTH | **M** — afledt af to M'er og ét S (slippage) | `backtest.costs.rundtur_dekomponering`: $1,22 + spread + 2 × realiseret slippage. Med det gamle 1,50-tick-skøn: $2,512 | omk_R, be_WR, risiko af MLL |
| **omk_R netto ved 1 ATR, 15m RTH** | ved R_p50 0,0176 · ved middel-R 0,0152 | **M** — afledt af to M'er og ét S (slippage) | $2,627 / R ved NQ 29.138, primærvindue 2019-05-06 → 2026-09-10 (fase 2). Fase 1 regnede 0,0180 med $2,47 og K3 2016-2026 | be_WR og hele sizing-gitteret |
| be_WR ved 2:1, 15m RTH, 1 ATR | ved R_p50 33,92% · **ved middel-R 33,84%** | **V** (beregnet) | `research.stats.breakeven_win_rate` / `mll_ruin.be_wr`. Når R trækkes pr. handel, er det middel-R der giver nul edge; §5a's kolonne ved R_p50 var break-even for konstant-modellen | — (følger af ovenstående) |

**Bemærk:** gebyret er verificeret, spreadet er målt og står nu i `config.yaml`, og slippage er det
eneste rene skøn tilbage i omkostningen. Fase 1's tabeller er regnet med $2,47 (§4) og $2,59
(§5a) og står ved magt — differencen til $2,627 flytter risikokolonnen ~0,002 pp. $2,627 er
tallet fremadrettet.

---

## 2. Volatilitet

| tal | værdi | status | kilde | vælter hvis forkert |
|---|---|---|---|---|
| **ATR 15m, RTH** | **Fase 2 primærvindue 2019-05-06 → 2026-09-10:** p50 0,257 · **p90 0,477** · middel 0,297%. Fase 1, K3 2016-2026: p10 0,130 · p50 0,232 · p90 0,459% | **M** — fordeling, NQ, RTH og døgn adskilt | Databento NQ.v.0 1m. 47.868 barer (primært) / 69.610 (K3). **Målt på NQ, ikke MNQ** — se instrumentrækken | Sizing-gitteret. **Go/no-go på p90** |
| **ATR 15m, døgn** | Primærvindue: p50 0,148 · p90 0,316%. Fase 1, K3: p10 0,062 · p50 0,132 · p90 0,296% | **M** | samme | Døgndrift |
| **ATR 5m / 3m / 1m, RTH** | Primærvindue: p50 0,146 / 0,112 / 0,063% · p90 0,285 / 0,222 / 0,131%. Fase 1, K3: p50 0,132 / 0,101 / 0,057% · p90 0,271 / 0,210 / 0,123% | **M** | samme | Timeframe-valget |
| ATR 5m / 3m / 1m, døgn | Primærvindue: p50 0,080 / 0,060 / 0,033% · p90 0,193 / 0,151 / 0,087%. Fase 1, K3: p50 0,071 / 0,053 / 0,029% | **M** | samme. 1m døgn fejler K4 i fase 1 (2,0% flade barer) | — |
| ATR 15m, §5's gamle basis | 0,168% — **erstattet** | **M** | `venue_costs.md` linje 313: 60 dage Yahoo. **Målt på døgnserien, ikke RTH** | Erstattet af rækkerne ovenfor |
| **Instrument for ATR** | ATR i procent antages ens på NQ og MNQ | **A** | Ikke målt. MNQ-1m-barer ligger ikke i cachen; et udtræk (~$9,46) blev fravalgt 2026-09-13. Risikoen kommer derfor fra NQ, spreadet fra MNQ | Hele sizing-gitteret, hvis MNQ's tyndere bog giver bredere barer |
| Kvadratrods-skalering af ATR | ATR_T = ATR_15m × √(T/15) | **M** | Hver timeframe er målt. I RTH (K3 2016-2026) ligger formen −1,8% (5m), −3,0% (3m) og −5,5% (1m) fra √T; i døgn −7 til −15%. **Afvigelsen er negativ, ikke positiv** — lave timeframes har lavere ATR end √T forudsiger | Ingen |
| NQ-prisniveau | **29.138,00** — RTH-luk 2026-09-10 15:59 ET | **V** | CME via Databento (NQU6). Læses fra data i `research/mll_ruin.py`, ikke hardkodet. 29.639,50 (2026-09-07) er ude af brug og står kun som K1's regressionsinput | Skalerer alle dollartal lineært |

### ATR efter fase 1

**Status: M med kendt stikprøve** — 10,7 år NQ 1m fra CME, i de år hvor RTH-dækningen er komplet.
2010-2015 er målt men består ikke K3 og indgår ikke i go/no-go-grundlaget. Fase 2 bruger
2019-05-06 og frem som primærvindue; det er ~9% mere volatilt i middel end K3 2016-2026.

Genberegnet ved §5's NQ-niveau (29.639,50) og $2,47 pr. rundtur. Kun ATR er skiftet:

| 1 MNQ, 1-ATR-stop, 15m | risiko_pct_af_MLL_netto_p50 | risiko_pct_af_MLL_netto_p90 | omk_R_netto_p50 | omk_R_netto_p90 | be_WR_pct_netto_p90 |
|---|---|---|---|---|---|
| §5 (0,168%, én værdi) | 5,10 | 5,10 | 0,0248 | 0,0248 | 34,16 |
| **målt RTH** | **7,00** | **13,72** | 0,0180 | 0,0321 | 34,40 |
| målt døgn | 4,05 | 8,90 | 0,0315 | 0,0675 | 35,58 |

`omk_R_netto_p90` og `be_WR_pct_netto_p90` i denne tabel er 90. percentil af omk/R bar for bar,
altså omkostningen ved ATR's **p10** — den høje ende af be_WR. Fase 2 navngiver kolonnerne efter
hvad de står ved (`be_WR_pct_ved_R_p50`, `be_WR_pct_ved_middel_R`).

**Sessionen er den største enkeltfaktor.** RTH ligger 75% over døgn på medianen og 55% på p90.

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
| **Fladningsregel** | Alt fladt kl. 15:10 CT hver hverdag; Topstep begynder at flade 15:08 CT | **V** (2026-09-12) |
| **LFA: markedsdatapris** | **ukendt** | — |

---

## 4. Modelantagelser i ruinmodellen

§5's og fase 2's tal gælder kun i det omfang disse holder. Ruinmodellen er `research/mll_ruin.py`
(v2, 2026-09-13).

| antagelse | valgt værdi | status | hvorfor den kan være forkert |
|---|---|---|---|
| Gevinst/tab-forhold | 2:1 | **A** | Det gamle projekt gik til 1,5:1 fordi prisen ofte lige akkurat missede TP. Ved 1,5:1 er be_WR ~40%, ikke ~34% |
| Handler pr. dag | 1-3, ligefordelt | **A** | Fri antagelse. Påvirker hvor hurtigt både mål og ruin nås |
| Win rate | Absolut 34/37/40/45% og relativ be_WR + 0/3/6/11 pp | **A** | Ingen strategi har leveret nogen af dem på MNQ. De to akser giver forskellig celle (fase 2), fordi vi ikke ved hvordan WR reagerer på stopbredde |
| **Handler er uafhængige** | ja | **A** | **Rigtige strategier klynger deres tab.** Uafhængighed gør ruin pænere end virkeligheden. Ruintallene er sandsynligvis optimistiske |
| Fast kontraktantal | ja | **A** | ATR svinger dagligt, så dollarrisikoen svinger med. Dynamisk sizing er ikke testet |
| Stoppet rammes præcist | ja | **A** | Slippage på stops er ikke målt; slippage indgår kun som middelomkostning |
| Horisont | 200 handelsdage | **A** | Ved lav risiko er censureringen stor: ved WR 40% står 99,6% af stierne i 1m/0,50 ATR som uafgjort, 38% i 5m/0,50 |
| Målfunktion | "nå $3.000 før ruin" | **A** | Gælder kun Combine. XFA og LFA har en anden målfunktion: fem dage à $150+ |
| **ATR-input** | Ét træk pr. handel fra den empiriske ATR-fordeling for cellens timeframe i RTH, NQ 2019-05-06 → 2026-09-10 | **M** (inputtet) | Erstatter konstanten 0,168%. Fordelingen i stedet for en konstant ved samme middel løfter P(ruin) med 8,5 pp på den valgte celle (fase 2) |
| ATR-trækkene er uafhængige i tid | ja | **A** | Høje ATR'er klumper sig i uger. Modellen ser at en dyr handel er dyrere, ikke at flere dyre handler kommer i træk |
| **Prisniveau i ruinmodellen — fast nutidigt niveau, ikke barens historiske** | NQ 29.138 for alle træk | **A** | MLL'en er $2.000 i dagens dollar. NQ lukkede RTH i 4.490 (2016-01-04), 7.808,50 (2019-05-06) og 29.138 (2026-09-10). Samme ATR i procent er 3,7 gange flere dollar i dag end i 2019. Trak modellen prisen med fra baren, blandede den regimer og undervurderede risikoen systematisk. Antagelsen er at procent-ATR er regimets stabile mål |
| **Ingen position ved dagsgrænsen** (trailet regnes på en flad konto) | ja | **V** | Var en antagelse i v1. Nu en regel: Topstep kræver alt fladt kl. 15:10 CT (§3) |

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
| **Slippage på stops** | Spread er målt; fyldet i en hurtig bevægelse er ikke. **Fase 2: blokerende (C4)** — den valgte celles konklusion skifter mellem 0,5417 og 1,0 tick pr. side |
| Er ATR i procent den samme på MNQ som på NQ? | Ikke målt. Kræver MNQ-1m-barer (~$9,46) |
| Hvad koster markedsdata på LFA? | Løbende omkostning i det eneste live-trin |

### Besvaret i fase 1

| spørgsmål | svar |
|---|---|
| Rækker en gratis kildes futureshistorik? | **Nej, ikke uden konto.** Yahoo har 60 dage på 15m. Databento via gratis kredit: 16,3 år NQ 1m, heraf 10,7 år (2016-2026) med komplet RTH |
| Kan spread overhovedet måles fra de data vi kan få? | **Ja** — fra Databentos bid/ask, ikke fra OHLC. Se spread-rækkerne i §1 |
| Stemmer barerne overens på tværs af kilder? | **Ja.** Yahoo og Databento har identiske 1m- og 15m-barer, samme bar-grænser og tidszone (K2) |

---

## 6. Apparat og dataformat

Fra fase 1-sessionens efterskrift (`research/output/fase1_efterskrift.md`), ført ind 2026-09-13.

| antagelse | status | note |
|---|---|---|
| Spreadmålingens fortolkning af bbo | **A** | Et bbo-snapshot beskriver intervallet før; en quote fremføres højst 60 s. Ubekræftet — Databentos dokumentation kunne ikke hentes. ~7% af sekunderne mangler en record. Spread-rækkerne i §1 hviler på den. Fase 2's følsomhed (1,50 og 2,17 tick) flytter ikke den valgte celles konklusion |
| `ts_event` er barens åbning | **M, indirekte** | Bekræftet ved at barerne er identiske med Yahoo (390 af 390 RTH-1m-barer), ikke ved dokumentation |
| Apparatet er byte-identisk med det gamle repo | **A** | Kan ikke efterprøves. `REAL TRADING BOT` blev ikke fundet på Macen |
| `data/ohlcv.py` følger `_validate_ohlcv`'s kontrakt | **A** | Skrevet ud fra PRD'ens beskrivelse, ikke fra originalen |
| Kalenderdækning | **A** | `exchange_calendars` dækker kørselsdato −20/+1 år. Uden for vinduet blev alt tavst markeret ETH. **Siden 2026-09-13 fejler `rth_mask` i stedet**, med både kalenderens og seriens interval i beskeden |
