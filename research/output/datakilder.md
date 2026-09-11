# Datakilder — fase 1

Kortlagt 2026-09-11. Besvarer B1 (kilder, dybde, pris, overensstemmelse) og første del af
B3 (kan spread måles). PRD: `PRD_FASE1_DATAGRUNDLAG.md`.

**Status:** kortlægning færdig. Verifikation, ruller og spread udfyldes efter
Databento-udtrækket.

---

## 1. Kildeoversigt (§4.1)

"Målt" betyder hentet og talt af os. "Oplyst" betyder udbyderens egen side.

| kilde | NQ / MNQ | opløsninger | dybde | pris | må vi handle på det? |
|---|---|---|---|---|---|
| **Databento GLBX.MDP3** | begge, CME-primærdata | 1s/1m/1h/1d OHLCV, trades, bid/ask | oplyst fra 2010-06-06 | $125 gratis kredit | ja, intern kommerciel brug |
| **Yahoo NQ=F** | NQ, kontinuerlig | 1m/2m/5m/15m/30m/1h… (ingen 3m) | **målt:** 1m 30 d, 15m 60 d, 1h 730 d | gratis | nej — personlig brug |
| London Strategic Edge | **sandsynligvis ingen** — "futures" = Eurex | 14, inkl. 1m/3m/5m/15m | futures ikke oplyst | gratis nøgle | ja, ikke videresalg |
| FirstRate Data | NQ, kontinuerlig + enkeltmåneder | 1m/5m/30m/1h (ingen 15m) | oplyst fra 2008-01-02 | betalt, 2 ugers prøve | ikke oplyst |
| Dukascopy | **nej** — CFD på Nasdaq-100 | tick/1s/1m… | 1m fra 2011 (tredjepart) | gratis | **nej** — ikke-kommerciel, ingen database |
| Barchart | NQ | 1m intraday ~10 år | kun Premier | betalt | ikke oplyst |
| TopstepX / ProjectX | begge | sekund…måned | ikke oplyst | Topstep-konto + $14,50/md | — (det er venuet) |

**Ingen kilde uden konto har ≥ 3 år NQ 15m.** Den eneste nøglefri kilde er Yahoo, og den
rækker 60 dage på 15m — samme cap som §5's 0,168% blev målt under.

### Databento — GLBX.MDP3 (valgt)

| felt | |
|---|---|
| Instrumenter | NQ og MNQ som enkeltkontrakter. Kontinuerlig via symbologi: `NQ.v.0` (størst volumen), `.c.0` (nærmeste udløb), `.n.0` (open interest). Rå priser, ingen tilbagejustering |
| Opløsninger | ohlcv-1s/-1m/-1h/-1d, trades, mbp-1/-10, mbo, bbo-1s/-1m, tbbo. **Ingen 3m/5m/15m** — aggregeres fra 1m |
| Dybde | oplyst fra 2010-06-06 · målt: *udfyldes* |
| Pris | usage-based, estimeres gratis før hvert udtræk. $125 kredit ved oprettelse, udløber efter 6 md. Fase 1-loft $25 |
| Licens | intern kommerciel brug tilladt på alle planer. Cachen er git-ignoreret |
| Format | DBN/CSV/JSON over HTTP. Python-klient `databento` 0.86 |
| Sessioner / tidszone | **UTC**, nanosekunder. Hele Globex-døgnet, ingen RTH-markering — den lægger datalaget på efter NYSE-kalenderen |
| Quotes | **ja** — bbo-1m og mbp-1 |

### Yahoo Finance — NQ=F (anden kilde til K2)

| felt | |
|---|---|
| Instrumenter | NQ som Yahoos egen kontinuerlige front-kontrakt. Rulledato udokumenteret |
| Opløsninger | 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 4h, 1d og op. **3m afvises** af API'et |
| Dybde (målt 2026-09-11) | 1m: 30 dage, højst 7 pr. kald. 5m/15m: fra 2026-07-01. 1h: fra 2024-04-18 |
| Pris | gratis, ingen nøgle |
| Licens | yfinance er uofficiel; Yahoos data er til personlig brug. Egnet til krydstjek, ikke som grundlag |
| Format | uofficielt JSON-API via yfinance 1.7. Ingen dokumenterede rate limits |
| Sessioner / tidszone | **America/New_York**, tz-aware. `prepost=True` giver hele døgnet |
| Quotes | nej |

### London Strategic Edge (droppet 2026-09-11)

| felt | |
|---|---|
| Instrumenter | "54 futures" uden symbolliste. Den officielle klient (`lse-data`, `client.py`) mapper kategorien *Futures* til datasættet **`eurex`**. NQ/MNQ nævnes ingen steder. Kataloget kræver nøgle (HTTP 401 uden), så det kunne ikke efterprøves |
| Opløsninger | 1s, 5s, 15s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo |
| Dybde | aktier 2003, FX 2009, krypto 2017. Futures ikke oplyst |
| Pris | gratis nøgle |
| Licens | egen research, trading og modeltræning, også kommercielt. Ikke videresalg eller redistribution |
| Format | REST, maks 5.000 rækker pr. kald, plus asynkron Parquet-eksport. Streaming og download deler én kvote |
| Tidszone | UTC |
| Quotes | ikke dokumenteret for futures |

### De øvrige

- **FirstRate Data** — NQ kontinuerlig fra 2008-01-02 i tre justeringsvarianter, enkeltkontrakter
  fra NQZ08. 1m/5m/30m/1h/1d, CSV i zip, US/Eastern. Betalt; to ugers gratis prøve. Ingen quotes.
- **Dukascopy** — `USATECHIDXUSD` er en CFD, ikke NQ. Gratis og dyb, med bid/ask — men
  CFD'ens spread, ikke CME's. Vilkårene tillader kun personlig, ikke-kommerciel brug og
  forbyder at opbygge en database af indholdet. Uegnet.
- **Barchart** — 1m intraday ~10 år tilbage kræver Premier. Gratis: daglige priser 2 år.
  Maks 10.000 rækker pr. download.
- **TopstepX / ProjectX Gateway** — historik via `POST /api/History/retrieveBars` (sekund til
  måned, maks 20.000 barer pr. kald, dybde ikke oplyst). Realtid via market hub:
  `GatewayQuote` med `bestBid`/`bestAsk`, `GatewayTrade`, `GatewayDepth`. Kræver
  Topstep-konto og API-abonnement — uden for fase 1, men det er serien botten handler i (C7).
- **Portara (CQG), Kibot** — betalte. Level 1-tick med bid/ask for NQ; Portara fra 1999.

---

## 2. Valg

**Databento**, besluttet af Mads 2026-09-11, med fire betingelser:

1. Maks $25 af kreditten i fase 1. Prisestimat før hvert udtræk.
2. Kun 1m OHLCV. 3m/5m/15m aggregeres, så alle timeframes deler bar-grænser.
3. ATR måles på NQ, spread på MNQ.
4. Rullemetoden dokumenteres og antallet af spring rapporteres.

Yahoo er anden kilde til K2. LSE droppes.

---

## 3. Verifikation (§4.2) — K1-K4

*Udfyldes efter Databento-udtrækket.*

---

## 4. Rullemetode

*Udfyldes efter Databento-udtrækket.*

---

## 5. Spread (§4.5)

*Udfyldes efter Databento-udtrækket.*

---

## Kilder

- databento.com: catalog/cme/GLBX.MDP3/futures/NQ, pricing
- yfinance 1.7.0 mod NQ=F, målt 2026-09-11
- londonstrategicedge.com (forside, /data, /api-documentation); github.com/londonstrategicedge/lse-data
  (`README.md`, `lse/client.py`, `lse/vault.py`); api.londonstrategicedge.com/vault (401 uden nøgle)
- firstratedata.com/i/futures/NQ og forsiden
- dukascopy-node.app/instrument/usatechidxusd; dukascopy.com Terms of Use
- help.barchart.com: "How can I download historical data"
- gateway.docs.projectx.com: retrieve-bars, realtime
- portaracqg.com/futures/int/enq; kibot.com
