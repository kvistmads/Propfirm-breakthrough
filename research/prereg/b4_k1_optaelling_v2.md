# B4 kandidat 1 — præregistrering: signaloptælling, kerne v2

**Skrevet:** 2026-09-22, før kørslen. Committes før kørslen (metoderegel 13).
**Grundlag:** kernen v2 i `research/output/b4_hypoteser.md`, besluttet af ejeren 2026-09-22.
**Bygger på:** `research/prereg/b4_k1_optaelling.md` (11d68f2) og tillægget
`b4_k1_optaelling_tillaeg.md` (50a060e). **Alt derfra gælder, medmindre det er ændret her.**

---

## 1. Hvorfor en ny optælling

Optælling 1 (kerne v1) viste at 55,4% af signalerne var berøringer i lyset lige efter
udbruddet. Prisen havde ikke forladt zonen, så det er ikke videoens retest. Kernen er
ændret før noget udfald er set. MDE skal regnes på den kerne der faktisk testes, derfor
tælles der igen.

Kørslen ser **ikke** på udfald — samme regel som i optælling 1, §1. Den lægger intet til
tælleren.

## 2. Hvad der er ændret — eksemplet er demand, supply er spejlvendt

| element | v1 | **v2** |
|---|---|---|
| Højde | H = high − low | uændret |
| Buffer | ingen | **B = 0,10 × H** |
| Indgangsniveau | E = high | **E = high + B** |
| Aktivering | — | Det første lys, **fra og med udbrudslyset**, hvis low > E |
| Ugyldig | — | Et lys **efter udbrudslyset og før aktiveringen** med close < low |
| Berøring | første lys efter udbrudslyset med low ≤ high | første lys **efter aktiveringslyset** med low ≤ E |
| Berøringer før aktivering | — | tæller ikke, og zonen lever videre |
| Risiko | H | **E − low = 1,1 × H** |
| Stoploft | H / close ≤ 0,429% | **1,1 × H / close ≤ 0,429%** |
| Kontrakter | floor(250 / (H_pt × 2)) | **floor(250 / (1,1 × H_pt × 2))** |
| omk_R_netto | 2,627 / (2 × H_pt) | **2,627 / (2 × 1,1 × H_pt)** |

Supply: E = low − B, aktivering når high < E, ugyldig ved close > high før aktivering,
berøring når high ≥ E.

Uændret fra v1: basislys og udbrudslys, farvekravet, zonen dør ved berøringen uanset
tidspunkt, zonen dør ved kontraktskift i alle faser, vinduet 08:30-14:30 CT (halve dage
til 30 min før luk), in-sample 2016-01-01 til 2023-12-31, data kun gennem `data/holdout.py`.

Hver zone ender i præcis ét af fem forløb: berørt, ugyldig før aktivering, død ved
kontraktskift, aktiv men ikke berørt ved in-sample-slut, eller aldrig aktiveret ved
in-sample-slut.

## 3. Sekundært: varianten uden buffer

Samme kørsel tæller også varianten **B = 0** (E = high, risiko = H, stoploft H / close ≤
0,429%). Den bruges kun til at kunne regne MDE for varianten senere. Beslutningsreglen i §5
gælder kernen v2 med buffer.

## 4. Rapport

Samme hovedtabel og samme tabel pr. år som i optælling 1, for kernen v2, med Wilson 95%-CI
på hver andel. Nye rækker:

| kolonne | formel |
|---|---|
| zoner_ugyldige_foer_aktiv_pct | ugyldige / zoner_dannet_n |
| zoner_aldrig_aktive_pct | aldrig aktiveret ved in-sample-slut / zoner_dannet_n (censureret) |
| zoner_aktive_ikke_beroert_pct | aktive men ikke berørt ved in-sample-slut / zoner_dannet_n (censureret) |
| tid_til_aktiv_timer_p50/_p90 | udbrudslysets lukning til aktiveringslysets åbning, kun signaler |
| tid_efter_aktiv_timer_p50/_p90 | aktiveringslysets lukning til berøringslysets åbning, kun signaler |
| beroering_lige_efter_aktivering_pct | signaler hvor berøringen er lyset lige efter aktiveringslyset / signaler |
| risiko_pt_p10/_p50/_p90 | 1,1 × H_pt, kun signaler |

Plus én kort tabel for varianten uden buffer: `dage_med_signal_n`, `dage_med_signal_pct`
med CI og `signaler_n`.

## 5. Beslutningsregel — uændret fra optælling 1

| dage_med_signal_n | andel af 2.012 dage | vi gør |
|---|---|---|
| ≥ 590 | ≥ 29,3% | Edge-testen præregistreres, også med filtersøgning |
| 390-589 | 19,4-29,3% | Kun kernen testes |
| < 390 | < 19,4% | Kandidaten parkeres |

Krydser konfidensintervallet en grænse, gælder den laveste kategori.

## 6. Regressionstjek før kørslen

Koden udvides, den erstattes ikke. **Før v2 køres, skal den ændrede kode med v1-kernen
gengive optælling 1's csv (commit 43c5182) præcis.** Afviger den, køres v2 ikke, og det
rapporteres.

## 7. Forventning, skrevet før kørslen

Ikke et kriterium. Trin 2 fjerner berøringerne lige efter udbruddet, og flere zoner når
at dø om natten, før de bliver testet i RTH. **Forventningen er at mellem 60% og 90% af
dagene har et signal**, altså færre end v1's 96,4%. Andelen af berøringer lige efter
aktiveringen forventes at være langt under v1's 55,4%.

## 8. Efter kørslen

Stop. Tabellen i chatten, ingen ændring af definitioner, ingen forslag. Resultatet læses
sammen med ejeren.
