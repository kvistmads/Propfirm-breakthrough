# Propfirm-sporet

**Status:** påbegyndt 2026-09-09. Opdateret samme dag efter første arbejdssession.
Repoet står, apparatet er kopieret og testene er grønne. **Åbent spørgsmål 1 og 2 er
besvaret.** Ingen konto åbnet, ingen strategi bygget.

Søsterdokumenter: `STRATEGI_TSMOM.md`, `STRATEGI_DAYTRADING.md`.

---

## 1. Hvad sporet er

Et separat handelssystem der skal **bestå en propfirm-evaluering og derefter holde den
funded konto i live**. Kapitalen er propfirmaets, ikke Mads'.

To strategier, ikke én:

- **Eval-strategien** skal nå profitmålet inden for reglerne. Den må være aggressiv,
  fordi konsekvensen af at fejle er et nyt evalueringsgebyr — ikke tab af egne penge.
- **Konto-strategien** skal holde kontoen i live bagefter. Den må være defensiv,
  fordi konsekvensen af at fejle er at hele arbejdet er væk.

De to har modsatrettede tabsfunktioner. Det er grunden til at de er to strategier og
ikke én med et parameter skruet på.

**Efter ruinmodellen (§5) ved vi at spændingen er mindre end frygtet:** de to
strategiers optimale sizing ligger som naboer, ikke i hver sin ende.

### Afgrænsning

- **Nyt repo.** Ikke en ny main i det eksisterende. Begrundelsen er Mads' egen:
  "knald eller fald, en forkert fejl på det forkerte tidspunkt, konto død."
- **Apparatet kopieres, deles ikke.** Gennemført — se §6.
- **De 5-10K er ikke en del af dette spor.** De hører til det eksisterende
  krypto-paperprojekt.

---

## 2. Beslutninger truffet

| Spørgsmål | Valg |
|---|---|
| Kapital | Udelukkende propfirm-kapital |
| Firma | Topstep er førstevalg, ikke låst |
| **Kontostørrelse** | **$50K — valgt 2026-09-09** |
| Mål | Bestå eval, behold funded konto |
| Autonomi | Backtest og paper-forward **fuldauto**; funded live **semi**, udvides senere. Combine-fasen ikke afgjort |
| Session | US RTH som udgangspunkt; blanding med døgndrift skal måles først |
| Instrument | MNQ (mikro Nasdaq) |
| **Daily Loss Limit** | **Slået til ($1.000 i Combine)** |
| **Ruinmål** | **Drawdown, 1:1 med Topsteps egen mekanik — ikke "tab i træk"** |

Semi-først er valgt bevidst. Fuldt autonomt er tilladt hos Topstep, så det er ikke en
regelbegrænsning — det er en tillidsbegrænsning.

---

## 3. Topstep's regler — primærkilder

Alt herunder er fra Topstep's eget help center, hentet og genverificeret 2026-09-09.
**Regler ændrer sig; slå dem op igen før noget bygges.**

### Automatisering — tilladt

> "Custom automated strategies and bots are allowed via the TopstepX / ProjectX API,
> subject to standard platform rules and our prohibition on high-frequency trading (HFT)."

API-adgang koster **$29/md, $14,50 med koden `topstep`**. REST + WebSocket.
Ingen sandbox — "API orders are final". Topstep yder ingen support på implementeringen.

### Den bindende begrænsning — hvor koden kører

> "All trading activity must originate from your personal device. The use of VPS, VPNs,
> and remote servers is prohibited by Topstep's Terms of Use."

**Det udelukker en cloud-server.** Botten skal køre på Mads' egen maskine. Det udelukker
ikke at han er på arbejde imens — reglen handler om *hvor koden kører*.

Konsekvens: Macens oppetid bliver en del af strategien. Skal løses ordentligt før første
live-handel, ikke bagefter.

### Kontoparametre — verificeret pr. kontostørrelse

| konto | profitmål_$ | MLL_$ | mål/MLL | bedste dag maks_$ | maks kontrakter | maks mikroer |
|---|---|---|---|---|---|---|
| $50K | 3.000 | 2.000 | **1,50** | 1.500 | 5 | 50 |
| $100K | 6.000 | 3.000 | 2,00 | 3.000 | 10 | 100 |
| $150K | 9.000 | 4.500 | 2,00 | 4.500 | 15 | 150 |

**mål/MLL er sizing-invariant** — forholdet ændrer sig ikke når man skruer på
kontraktantallet. $50K er derfor strukturelt den letteste konto at bestå (1,50 mod 2,00),
og det er en selvstændig grund til valget ud over prisen.

**Combine-pris:** $50K koster $49/md på standard-sporet (+$149 aktiveringsgebyr pr.
optjent funded konto) eller $95/md på sporet uden aktiveringsgebyr. Reset koster det
samme som en måned. Sporet kan ikke ændres efter køb.

### Maximum Loss Limit — mekanikken, præcist

Det her er den vigtigste halve side i dokumentet, fordi to udsagn der lyder modstridende
begge er sande og handler om hver sin ting:

| | |
|---|---|
| MLL **trailer** på | **dagsslutsaldo**. Aldrig nedad |
| MLL **låser** | når den når startsaldoen ($50.000), dvs. ved dagsslutsaldo $52.000 |
| MLL **brydes** på | **net P&L i realtid, urealiseret tæller med** → øjeblikkelig likvidering |
| Intradag give-back | tæller **ikke** mod trailet. Kun mod bruddet |

**Trailet er dagsslut, bruddet er realtid.** Topstep er altså ikke intraday-trailing:
et løb til +$800 der gives tilbage til +$300 koster ingenting i gulv. Topsteps eget
eksempel: start 50.000 / MLL 48.000 → dag 1 +500 → saldo 50.500, MLL 48.500 → dag 2
−500 → saldo 50.000, MLL bliver på 48.500.

Konsekvensen for sizing er at risikoen **ikke er jævnt fordelt** over de $3.000:

| fase | saldo_$ | luft_til_MLL_$ |
|---|---|---|
| start | 50.000 | 2.000 |
| under opbygning | 50.000–52.000 | altid ~2.000 — gulvet følger med op |
| efter lås | > 52.000 | saldo − 50.000, vokser frit |
| profitmål nået | 53.000 | 3.000 |

To tredjedele af eval-løbet ligger i det stramme felt, den sidste tredjedel i det løse.

### Daily Loss Limit — ikke det samme som MLL

Dokumentets tidligere udgave blandede de to. De er forskellige grænser med forskellige
tal på forskellige stadier:

| grænse | Combine $50K | Funded $50K | konsekvens ved brud |
|---|---|---|---|
| Maximum Loss Limit | 2.000 | ikke separat verificeret | konto død |
| Daily Loss Limit | **1.000 — valgfri** | 2.000 | positioner flades, pause til 17:00 CT. **Ikke** et regelbrud |

Funded-DLL justeres automatisk ned når saldoen falder under $10K/$5K over startsaldoen
og revideres om fredagen. Kontoen likvideres automatisk under $1.000, og lukkes efter
30 dage uden handel.

**Ved 1-3 mikroer binder DLL'en aldrig.** Værst tænkelige dag ved 3 kontrakter × 3
handler er $918, under de $1.000. Den er slået til fordi den ikke koster noget, men den
beskytter ikke noget ved denne størrelse — den begynder først at virke over ~10 kontrakter.

### Konsistens — hæver målet, dumper dig ikke

> "Your single best day of profit must stay at or below 50% of your Profit Target."

Overskrides det, **hæves profitmålet** — man dumper ikke. Bestå kræver derfor
`profit >= max(3.000, 2 × bedste dag)`. Sådan er den implementeret i ruinmodellen.

**Minimum handelsdage: to.** *"You can pass in as few as two days."*

**Ikke verificeret endnu:** om markedsdata følger med API-adgangen eller er et separat
abonnement, og om funded-MLL afviger fra Combine-MLL.

---

## 4. Omkostningsgrundlaget

**Gebyret er nu verificeret for den kanal botten faktisk bruger.** Det gamle tal på
0,023 R kom fra `research/output/venue_costs.md` linje 289 og var regnet på **Tradovate
Free** — ikke TopstepX. Præcis MEXC-lektionen, og den blev fanget.

Kontrakten (CME): MNQ er **$2 pr. indekspoint, tick 0,25 = $0,50**.
Gebyret (TopstepX): **$1,22 rundtur** = $0,50 kurtage + $0,71 børs + $0,01 NFA. Samme
sats i Combine, Express Funded og Live Funded.

Ved NQ 29.639,50 og ATR_15m 0,168% er 1 ATR = 49,79 point = **R = $99,59** pr. kontrakt:

| grundlag | gebyr_$ | spread_$ | slippage_$ | i_alt_$ | omk_R | be_WR_pct ved 2:1 |
|---|---|---|---|---|---|---|
| gammelt tal (Tradovate Free) | 1,50 | 0,75 | — | 2,25 | 0,023 | 34,1 |
| verificeret, gebyr + spread | **1,22** | 0,75 | — | **1,97** | **0,0198** | **33,99** |
| **som koden faktisk regner** | 1,22 | 0,75 | 0,50 | **2,47** | **0,0248** | **34,16** |

**Tredje række er den der gælder.** Dokumentets gamle 0,023 R var *uden* slippage, men
omkostningsmodellen i repoet trækker 0,5 tick pr. side. Det tal backtesten bruger er
**0,0248 R**. De to må ikke krydslæses, lige så lidt som 2:1 og 1,5:1 må.

Spread på 1,5 tick er stadig et **skøn**, markeret som sådan i `config.yaml`. Åbent
spørgsmål 6.

**Omkostningsspørgsmålet er lukket.** Det der mangler er en edge — og §5 sætter nu tal
på præcis hvor meget det mangler.

### Hvad tallene stadig ikke indeholder

- **Slippage på stops** ud over de modellerede 0,5 tick. Et stop i en hurtig bevægelse
  fylder dårligere. Ikke målt.
- **Spread uden for US RTH.** 1,5 tick er et RTH-skøn. Ønsket om døgndrift rammer her.
- **Faste omkostninger.** API $14,50/md + Combine $49-95/md. På en evalueringskonto er
  de reelle og løbende — og ruinmodellen viser at *tid* er den skjulte pris ved lav risiko.

---

## 5. Positionsstørrelse mod MLL — BESVARET

Kørt 2026-09-09. Monte Carlo, 20.000 stier pr. celle, horisont 200 handelsdage,
mekanikken 1:1 med §3. Kode: `research/mll_ruin.py`. Rapport:
`research/output/mll_ruin.md` + `.csv`.

**Præregistreret kriterium:** vej 3 ("acceptér 5% pr. handel") forkastes hvis
P(ruin før profitmål) > 50% ved WR 40%, 1 MNQ og 1-ATR-stop.

**Resultat: P(ruin) = 10,09% [9,7–10,5].** Pessimistisk brudmodel 11,84% [11,4–12,3].
**Ikke falsificeret.**

### Gitteret ved WR 40%, netto

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

### Hvad tallene siger

**Bekymringen vendte den forkerte vej.** De 5% af MLL pr. handel er ikke et problem —
de er tæt på det bedste valg for evalueringen. Grunden står i §3: profitmålet er 1,5 ×
MLL. Man *skal* tage risiko for at komme i mål, og skruer man ned, når man aldrig frem.

**Den lave-risiko-vej koster tid, ikke sikkerhed.** 1 kontrakt med 0,5-ATR-stop har
1,1% ruin — og **41,6% når aldrig i mål på 200 handelsdage**. Det er ti måneders
abonnement til $49-95/md for et udfald der hverken er bestået eller dødt.

**Omkostninger koster 1,4 til 22,2 procentpoint** af bestå-sandsynligheden, med det
største udslag netop hvor edgen er tyndest (1 kontrakt, 0,5 ATR: 79,5% brutto → 57,3%
netto).

**Og det tal der betyder mest:** hen over hele sizing-gitteret spænder bestå fra 57 til
89%. Hen over win rate spænder den fra **1 til 99%**. Kontrolcellen uden edge (WR 34%,
under break-even) dør i 72% af stierne uanset sizing. **Sizing er andenordens. Edgen er
førsteordens.** Dokumentets egen linje — "det der mangler er en edge" — er hermed et tal.

**Eval og funded er forenelige.** 1 kontrakt / 1,0 ATR vinder på eval (88,6% mod 86,0%,
CI'erne overlapper ikke). 1 kontrakt / 0,75 ATR halverer ruin (5,3% mod 10,1%) for 30
dage mere. Det er nabo-indstillinger, ikke modsætninger. Den spænding §1 advarede om
findes, men den er lille.

### De fire veje, afgjort

| vej | status |
|---|---|
| 1. Lavere timeframe | **Ikke afgjort.** Kræver målt ATR på 5m/3m/1m. Modellen antager 15m |
| 2. Sub-ATR stop | **Ikke afgjort.** Modellen holder WR fast; i virkeligheden falder WR når stoppet strammes. Kræver data |
| 3. Acceptér 5% | **Overlever.** Ruin 10,1%, bestå 88,6%. Bedste celle i gitteret |
| 4. Større konto | **Bortfaldet.** $50K er valgt, og mål/MLL 1,50 gør den strukturelt lettest |

### Hvad modellen ikke svarer på

- **Hvordan WR ændrer sig med stopbredden.** Vej 2 er stadig åben.
- **Konto-strategien.** Målfunktionen der er implementeret er "nå $3.000 før ruin" —
  altså evalueringen. Konto-strategien har en anden målfunktion (overlev og tag payouts)
  og kræver payout-reglerne verificeret først.
- **Vejen inde i en handel.** Derfor to brudmodeller frem for ét tal. Spændet mellem dem
  er modelusikkerheden, og den er større end stikprøveusikkerheden.

---

## 6. Repoets tilstand

**Testene er grønne: 94 passed, 4 skipped.**

Apparatet er kopieret fra det gamle repo og er byte-identisk på de filer der kom med:
`backtest/` (costs, rnorm, paired, metrics, report), `research/` (stats, portfolio,
venues, diagnostics, tsmom, daily_series, bias_engine), `data/indicators.py`,
`strategies/base.py`, `config.yaml`.

**Kopien var ufuldstændig første gang, og det var lærerigt.** Den forrige sessions
afhængighedsanalyse scannede toplinje-imports og konkluderede "tre ekstra filer, ikke en
kaskade". Den ramte forbi, fordi `paired.py:58` er en **doven import inde i en
funktion** — indrykket, og derfor usynlig for et scan efter linjer der begynder med
`from` eller `import`.

**Runner-beslutningen:** `backtest/runner.py` er ikke kopieret og skal ikke kopieres.
Den trækker ccxt, yfinance, `data/fetcher.py`, `strategies/registry.py` og de tre
krypto-composites med sig — kopieres den, *er* det nye repo det gamle repo. Propfirm-
sporet bygger sin egen MNQ-runner, og `paired.py:58` pointes mod den.
`tests/test_paired.py::TestEndToEnd` er markeret `skip` med den begrundelse i koden.

`research/run_flip_oos_test.py` er bevidst ikke med — den testede en forkastet hypotese
fra det gamle projekt. `tests/test_costs.py::TestOutOfSampleSplit` er fjernet med den.

**Én kodeafvigelse fra det gamle repo:** `BaseStrategy.get_asset_class()` faldt tilbage
på `"crypto"` for alt ukendt. MNQ ville have fået den proportionale 0,20%-model i stedet
for kontraktmodellen. Den har nu `MNQ → index`. Det er stadig en fallback-fælde for
ethvert fremtidigt futures-symbol — koblingen mellem `costs.py` og `base.py` bør klippes
over og erstattes af en eksplicit symbol-til-klasse-tabel i `costs.py`.

MNQ er lagt ind som symbol-override under `backtest.costs.symbols` med de verificerede
tal fra §4.

---

## 7. Signal, mobil og infrastruktur

Uændret fra første udgave.

Semi-autonom drift er ikke kun et tillidsvalg — den er også den sikre vej i forhold til
personal-device-reglen, fordi **ordren afsendes fra Macen** uanset hvad. Telefonen sender
kun et "ja".

### Arkitektur — pilen vender udad

    Mac finder setup
      -> sender signal ud via Telegram-bot
      -> Mads trykker ja på telefonen
      -> Macen poller efter svaret og lægger ordren

Ingen åbne porte, ingen tunnel, ingen angrebsflade mod den maskine der handler.
Kræver en fallback for det tilfælde at Telegram er nede.

### Bekræftelsesgaten gælder KUN live med rigtige penge

    backtest        fuldauto    strategiens rå egenskaber
    paper-forward   fuldauto    referencen, kører permanent
    Combine         ÅBENT       ingen kapital på spil, kun evalueringsgebyret
    funded live     semi        bekræftelse via Telegram

En testfase hvor Mads skal bekræfte, måler hans vagtplan lige så meget som strategien.
**Paper-instansen bliver ved med at køre fuldautomatisk parallelt med den
semi-automatiske live-instans.** Forskellen mellem de to kurver *er* prisen for
bekræftelsesgaten — direkte observeret frem for estimeret.

### Beslutninger for live-fasen

| | |
|---|---|
| Kanal | Telegram-bot |
| Timeout | Signalet udløber. Botten gør intet hvis der ikke svares i tide |
| Svarvindue | 5 minutter |
| Uden at spørge: lukke position | **Tilladt** |
| Uden at spørge: flytte stop/TP | **Tilladt** |
| Uden at spørge: åbne position | **Ikke tilladt** |

Tilladelserne er asymmetriske med vilje. At lukke en position kan aldrig skabe ny
eksponering, og en bot der skal bede om lov til at redde kontoen mens telefonen ligger i
et skab er farligere end en der bare gør det.

**Krav:** botten logger både hvad den ville have gjort og hvad der faktisk skete.
Bygges ind fra dag ét.

### Infrastruktur

`RunAtLoad` + `KeepAlive` + `ThrottleInterval`, kopieret fra
`com.madskvist.tradingbot.plist`. **Men `KeepAlive` er farligere på en prop-konto.**
Dør botten med en åben position og genstartes, må den ikke tro at den står flad — MLL'en
tæller urealiseret tab i realtid.

**Krav: tilstandsgenopretning ved opstart.** Botten spørger Topstep "hvad har jeg åbent?"
før den gør noget som helst andet.

---

## 8. Metoderegler

Ikke til forhandling. De er grunden til at fire hypoteser blev afvist i stedet for
rationaliseret — og til at det forkerte gebyrtal blev fanget før det kom i en model.

1. **Præregistrér kriteriet før kørslen.**
2. **Konfidensinterval på alt.** Krydser det nul, er resultatet uafgjort.
3. **Mindste detekterbare forskel beregnes før testen.**
4. **Gates hører til i live, aldrig i backtesten.**
5. **Alle tal både brutto og netto.**
6. **Enheden står i kolonnenavnet.**
7. **En gebyrsats tæller først når den er verificeret for den kanal botten faktisk
   bruger.** Fanget igen 2026-09-09: Tradovate Free mod TopstepX.
8. **Stop efter hver kørsel.** Ingen konfigurationsændringer, ingen strategiforslag.
9. **Egne idéer skal ikke valideres videnskabeligt** — de vurderes på: kan den
   automatiseres, passer den til botten, hvor omfattende er ændringen.
10. **Alt andet sammenlignes mod nyeste litteratur.**

---

## 9. Åbne spørgsmål, i den rækkefølge de skal besvares

**Besvaret:**

1. ~~Positionsstørrelse mod MLL.~~ **Lukket, §5.**
2. ~~Topstep's profitmål og Combine-pris pr. kontostørrelse.~~ **Lukket, §3.**
4. ~~Tæller en ordre afsendt fra telefonen som "your personal device"?~~ **Bortfaldet.**

**Før kode:**

3. Følger markedsdata med API-adgangen, eller er det et separat abonnement?
5. **Historik til backtest.** Nu forfremmet: den er en *forudsætning* for at afgøre vej 1
   og vej 2, ikke noget der kommer bagefter. `londonstrategicedge.com` har 14 opløsninger
   inkl. 15m, bulk Parquet, gratis nøgle, licens der tillader egen research og trading.
   **Futures-dybden er ikke oplyst.** Test: hent NQ 15m, se hvor langt tilbage det går,
   hold en dag op mod Yahoo.
6. **Reelt spread på MNQ**, målt frem for gættet — og målt pr. tidsblok, så ønsket om
   døgndrift kan vurderes i stedet for antages.
11. **Målt ATR pr. timeframe** (15m/5m/3m/1m, RTH og døgn). Uden den kan vej 1 ikke
    afgøres. Afhænger af 5.
12. **Payout-reglerne**, så konto-strategiens målfunktion kan defineres. Uden dem er
    §5's ruinmodel kun besvaret for eval-halvdelen.

**Før live:**

7. **Tilstandsgenopretning ved opstart.** Uden den er `KeepAlive` en risiko.
8. Netværkstab midt i en åben position.
9. Fallback når Telegram er nede.
10. Slippage på stops, målt.
13. Hvad gør systemet når MLL'en nærmer sig? Eksplicit regel i koden, ikke en konsekvens
    af at strategien tilfældigvis holder op med at handle.

---

## 10. Hvad der IKKE er en del af dette spor

- **TSMOM.** Ude af projektet. Dokumenteret i `STRATEGI_TSMOM.md` som reference.
- **Krypto.** Omkostningen på 15m gør sporet dødt for daytrading.
- **De 5-10K egen kapital.** Hører til det eksisterende projekt.
- **Aktie-execution.** Udskudt.

---

## 11. Åbne observationer fra det eksisterende projekt

Ikke undersøgt, men noteret så de ikke fordamper:

- **Break-even-stop og trailing stop fungerer muligvis ikke som håbet.** Mads'
  observation fra live paper-handler. Ikke målt. Kandidat til en falsifikationstest.
- **Prisen rammer ofte lige akkurat ikke TP**, hvorefter den går mod SL eller lukkes af
  tidsstop. Det var begrundelsen for `tp_rr_ratio` 1,5 i det nuværende projekt.

Bemærk at propfirm-sporets tabeller regner med **2:1**, ikke 1,5:1. Ved 2:1 med
omkostning 0,0248 R er break-even 34,16%; ved 1,5:1 er den ~40%. **De to må ikke
krydslæses.**

---

## Kilder

- help.topstep.com: TopstepX API Access, Trading Combine Parameters, Live Funded Account
  Parameters, What is the Maximum Loss Limit, Daily Loss Limit in the Trading Combine,
  What is the Consistency Target, TopstepX Commissions and Fees, Topstep Pricing
  (alle 2026-09-09)
- topstep.com/blog/prop-firm-drawdown-rules — end-of-day-drawdown-modellen
- cmegroup.com — Micro E-mini Nasdaq-100 contract specifications
- NQ-niveau 29.639,50 pr. 2026-09-07
- `research/output/venue_costs.md` — gammelt repo, læst. Bemærk: Tradovate-baseret
- `research/output/mll_ruin.md` — dette repo, §5
