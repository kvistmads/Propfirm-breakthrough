# PRD — Fase 1: Datagrundlag

**Skrevet:** 2026-09-10 af overblikssessionen.
**Besvarer:** åbent spørgsmål B1, B2 og første del af B3 i `STRATEGI_PROPFIRM.md`.
**Repo:** `Propfirm breakthrough`. Egen branch, ikke `main`.
**Kræver ikke:** Topstep-konto, API-abonnement eller penge. Intet i denne fase koster
noget.

---

## 1. Hvorfor denne fase er først

Der er **ingen prisdata i repoet overhovedet.** Intet kan backtestes, ingen strategi kan
måles, og ingen af de fire veje i §5d kan afgøres.

Og der er en anden grund, som er vigtigere: **hele §5 står på ét ATR-tal målt over 60
dage.** Yahoos intraday-cap er årsagen. Rækker en anden kilde dybere, falder forbeholdet
bort og sizingen kan bygges på en fordeling i stedet for på to måneder. Rækker den ikke,
skal vi vide det nu og regne med en eksplicit antagelse i stedet for at behandle 0,168%
som et kendt tal.

**Fasen er ikke stor. Den er bare først.**

---

## 2. Afgrænsning

**Denne fase gør IKKE:**

- leder efter en edge eller et signal
- bygger en runner eller en strategi
- rører `backtest/paired.py`'s manglende `runner`-import
- optimerer noget som helst

**Den skaffer data, verificerer at de er hvad de udgiver sig for, og måler volatiliteten.**
Det er alt.

Metoderegel 8 gælder: **stop efter hver kørsel.** Ingen konfigurationsændringer, ingen
strategiforslag — heller ikke gode. Resultaterne læses sammen i overblikssessionen først.

---

## 3. Præregistrerede kriterier

Skrevet før noget køres. Disse afgør fasens udfald, ikke en vurdering bagefter.

| # | kriterium | tærskel | hvis det ikke holder |
|---|---|---|---|
| **K1** | Dybde på NQ 15m fra mindst én gratis kilde | **≥ 3 år** | ATR rapporteres som eksplicit antagelse med følsomhedskolonne, ikke som fordeling. §5's forbehold bliver stående |
| **K2** | To uafhængige kilder beskriver samme serie | **median absolut afvigelse i dagligt high-low-range < 5%** | Bar-grænserne ligger forskelligt (tidszone, sessionsdefinition). Skal afklares før nogen af kilderne bruges |
| **K3** | Dækning i US RTH | **< 2% manglende barer** | Kilden er ikke egnet til intradag-backtest. Find en anden |
| **K4** | Ingen degenererede serier | **flade barer < 1%, ingen ikke-monotone timestamps** | Samme |

K2 er der på grund af guld-lektionen: **20% forskel i ATR mellem to kilder for samme
instrument og periode**, formentlig fordi bar-grænserne lå forskelligt (MT4 servertid mod
UTC). Det er ikke en teoretisk risiko — vi har set den.

---

## 4. Opgaver, i rækkefølge

### 4.1 Kortlæg kilderne

`londonstrategicedge.com` er nævnt i `STRATEGI_PROPFIRM.md`: 14 opløsninger inkl. 15m,
bulk Parquet, gratis nøgle, licens der tillader egen research og kommerciel trading (ikke
videresalg). **Futures-dybden er ikke oplyst** — de nævner aktier 2003, FX 2009, krypto
2017.

Undersøg den, og mindst to alternativer. For hver kilde:

| felt | |
|---|---|
| Instrumenter | Har den NQ og/eller MNQ? Kontinuerlig kontrakt eller enkeltmåneder? |
| Opløsninger | 1m / 3m / 5m / 15m? |
| Dybde | Hvor langt tilbage, målt — ikke som annonceret |
| Pris | Gratis, gratis nøgle, eller betalt |
| Licens | Må vi bruge det til egen research og til at handle på? |
| Format | Parquet / CSV / API. Rate limits |
| Sessioner | RTH og døgn adskilt, eller sammenblandet? Hvilken tidszone er timestampet i? |

**Tidszonen er ikke en detalje.** Den er den mest sandsynlige årsag til at K2 fejler.

### 4.2 Hent og verificér

Hent NQ 15m fra den bedste kilde. Derefter:

- Mål den faktiske dybde. Første og sidste bar, og om der er huller undervejs.
- Kør `research/diagnostics.py` på serien — den findes allerede og dækker flade barer,
  huller, dækningsgrad og krydsvalidering. **Brug apparatet, byg ikke et nyt.**
- Hold én handelsdag op mod Yahoo bar for bar. Samme åbning, samme lukning, samme
  bar-grænser? Rapportér K2's tal.

### 4.3 Byg datalaget

Et minimalt lag i repoet:

- indlæsning fra kilden med cache til Parquet (arkivet skal ikke hentes igen ved hver
  kørsel)
- validering ved indlæsning — afvis tomme svar, manglende kolonner, NaN og ikke-monotone
  timestamps, samme kontrakt som `data/fetcher._validate_ohlcv` i det gamle repo
- eksplicit sessionsmarkering: hver bar mærkes RTH eller uden for RTH
- resampling til de timeframes vi skal bruge

**Må ikke importere fra `REAL TRADING BOT`.** Apparatet er kopieret, ikke delt.

Tests, og de skal være grønne sammen med de eksisterende 94.

### 4.4 Mål ATR-fordelingen

Dette er fasens egentlige resultat.

For **15m, 5m, 3m og 1m**, og for **RTH og døgn hver for sig**:

| kolonne | |
|---|---|
| `timeframe` | |
| `session` | RTH / døgn |
| `n_barer` | |
| `ATR_pct_p10`, `ATR_pct_p50`, `ATR_pct_p90` | fordelingen, ikke et gennemsnit |
| `R_usd_p10`, `R_usd_p50`, `R_usd_p90` | ved MNQ à $2/point og dagens NQ-niveau |
| `risiko_pct_af_MLL_p50`, `risiko_pct_af_MLL_p90` | mod $2.000. **p90 er go/no-go-kolonnen** |
| `omk_R_p50`, `omk_R_p90` | ved $2,47 pr. rundtur |
| `be_WR_pct_p50`, `be_WR_pct_p90` | ved 2:1 |

Og hvis dybden rækker: **samme tabel opdelt pr. år**, så regimevariationen kan ses. Det er
hele pointen med at gå væk fra 60 dage.

**Go/no-go vurderes på p90**, ikke på medianen — metoderegel 11. Retningen er asymmetrisk:
høj ATR er det der kan gøre en timeframe ufarbar, fordi 1 MNQ er udelelig.

Sammenlign med den kvadratrods-skalerede tabel i §5b og rapportér afvigelsen. Forventningen
er at de lave timeframes har **højere** ATR end kvadratroden forudsiger.

### 4.5 Afgør om spread kan måles

`STRATEGI_PROPFIRM.md` B3 spørger til reelt spread pr. tidsblok. **Spread kræver bid/ask,
og det kan formentlig ikke udledes af OHLC-barer.**

Opgaven her er kun at afgøre spørgsmålet:

- Har nogen af kilderne quote-data, eller kun trades?
- Hvis ikke: hvad ville der skulle til? Egen optagelse fra TopstepX' Level 1-feed, eller
  en anden kilde?
- Rapportér konklusionen. **Byg ikke en optager i denne fase.**

---

## 5. Leverancer

| leverance | hvor |
|---|---|
| Kildeoversigt med de felter fra 4.1 | `research/output/datakilder.md` |
| Verifikation mod Yahoo, K1-K4 med tal | samme dokument |
| Datalag + cache | `data/` i repoet |
| Tests grønne | `.venv/bin/python -m pytest tests/ -q` |
| ATR-fordelingen | `research/output/atr_fordeling.md` + `.csv` |
| Konklusion på spread | `research/output/datakilder.md` |
| **Kompakt tabel i chatten** | maks ~15 linjer, brutto og netto side om side, enheder i kolonnenavnene |

Tabellen i chatten er ikke valgfri. Ejeren er ofte på telefonen og skal kunne læse resultatet
uden at åbne en fil.

---

## 6. Tilbage til overblikssessionen

Når fasen er kørt, rapportér disse fem ting — de er det overblikssessionen skal bruge for
at skrive fase 2:

1. **Holdt K1-K4?** Hvilke, og med hvilke tal.
2. **Faldt §5's ATR-forbehold bort, eller står det?**
3. **Hvilken timeframe peger fordelingen på?** Med p90-kolonnen som argument.
4. **Kan spread måles, og hvorfra?**
5. **Hvilke rækker i `claude/ANTAGELSER.md` skifter status?** ATR står i dag som "M,
   svagt". Efter denne fase skal den enten være "M" med en kendt stikprøve, eller "A" med
   en følsomhedskolonne.

**Ingen strategiforslag i rapporten.** Heller ikke gode. Det er metoderegel 8, og den
findes fordi den er blevet brudt før.
