# Fase 2 — præregistrering: valgregel, vinduer og operationalisering af K2-K5

**Skrevet:** 2026-09-13, før gitteret er kørt. Committet før kørslen (metoderegel 13).
**Grundlag:** `PRD_FASE2_RUINMODEL.md` §3 (K1-K5) og Mads' svar i fasesessionen
2026-09-13 på de punkter PRD'en ikke fastlagde. Hvor en regel nedenfor er fasesessionens
egen præcisering af et svar, står det.

**Allerede kørt før denne fil:** K1 på commit `0aa23bc`. 432 af 432 andele inden for v1's
95%-CI, alle identiske op til v1's afrunding (største afvigelse 0,005 pp). K1 køres igen på
den endelige kode før gitteret, fordi trækrækkefølgen ændres for at parre stierne (se
"Parring"). Gitterkørslen nægter at starte hvis K1-resultatet ikke er fra den kode der kører.

Intet i gitteret er set, da dette blev skrevet. Kendt på forhånd fra fase 1's fordelinger:
15m med 1-ATR-stop ligger på ~14% af MLL ved p90 og fejler K3's ≤ 10% i begge vinduer.

---

## 1. Data og vinduer

| vindue | serie | afgrænsning | hvad køres |
|---|---|---|---|
| **Primært** | NQ.v.0 1m, Databento GLBX.MDP3, RTH | ET-dato ≥ 2019-05-06 til seriens sidste bar (2026-09-10) | **Hele gitteret** |
| Reference A | samme | K3-årene 2016-2026 (fase 1's go/no-go-grundlag) | Kun valgt celle og nummer to, WR 40% absolut. Afstemning mod §5 |
| Reference B (K5) | samme | Seneste 12 måneder: ET-dato 2025-09-11 → 2026-09-10 | Kun valgt celle og nummer to, WR 40% absolut |

- 3m/5m/15m aggregeres fra 1m som i fase 1. ATR (Wilder 14, brudhåndtering) regnes på hele
  RTH-serien før vinduet skæres, så opvarmningen aldrig starter forfra. Barer med ATR ≤ 0
  eller NaN udelades, som i `atr_fordeling.fordeling`.
- **Instrument.** Mads besluttede 2026-09-13 at primærvinduet skulle ligge på MNQ. MNQ-1m-barer
  ligger ikke i cachen, og et udtræk ville koste ~$9,46. Mads valgte ingen udgift: **NQ fra
  2019-05-06**. Instrumenttjekket NQ mod MNQ udgår, og "ATR i procent er den samme på NQ og
  MNQ" står i rapporten som antagelse (A). Risikoen kommer dermed fra NQ og spreadet fra MNQ.
- **NQ-niveau:** sidste RTH-luk i serien, læst fra data (29.138,00, 2026-09-10 15:59 ET). Ét
  fast niveau for alle træk.
- **Omkostning:** `backtest.costs.rundtur_dekomponering`, RTH: $1,22 + 1,73 tick spread + 2 ×
  0,5417 tick realiseret slippage = $2,627. Brutto = $0.

## 2. Model

- 20.000 stier pr. kørsel. Horisont 200 handelsdage. 1-3 handler pr. dag, ligefordelt. Seed
  20260909 i **alle** celler.
- R trækkes pr. handel fra cellens empiriske ATR-fordeling (med tilbagelægning), ved det faste
  NQ-niveau.
- **Parring** (Mads: parrede stier, samme seed, samme uniforme træk, tærsklet ved hver celles
  WR). Vinder/taber-uniformen og antal handler pr. dag trækkes i hver slot uanset stiens
  tilstand. ATR trækkes som kvantil *u* af cellens sorterede fordeling, med samme *u* i alle
  celler. Sti *i* ser dermed samme tilfældighed i hver celle; kun tærsklerne er forskellige.
  *Fasesessionens præcisering:* kvantilparringen af ATR. Den ændrer ikke fordelingen af hvert
  enkelt træk, som stadig er ligefordelt over de målte barer.
- **Forskelle mellem to andele på samme stier** får Newcombes hybrid score-interval for parrede
  andele (Newcombe 1998, metode 10). Enkeltandele får Wilson-interval.

## 3. WR-akser

| akse | værdier |
|---|---|
| Absolut | 34 · 37 · 40 · 45 % |
| Relativ | be_WR · be_WR+3 · be_WR+6 · be_WR+11 pp |

- `be_WR_pct_ved_middel_R = (1 + omk_usd / E[R_usd]) / 3 × 100`, hvor E[R_usd] er middelværdien
  af **den array simulationen sampler fra**, beregnet i koden. Det er nulmodellen: nul
  forventet P&L pr. handel. Brutto-nulmodellen er 1/3.
- §5a's gamle kolonne regnet på R_p50 står ved siden af som `be_WR_pct_ved_R_p50`.
- **Selvtjek af nulmodellen:** for hver af de 12 nul-celler i primærvinduet (netto, begge
  brudmodeller) skal realiseret middel-P&L pr. taget handel have et 95%-CI der indeholder 0.
  Hver taget handel tæller med sit nominelle udfald, også den der slår kontoen ihjel. Holder
  det ikke, er formlen og simulationen uenige, og det rapporteres som fejl.

## 4. Valgregel

| led | regel |
|---|---|
| Kandidatfelt | De 12 celler med 1 kontrakt (15m/5m/3m/1m × stop 1,00/0,75/0,50 ATR), RTH, primært vindue |
| Målfunktion | `bestaa_pct_netto_pess` ved **WR 40% absolut**. Ikke `bestaa_pp_over_nulmodel` — nulmodellen er diagnose, ikke mål |
| Bibetingelse | `risiko_pct_af_MLL_netto_ved_ATR_p90 ≤ 10`. **K3 er et filter** |
| Valg | Højeste målfunktion blandt cellerne der klarer bibetingelsen |
| Uafgjort | Parret CI på forskellen `bestaa_pct_netto_pess(valgt) − bestaa_pct_netto_pess(nummer to)`. Krydser det nul, er valget **uafgjort**: begge celler rapporteres, der vælges ikke |
| Tiebreak | Kun ved uafgjort: den af de to med lavest `risiko_pct_af_MLL_netto_ved_ATR_p90` bruges til K4, K5, følsomhed og konstant-sammenligningen. Skrives eksplicit som tiebreak, ikke som resultat |
| Uden bibetingelse | Maksimum uden K3-filteret rapporteres også. Er det en anden celle, vises begge og forskellen i beståelsesrate med parret CI |
| Robusthed | Samme regel anvendt på den relative akse ved **be_WR + 6 pp**. Rapportér om valget skifter. Skifter det, er cellen et artefakt af sammenligningsgrundlaget og skrives sådan |
| K4 og K5 | Tjekkes på den valgte celle bagefter. En fejl vælger ikke om; den markerer valget som ikke brugbart endnu og siger hvorfor |

*Fasesessionens præcisering:* be_WR + 6 pp er den relative akses modstykke til WR 40% absolut.
Det gamle gitter lå med 34% omtrent på break-even, og 40 = 34 + 6.

## 5. Kriterierne operationaliseret

Alle ved 1 kontrakt, netto og primært vindue, medmindre andet står.

| # | tærskel (PRD §3) | holdt | ikke holdt | uafgjort |
|---|---|---|---|---|
| **K1** | hver celle inden for sit 95%-CI | alle 432 andele inden for v1's Wilson-CI, og de deterministiske kolonner er ens | ellers. **Så stopper alt** | — |
| **K2** | ∃ celle med P(ruin) ≤ 20% ved WR 40%, pessimistisk | mindst én celle med Wilson-øvre ≤ 20% | alle 12 har Wilson-nedre > 20% | ellers |
| **K3** | risiko p90 ≤ 10 på valgt celle | en celle blev valgt (filteret) | ingen af de 12 klarer ≤ 10. Så vælges ingen celle | — (deterministisk på hele fordelingen) |
| **K4** | ≤ 5 pp mellem brudmodellerne på valgt celle | parret CI for `ruin_pess − ruin_opt` ved WR 40% har øvre ≤ 5 | nedre > 5 | ellers |
| **K5** | samme celle under 12 måneder | valgreglen anvendt på {valgt, nummer to} i reference B giver den valgte: den klarer filteret, og enten er forskellens parrede CI > 0, eller nummer to fejler filteret | den valgte fejler filteret, eller CI < 0 | CI krydser nul |

Er der kun én celle der klarer filteret, er valget entydigt, og K5 holder hvis den stadig
klarer filteret under 12 måneder.

## 6. Fordeling mod konstant — ét tal (PRD §6.4)

Valgt celle, WR 40%, netto, samme stier:

- **Det ene tal:** `ruin_pct_netto_pess(fordeling) − ruin_pct_netto_pess(R fast ved E[R])`, med
  parret CI. Samme forventning, nul spredning, så forskellen skyldes fordelingens varians og
  intet andet.
- Rapporteres også: samme forskel mod **R fast ved R_p50**, som svarer til hvad den gamle model
  reelt gjorde, samt begge for den optimistiske brudmodel.

## 7. Følsomhed (PRD 4.5)

Valgt celle, WR 40% absolut, netto, begge brudmodeller, og nulmodellen ved variantens egen
be_WR:

| variant | spread_ticks | slippage realiseret, tick pr. side |
|---|---|---|
| basis | 1,73 | 0,5417 |
| slippage 0 | 1,73 | 0 |
| slippage 1,0 | 1,73 | 1,0 |
| spread 1,50 | 1,50 | 0,5417 |
| spread 2,17 | 2,17 | 0,5417 |

**"Konklusionen"** er cellens status på tre punkter: K2's tærskel (Wilson-øvre for
`ruin_pct_netto_pess` ≤ 20%), K3 (≤ 10 med variantens omkostning) og K4 (≤ 5 pp). Skifter
nogen af de tre mellem slippage 0,5417 og 1,0, er **C4 blokerende**. Skifter nogen mellem spread
1,50 og 2,17, rapporteres det som afhængighed af spreadmålingens ubekræftede antagelser.

## 8. Referencerækker og tabeller

- **2 og 3 kontrakter** på den valgte celles timeframe, alle tre stopbredder, begge WR-akser,
  primært vindue. Referencer, ikke kandidater.
- **§5a's ATR-tabel regnet om på primærvinduet:** alle fire timeframes, RTH og døgn, samme
  kolonner som §5a plus `R_usd_middel`, `be_WR_pct_ved_middel_R` og `be_WR_pct_ved_R_p50`.
  Døgnrækker regnes med rundturen uden for RTH ($2,847). Den gamle tabel står ved siden af.
- **Chatten:** kun rækkerne med 1 kontrakt ved WR 40% absolut.
