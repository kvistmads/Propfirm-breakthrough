# Antagelsesregister

**Formål:** ét sted hvor hvert tal i projektet står med sin kilde, sin status og hvad der
vælter hvis det er forkert. Registeret findes fordi vi allerede har fanget én fejl af
netop denne type: 0,023 R var regnet på Tradovate Free, ikke på den kanal botten bruger.
Den fejl kostede ingenting, fordi den blev fanget. Den næste gør måske.

**Opdateret:** 2026-09-10.

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
| Spread | 1,5 tick = $0,75 | **S** | Overtaget fra `venue_costs.md`. Aldrig målt | omk_R. Er den 3 tick uden for RTH, fordobles spreaddelen |
| Slippage | 0,5 tick pr. side | **S** | `backtest/costs.py`-default. Ingen offentlig statistik at slå op | omk_R. Stop i hurtige bevægelser fylder værre |
| **omk_R netto ved 1 ATR** | **0,0248** | **S** | Afledt: $2,47 / $99,59 | be_WR og hele §5-gitteret |
| be_WR ved 2:1 | 34,16% | **V** | Beregnet af `research/stats.breakeven_win_rate` | — (følger af ovenstående) |

**Bemærk:** gebyret er verificeret, men de to andre led er skøn. To tredjedele af
omkostningen i dollar er verificeret; en tredjedel er gættet.

---

## 2. Volatilitet

| tal | værdi | status | kilde | vælter hvis forkert |
|---|---|---|---|---|
| ATR 15m på NQ | 0,168% | **M, svagt** | `venue_costs.md` linje 313: **60 dages historik**, Yahoos intraday-cap | Hele §5-gitteret. Se nedenfor |
| ATR på 5m/3m/1m | **ukendt** | — | Ikke målt. Kun kvadratrods-skaleret | Timeframe-valget |
| **Kvadratrods-skalering af ATR** | ATR_T = ATR_15m × √(T/15) | **A** | Lærebogsantagelse | §5b's tabel. Intradag skalerer ATR typisk *under* kvadratroden, fordi barens range indeholder spread og støj der ikke skalerer med tiden |
| NQ-prisniveau | 29.639,50 | **V** | 2026-09-07 | Skalerer alle dollartal lineært |

### Hvorfor ATR er registerets svageste tal

60 dage er ét volatilitetsregime. Retningen af fejlen er **ikke** entydig, og det er
pointen — de to konsekvenser trækker hver sin vej:

| ATR 15m | R_pr_kontrakt_$ | risiko_pr_handel_$ | pct_af_MLL | omk_R | be_WR_pct |
|---|---|---|---|---|---|
| 0,118% (−30%) | 69,71 | 72,18 | **3,61** | 0,0355 | 34,52 |
| **0,168% (basis)** | **99,59** | **102,06** | **5,10** | **0,0248** | **34,16** |
| 0,218% (+30%) | 129,47 | 131,94 | **6,60** | 0,0191 | 33,97 |

**Højere ATR gør handlen dyrere i MLL-andel og billigere i R.** Omkostningen er fast pr.
handel mens 1R vokser, så gebyret fylder mindre. Man kan ikke aflæse "højere ATR = værre"
af én kolonne.

**Den bindende begrænsning er at 1 MNQ er udelelig.** Man kan ikke size under én kontrakt.
Ved ATR +30% risikerer den mindst mulige position 6,6% af MLL, og eneste håndtag er at
stramme stoppet — til 0,77 ATR for at komme tilbage på 5,1%. Et strammere stop koster win
rate, og hvor meget ved vi ikke. **Et ATR-estimat der er 30% for lavt kan derfor afgøre om
15m overhovedet er farbar — ikke bare flytte en procentsats.**

**Konsekvens for metoden:** size ikke efter et punktestimat. Rapportér 10./50./90.
percentil af ATR over så lang historik som muligt og vurder go/no-go på den **høje** ende —
samme regel som blev brugt på guldprisen. Det kræver fase 1.

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

**Rettelse besluttet 2026-09-10:** når der findes en strategi, skal ruinmodellen ikke
trække uafhængige handler, men **bootstrappe fra strategiens egen handelssekvens** (blok-
bootstrap, så klyngningen bevares). Det er den eneste måde at få tallet til at afspejle
strategien frem for antagelsen.

---

## 5. Hvad vi slet ikke ved endnu

| spørgsmål | konsekvens |
|---|---|
| Findes der en edge på indeksfutures på 15m eller lavere? | Uden den er alt ovenstående ligegyldigt |
| Rækker en gratis kildes futureshistorik? | Afgør om ATR kan måles som fordeling eller kun som skøn |
| Kan spread overhovedet måles fra de data vi kan få? | Spread kræver bid/ask; OHLC-barer har det ikke |
| Hvor meget afviger backtest-serien fra TopstepX' feed? | Guld-lektionen: 20% forskel i ATR mellem to kilder for samme instrument |
| Hvad koster markedsdata på LFA? | Løbende omkostning i det eneste live-trin |
