# Propfirm-sporet

**Status:** 2026-09-10. Repoet står, apparatet er kopieret, testene er grønne
(94 passed, 4 skipped), alt er committet og pushet. **Spørgsmål A1-A6 er besvaret.**
Ingen konto åbnet, ingen strategi bygget, ingen prisdata i repoet.

Søsterdokumenter: `claude/ANTAGELSER.md` (hvilke tal er verificeret og hvilke er gæt),
`claude/PRD_FASE1_DATAGRUNDLAG.md` (næste fase), `STRATEGI_TSMOM.md`,
`STRATEGI_DAYTRADING.md`.

---

## 0. Invarianter

Regler der gør alle tabeller i dokumentet forkerte hvis de brydes. De står her og ikke i
en fodnote, fordi de er stille fejl — man ser dem ikke i et resultat.

> **RR-invarianten.** Alt i dette dokument regner med **2:1**. Ved 2:1 og omkostning
> 0,0248 R er break-even 34,16%. Ved 1,5:1 er den ~40%. **Tal fra en 2:1-tabel må aldrig
> læses sammen med tal fra en 1,5:1-tabel.** Ændres RR, skal hver eneste tabel regnes om
> — ikke justeres.

> **Kanal-invarianten.** En gebyrsats tæller først når den er verificeret for den kanal
> botten faktisk bruger. Fanget to gange: MEXC (web mod API) og MNQ (Tradovate Free mod
> TopstepX).

> **Enheds-invarianten.** Enheden står i kolonnenavnet. `omk_R_netto`, ikke `omk`.

> **Estimat-invarianten.** Et punktestimat sizes der ikke efter. Fordelinger rapporteres
> som 10./50./90. percentil, og go/no-go vurderes på den ende hvor det gør ondt.

---

## 1. Hvad sporet er

Et handelssystem der skal igennem Topsteps tre trin og derefter tjene penge på
propfirmaets kapital.

**To strategier, tre konfigurationer.** Antallet af strategier følger antallet af
*målfunktioner*, ikke antallet af konti:

| spor | konti | målfunktion | tabsfunktion |
|---|---|---|---|
| **A — eval** | Combine | Nå +$3.000 før −$2.000 (trailende gulv) | Fejl koster et gebyr. Må være aggressiv |
| **B — indtjening** | XFA, derefter LFA | Producér vindende dage à $150+ og tag payouts | Fejl koster kontoen. Skal være defensiv |

XFA og LFA deler målfunktion — vindende dage → payout. De adskiller sig kun på gulvet
($2.000 trailende der låser ved $0, mod $1.000 fast) og på om markedet er rigtigt. **Det
er en risikoparameter, ikke en strategi.** Derfor to strategier med tre
risikokonfigurationer, ikke tre strategier.

**A optimerer en strækning. B optimerer en gentagen daglig tærskel.** Det er den
væsentlige forskel, og den har konsekvenser helt ned i valget af timeframe (§5).

### Afgrænsning

- **Nyt repo.** Begrundelsen er Mads' egen: "knald eller fald, en forkert fejl på det
  forkerte tidspunkt, konto død."
- **Apparatet kopieres, deles ikke.** Gennemført — se §6.
- **De 5-10K egen kapital er ikke en del af dette spor.**

---

## 2. Beslutninger truffet

| Spørgsmål | Valg |
|---|---|
| Kapital | Udelukkende propfirm-kapital |
| Firma | Topstep er førstevalg, ikke låst |
| Kontostørrelse | **$50K** |
| Instrument | **MNQ** (mikro Nasdaq) |
| Antal strategier | **To** (spor A og B), tre risikokonfigurationer |
| Sizing, spor A | **1 MNQ, 1-ATR-stop** (§5) |
| Timeframe | **15m eller lavere.** 1h og 4h er udelukket — se §5 |
| Daily Loss Limit | Slået til ($1.000 i Combine) |
| Ruinmål | Drawdown, 1:1 med Topsteps egen mekanik |
| Autonomi | Backtest og paper-forward **fuldauto**; funded live **semi**. Combine-fasen ikke afgjort |
| Session | US RTH som udgangspunkt; døgndrift skal måles før den vurderes |
| RR | 2:1 — **antaget, ikke målt.** Se B5 |

---

## 3. Topsteps tre trin

Verificeret 2026-09-09/10. **Vi talte hidtil om "eval" og "funded" som to trin. Der er
tre, og de har fundamentalt forskellig risikogeometri.**

| trin | konto | penge | startsaldo | MLL | trailer MLL? |
|---|---|---|---|---|---|
| **1. Trading Combine** | simuleret | abonnement, ingen udbetaling | $50.000 | $2.000 | Ja — på dagsslutsaldo, låser ved startsaldo |
| **2. Express Funded (XFA)** | **simuleret, men rigtige udbetalinger** | 90% til dig | $0 | $2.000 | Ja — låser permanent ved $0 når saldo når $2.000 |
| **3. Live Funded (LFA)** | **rigtige markeder** | 90% + bonusser | 20% af samlet saldo, resten frigives i trin | **$1.000** | **Nej. Fast gulv** |

**Trin 2 er hvor pengene begynder, og den er stadig simuleret.** Man kan tjene rigtige
penge uden nogensinde at røre et live-marked.

### Hvad hvert trin kræver

| trin | krav |
|---|---|
| Combine | Nå $3.000. Bedste dag ≤ 50% af profitmålet, ellers **hæves** målet. Min. 2 handelsdage |
| XFA | **5 vindende dage à $150+ net.** Derefter payout på op til 50% af saldo, maks $5.000, min $125. Efter hver payout nulstilles tælleren og MLL låses på $0 |
| LFA | 5 benchmark-dage à $150+ pr. cyklus. 50% af saldo indtil 30 benchmark-dage, derefter 100% én gang pr. hverdag |

### Konsekvensen for strategidesign

**Combine belønner en strækning. XFA og LFA belønner en tærskel.**

På Combine skal man samle $3.000 op mod et gulv der følger med op. På XFA skal man lave
**fem dage med mindst $150 net** — og med 1 MNQ på 2:1 er én vinder $199. Én ren vinder på
en dag *er* en vindende dag. Markant lavere barre, og den favoriserer en anden adfærd:
tag gevinsten, luk dagen, gentag.

Efter første payout er XFA-gulvet $0. Man kan derefter aldrig tabe mere end det der står
på kontoen. **Trin 2 er et mildere regime end evalueringen, ikke et hårdere.**

**Og spor B har en nedre grænse for handelsfrekvens som spor A ikke har.** Fem vindende
*dage* kan ikke produceres af en strategi der handler én gang om ugen. Det binder
timeframe-valget — se §5.

### Automatisering og hvor koden kører

> "Custom automated strategies and bots are allowed via the TopstepX / ProjectX API,
> subject to standard platform rules and our prohibition on high-frequency trading (HFT)."

> "All trading activity must originate from your personal device. The use of VPS, VPNs,
> and remote servers is prohibited by Topstep's Terms of Use."

Ingen sandbox — "API orders are final". Ingen support på implementeringen. Macens oppetid
er en del af strategien og skal løses før første live-handel.

### MLL-mekanikken på de trailende trin

| | |
|---|---|
| MLL **trailer** på | **dagsslutsaldo**. Aldrig nedad |
| MLL **låser** | Combine: ved startsaldo ($50.000, dvs. dagsslut $52.000). XFA: ved $0 |
| MLL **brydes** på | **net P&L i realtid, urealiseret tæller med** → øjeblikkelig likvidering |
| Intradag give-back | tæller **ikke** mod trailet. Kun mod bruddet |

**Trailet er dagsslut, bruddet er realtid.** Topstep er ikke intraday-trailing: et løb til
+$800 der gives tilbage til +$300 koster ingenting i gulv.

Risikoen er ikke jævnt fordelt over de $3.000 i Combine:

| fase | saldo_$ | luft_til_MLL_$ |
|---|---|---|
| start | 50.000 | 2.000 |
| under opbygning | 50.000–52.000 | altid ~2.000 — gulvet følger med op |
| efter lås | > 52.000 | saldo − 50.000, vokser frit |
| profitmål nået | 53.000 | 3.000 |

To tredjedele af eval-løbet ligger i det stramme felt.

### Daily Loss Limit — ikke det samme som MLL

| grænse | Combine $50K | LFA | konsekvens ved brud |
|---|---|---|---|
| Maximum Loss Limit | 2.000, trailende | 1.000, fast | konto død |
| Daily Loss Limit | 1.000, **valgfri** | dynamisk med saldo | positioner flades, pause til næste dag. **Ikke** et regelbrud |

**Ved 1-3 mikroer binder DLL'en aldrig.** Værste dag ved 3 kontrakter × 3 handler er $918.

### Omkostninger og data

| post | $/md |
|---|---|
| Combine $50K, standard-spor | 49,00 |
| API med koden `topstep` | 14,50 |
| Level 1-markedsdata (Combine + XFA) | 0 |
| **i alt under evaluering** | **63,50** |

Level 2 koster $38/md og er unødvendig på 15m. Historiske data til backtest er en anden
sag og forventes gratis — se B1. **LFA-datapris er ukendt (C6).**

---

## 4. Omkostningsgrundlaget

Kontrakten (CME): MNQ er **$2 pr. indekspoint, tick 0,25 = $0,50**.
Gebyret (TopstepX): **$1,22 rundtur** = $0,50 kurtage + $0,71 børs + $0,01 NFA. Samme sats
på alle tre trin.

Ved NQ 29.639,50 og ATR_15m 0,168% er 1 ATR = 49,79 point = **R = $99,59** pr. kontrakt:

| grundlag | gebyr_$ | spread_$ | slippage_$ | i_alt_$ | omk_R | be_WR_pct ved 2:1 |
|---|---|---|---|---|---|---|
| gammelt tal (Tradovate Free) | 1,50 | 0,75 | — | 2,25 | 0,023 | 34,1 |
| verificeret, gebyr + spread | **1,22** | 0,75 | — | **1,97** | **0,0198** | **33,99** |
| **som koden faktisk regner** | 1,22 | 0,75 | 0,50 | **2,47** | **0,0248** | **34,16** |

**Tredje række gælder.** Det gamle 0,023 R var uden slippage; modellen i repoet trækker
0,5 tick pr. side.

**To af tre led er skøn.** Kun gebyret er verificeret. Spread (1,5 tick) og slippage
(0,5 tick/side) er gæt — se `claude/ANTAGELSER.md`.

**Omkostningsspørgsmålet er lukket.** Det der mangler er en edge.

---

## 5. Positionsstørrelse og timeframe

### 5a. Ruinmodellen — BESVARET, med forbehold

Kørt 2026-09-09. Monte Carlo, 20.000 stier pr. celle, horisont 200 handelsdage, mekanik
1:1 med Combine. Kode: `research/mll_ruin.py`. Rapport: `research/output/mll_ruin.md`.

**Præregistreret kriterium:** vej 3 ("acceptér 5% pr. handel") forkastes hvis
P(ruin før profitmål) > 50% ved WR 40%, 1 MNQ og 1-ATR-stop.

**Resultat: P(ruin) = 10,09% [9,7–10,5].** Pessimistisk brudmodel 11,84%.
**Ikke falsificeret.**

| kontrakter | stop_ATR | risiko_pr_handel_$ | pct_af_MLL | bestå_pct | bestå_CI_95 | ruin_pct_opt | ruin_pct_pess | uafgjort_pct | median_dage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0,50 | 52,27 | 2,61 | 57,27 | [56,6–58,0] | 1,11 | 1,31 | **41,61** | 141 |
| 1 | 0,75 | 77,16 | 3,86 | 86,02 | [85,5–86,5] | 5,28 | 6,18 | 8,71 | 99 |
| **1** | **1,00** | **102,06** | **5,10** | **88,61** | **[88,2–89,0]** | **10,09** | **11,84** | **1,30** | **69** |
| 2 | 0,50 | 104,53 | 5,23 | 82,53 | [82,0–83,1] | 15,16 | 17,69 | 2,30 | 74 |
| 2 | 0,75 | 154,33 | 7,72 | 73,83 | [73,2–74,4] | 26,13 | 30,46 | 0,04 | 40 |
| 2 | 1,00 | 204,12 | 10,21 | 67,65 | [67,0–68,3] | 32,35 | 37,97 | 0,00 | 25 |
| 3 | 0,50 | 156,80 | 7,84 | 70,89 | [70,3–71,5] | 29,09 | 33,20 | 0,03 | 41 |
| 3 | 0,75 | 231,49 | 11,57 | 63,03 | [62,4–63,7] | 36,97 | 43,20 | 0,00 | 21 |
| 3 | 1,00 | 306,18 | 15,31 | 57,67 | [57,0–58,4] | 42,33 | 50,28 | 0,00 | 14 |

**Bekymringen vendte den forkerte vej.** De 5% af MLL pr. handel er tæt på det bedste valg
for evalueringen. Profitmålet er 1,5 × MLL — man *skal* tage risiko for at komme i mål.

Den forsigtige og den aggressive ende havner samme sted (57%) af modsatte grunde: den ene
dør, den anden **når aldrig frem**. 1 MNQ med 0,5-ATR-stop har 1,1% ruin og 41,6% der ikke
er i mål efter 200 handelsdage.

**Valgt: den midterste, 1 MNQ med 1-ATR-stop.**

**Og det tal der betyder mest:** over hele sizing-gitteret spænder bestå fra 57 til 89%.
Over win rate spænder den fra **1 til 99%**. Kontrolcellen uden edge (WR 34%) dør i 72% af
stierne uanset sizing. **Sizing er andenordens. Edgen er førsteordens.**

### 5b. Timeframe-vinduet — hvorfor 1h og 4h er ude

Timeframen er klemt fra begge sider, og det er to helt forskellige kræfter.

**Nedefra af omkostningen.** Omkostningen er fast pr. handel ($2,47). Falder timeframen,
skrumper 1R, og gebyret fylder mere i R.

**Ovenfra af MLL'en — og af at 1 MNQ er udelelig.** Stiger timeframen, vokser 1R i dollar.
Der findes ingen halv kontrakt, så den mindst mulige position bliver hurtigt for stor mod
et gulv på $2.000.

Ved kvadratrods-skalering af ATR fra det målte 15m-tal:

| timeframe | ATR_pct (skaleret) | R_pr_kontrakt_$ | risiko_pr_handel_$ | **pct_af_MLL** | omk_R | be_WR_pct |
|---|---|---|---|---|---|---|
| 1m | 0,0434 | 25,71 | 28,19 | 1,41 | **0,0961** | 36,54 |
| 3m | 0,0751 | 44,54 | 47,01 | 2,35 | 0,0555 | 35,18 |
| 5m | 0,0970 | 57,50 | 59,97 | 3,00 | 0,0430 | 34,77 |
| **15m** | **0,1680** | **99,59** | **102,06** | **5,10** | **0,0248** | **34,16** |
| 1h | 0,3360 | 199,18 | 201,65 | **10,08** | 0,0124 | 33,75 |
| 4h | 0,6720 | 398,35 | 400,83 | **20,04** | 0,0062 | 33,54 |

**På 4h koster én MNQ med et 1-ATR-stop en femtedel af hele risikobudgettet. Fem tabende
handler og kontoen er død.** På 1h er det en tiendedel. Der er ingen vej udenom ved at
size ned — 1 kontrakt er bunden.

Man kan stramme stoppet i stedet (0,25 ATR på 4h giver samme dollarrisiko som 1 ATR på
15m), men så handler man reelt 15m-risiko med 4h-signaler, og stoppet ligger langt inde i
barens normale støj. Det er ikke en løsning, det er en omdøbning.

**Og spor B lukker døren helt.** XFA kræver fem vindende *dage*. På 4h er der 1-2 handler
om ugen; fem vindende dage tager måneder pr. payout-cyklus. På 15m med 1-3 handler dagligt
er det uger. **Kravet om dage sætter en nedre grænse på handelsfrekvensen, som en høj
timeframe ikke kan opfylde.**

**Konklusion: søgefeltet er 15m og nedad.** 5m og 3m er reelle kandidater — de koster mere
i R men giver luft mod MLL'en og flere chancer for en vindende dag. 1m er dyr (omk_R
0,096, be_WR 36,5%) og skal kunne bære det.

> **Forbehold:** kvadratrods-skalering er en **antagelse**, ikke en måling. Intradag
> skalerer ATR typisk *under* kvadratroden, fordi barens range indeholder spread og støj
> der ikke skalerer med tiden. De lave timeframes har derfor formentlig **højere** ATR end
> tabellen viser — hvilket gør dem billigere i R og dyrere i MLL-andel end vist. Retningen
> for 1h/4h er derimod ikke i tvivl: de er ude uanset skaleringsform. **B2 måler det
> rigtigt.**

### 5c. Forbeholdet på ATR-grundlaget

**Hele §5 står på ATR_15m = 0,168%, og det tal bygger på 60 dages historik**
(`venue_costs.md` linje 313, Yahoos intraday-cap). Ét volatilitetsregime på to måneder.

Retningen af en fejl er **ikke** entydig:

| ATR 15m | risiko_pr_handel_$ | pct_af_MLL | omk_R | be_WR_pct |
|---|---|---|---|---|
| 0,118% (−30%) | 72,18 | 3,61 | 0,0355 | 34,52 |
| **0,168% (basis)** | **102,06** | **5,10** | **0,0248** | **34,16** |
| 0,218% (+30%) | 131,94 | 6,60 | 0,0191 | 33,97 |

Højere ATR gør handlen **dyrere i MLL-andel og billigere i R** — omkostningen er fast pr.
handel mens 1R vokser. Man kan ikke aflæse fortegnet af én kolonne.

**Den bindende begrænsning er at 1 MNQ er udelelig.** Ved ATR +30% risikerer den mindst
mulige position 6,6% af MLL, og eneste håndtag er stopafstanden — 0,77 ATR for at komme
tilbage på 5,1%. Et strammere stop koster win rate, og hvor meget ved vi ikke. **Et
ATR-estimat 30% for lavt kan afgøre om 15m overhovedet er farbar.**

**Derfor afhænger §5 af B1.** Rækker datakildens futureshistorik, rapporteres ATR som
10./50./90. percentil og go/no-go vurderes på den høje ende. Rækker den ikke, regnes
sizingen med en eksplicit ATR-antagelse og en følsomhedskolonne.

### 5d. De fire veje

| vej | idé | status |
|---|---|---|
| 1 | Lavere timeframe | **Indsnævret til 15m og nedad** (§5b). Præcis valg kræver B2 |
| 2 | Sub-ATR stop | Kræver data og en strategi |
| 3 | Acceptér 5% | **Overlever. Valgt for spor A** |
| 4 | Større konto | Bortfaldet — $50K valgt |

**De fire veje er ikke valgmuligheder man vælger imellem. De er akser i ét sweep**, der
køres én gang mod en rigtig strategi på rigtige data. Vej 1 og 2 virker begge gennem win
rate, og win rate kommer fra en strategi.

### 5e. Hvad modellen ikke svarer på

- **Hvordan WR ændrer sig med stopbredden.** Vej 2 er åben.
- **Spor B.** Målfunktionen er "nå $3.000 før ruin" — altså Combine. XFA og LFA skal
  modelleres for sig, med "fem dage à $150+" som mål.
- **Klyngede tab.** Handlerne trækkes uafhængigt. Når der findes en strategi, skal modellen
  **blok-bootstrappe fra strategiens egen handelssekvens**.
- **Vejen inde i en handel.** Derfor to brudmodeller frem for ét tal.

---

## 6. Repoets tilstand

**94 passed, 4 skipped.** Committet og pushet (`6a5cd46`, 34 filer).

Apparatet er kopieret fra det gamle repo, byte-identisk: `backtest/` (costs, rnorm,
paired, metrics, report), `research/` (stats, portfolio, venues, diagnostics, tsmom,
daily_series, bias_engine), `data/indicators.py`, `strategies/base.py`, `config.yaml`.

**Kopien var ufuldstændig første gang.** Afhængighedsanalysen scannede toplinje-imports og
konkluderede "tre ekstra filer, ikke en kaskade". Den ramte forbi, fordi `paired.py:58` er
en **doven import inde i en funktion** — indrykket, og usynlig for et scan efter linjer
der begynder med `from` eller `import`.

**Runner-beslutningen:** `backtest/runner.py` er ikke kopieret og skal ikke kopieres. Den
trækker ccxt, yfinance, `data/fetcher.py`, `strategies/registry.py` og de tre
krypto-composites med sig. Propfirm-sporet bygger sin egen MNQ-runner, og `paired.py:58`
pointes mod den. `tests/test_paired.py::TestEndToEnd` er markeret `skip` med den
begrundelse i koden.

**Én kodeafvigelse:** `BaseStrategy.get_asset_class()` faldt tilbage på `"crypto"` for alt
ukendt — MNQ ville have fået den proportionale 0,20%-model. Den har nu `MNQ → index`.
Fallbacken er stadig en fælde for ethvert fremtidigt futures-symbol.

---

## 7. Arbejdsform og sessioner

Besluttet 2026-09-10.

| rolle | hvor | opgave |
|---|---|---|
| **Overblikssession** (denne) | Cowork | Holder den røde tråd, fælles forståelse af mål og midler. Sparring, idéer, verifikation af regler og tal. **Skriver PRD til hver fase — én ad gangen, når vi når dertil.** Vedligeholder `STRATEGI_PROPFIRM.md` og `claude/ANTAGELSER.md` |
| **Fasesession** | Cowork eller Code, én pr. fase | Udfører fasens PRD. Arbejder på egen branch |
| **Claude Code på Macen** | lokalt | Bygger og backtester |

Reglen der gør det til andet end en arbejdsdeling: **PRD'er skrives én ad gangen.** Skrev
vi alle faser nu, ville vi låse beslutninger vi endnu ikke har grundlag for — og fase 3's
PRD skal skrives med fase 2's resultater i hånden, ikke uden.

Git: nye branches pr. fase, ikke arbejde direkte på `main`.

### Testning kræver ikke Topstep

Backtest og paper-forward kører udelukkende på Macen med egne data. **Topstep-konto og
API-abonnement er først nødvendigt når evalueringen faktisk skal købes.** Det betyder at
alt frem til og med et validt paper-resultat kan bygges uden at betale noget.

Ét forbehold, og det er den samme fælde som på guld: **backtest på én kilde og live på
TopstepX' feed er to forskellige serier.** Vi så 20% forskel i ATR mellem to kilder for
samme instrument og periode, formentlig fordi bar-grænserne lå forskelligt. Før første
live-handel skal de to serier holdes op mod hinanden — det er ikke en detalje, det er
forskellen på om backtesten beskriver det marked botten handler i.

---

## 8. Metoderegler

1. **Præregistrér kriteriet før kørslen.**
2. **Konfidensinterval på alt.** Krydser det nul, er resultatet uafgjort.
3. **Mindste detekterbare forskel beregnes før testen.**
4. **Gates hører til i live, aldrig i backtesten.**
5. **Alle tal både brutto og netto.**
6. **Enheden står i kolonnenavnet.**
7. **En gebyrsats tæller først når den er verificeret for den kanal botten bruger.**
8. **Stop efter hver kørsel.** Ingen konfigurationsændringer, ingen strategiforslag.
9. **Egne idéer valideres ikke videnskabeligt** — de vurderes på: kan den automatiseres,
   passer den ind, hvor omfattende er ændringen.
10. **Alt andet sammenlignes mod nyeste litteratur.**
11. **Der sizes ikke efter punktestimater.** Percentiler, og go/no-go på den ende hvor det
    gør ondt.

---

## 9. Åbne spørgsmål

Bogstavet er fasen, tallet er rækkefølgen inden for fasen.

### A. Besvaret

| # | spørgsmål | svar |
|---|---|---|
| A1 | Positionsstørrelse mod MLL | §5a. 1 MNQ, 1-ATR-stop. Forbehold for ATR-grundlaget |
| A2 | Profitmål og priser pr. kontostørrelse | §3. $3.000 / $2.000 / $49-95 md |
| A3 | Følger markedsdata med API-adgangen? | §3. Level 1 gratis i Combine og XFA. Level 2 $38/md, unødvendig |
| A4 | Tæller en ordre fra telefonen som "personal device"? | Bortfaldet. Ordren afsendes fra Macen |
| A5 | Hvordan ser Topsteps trin faktisk ud? | §3. Tre trin, ikke to. XFA er simuleret men betaler |
| A6 | Kan 1h/4h bruges? | §5b. **Nej.** 10% og 20% af MLL pr. handel, og for få dage til spor B |

### B. Før kode — blokerende, i rækkefølge

| # | spørgsmål | afhænger af | hvorfor den blokerer |
|---|---|---|---|
| **B1** | **Datagrundlag.** Hvilke kilder findes, hvor dybt går futureshistorikken, hvad er gratis, og stemmer barerne overens på tværs af kilder? | — | **Der er ingen prisdata i repoet. Intet kan backtestes.** Se `claude/PRD_FASE1_DATAGRUNDLAG.md` |
| **B2** | **ATR-fordeling pr. timeframe** (15m/5m/3m/1m, RTH og døgn) som 10./50./90. percentil | B1 | Afgør vej 1 præcist og efterprøver hele §5 |
| **B3** | **Reelt spread pr. tidsblok** | B1 | **Kan formentlig ikke måles fra OHLC-barer** — spread kræver bid/ask. Første delopgave er at afgøre om det overhovedet kan måles, og hvorfra |
| **B4** | **Edge-hypotese til indeksfutures** | — | Uden den har vi et måleapparat uden noget at måle. **Det egentlige projekt.** Eget dokument |
| **B5** | **Understøtter MNQ 2:1, eller skal vi til 1,5:1?** | B1 + B4 | Ved 1,5:1 springer be_WR fra 34,2% til ~40% og hele §5 er ugyldig |

### C. Før live

| # | spørgsmål |
|---|---|
| C1 | **Tilstandsgenopretning ved opstart.** Uden den er `KeepAlive` en risiko frem for en sikkerhed |
| C2 | Netværkstab midt i en åben position |
| C3 | Fallback når Telegram er nede |
| C4 | Slippage på stops, målt |
| C5 | Eksplicit regel i koden når MLL nærmer sig |
| C6 | Hvad koster markedsdata på LFA? |
| C7 | **Afvigelse mellem backtest-serien og TopstepX' feed**, målt (§7) |

---

## 10. Definition af "klar til at bygge"

Vi bygger ikke fordi det føles som næste skridt. Vi er klar når **alle fem** holder:

1. **B1-B3 er besvaret** — der findes data, og ATR er målt som fordeling.
2. **B4 har mindst én kandidat** med et svar på "hvorfor betaler nogen mig for det her?"
3. **B5 er afgjort** — vi ved hvilket RR instrumentet understøtter.
4. **`claude/ANTAGELSER.md` har ingen S'er på kritisk vej** — eller de tilbageværende skøn
   har en følsomhedskolonne der viser at konklusionen holder i begge ender.
5. **Fælles forståelse af mål og midler.** Begge parter kan gengive hvad vi bygger, hvorfor,
   og hvad der ville få os til at stoppe.

---

## 11. Hvad der IKKE er en del af dette spor

- **TSMOM.** Ude. Dokumenteret i `STRATEGI_TSMOM.md` som reference.
- **Krypto.** Omkostningen på 15m gør sporet dødt for daytrading. Bemærk at
  `STRATEGI_DAYTRADING.md` §6's edge-kandidater alle er krypto-specifikke og **ikke**
  overføres — se B4. Det dokument er en historisk protokol og rettes ikke bagud.
- **De 5-10K egen kapital.**
- **Aktie-execution.** Udskudt.

---

## 12. Åbne observationer fra det eksisterende projekt

- **Break-even-stop og trailing stop fungerer muligvis ikke som håbet.** Mads' observation
  fra live paper-handler. Ikke målt. Kandidat til en falsifikationstest.
- **Prisen rammer ofte lige akkurat ikke TP**, hvorefter den går mod SL eller lukkes af
  tidsstop. Det var begrundelsen for `tp_rr_ratio` 1,5 i det gamle projekt — og præcis
  grunden til at B5 findes.

---

## Kilder

- help.topstep.com: TopstepX API Access, Trading Combine Parameters, Live Funded Account
  Parameters, Maximum Loss Limit, Daily Loss Limit, Consistency Target, TopstepX
  Commissions and Fees, Payout Policy, Level 1 and Level 2 Market Data, Pricing
- topstep.com: how-it-works, express-funded-account-rules, live-funded-account-rules,
  blog/prop-firm-drawdown-rules
- cmegroup.com — Micro E-mini Nasdaq-100 contract specifications
- NQ-niveau 29.639,50 pr. 2026-09-07
- `research/output/venue_costs.md` — gammelt repo, læst. Tradovate-baseret
- `research/output/mll_ruin.md` — dette repo, §5a
