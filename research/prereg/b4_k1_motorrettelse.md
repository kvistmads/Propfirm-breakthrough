# B4 kandidat 1 — motorrettelse efter trin A

**Skrevet:** 2026-09-23 af overblikssessionen, før rettelsen køres. Committes før kørslen.
**Grundlag:** `research/output/b4_k1_trinA_laest.md` §2 og §9.

Det her er ikke en ny test. Trin A's afgørelse står som kørt. Rettelsen skal gøre motoren
korrekt før trin 2, og målingen skal vise hvor meget fejlen betød.

## Tre rettelser

| nr | fejl | rettelse |
|---|---|---|
| 1 | Mål og BE-trigger tjekkes mod hele fyldnings-1m-barens high/low, også den del der lå før fyldningen | I fyldnings-1m-baren kan **kun stoppet** rammes. Mål, BE-trigger og +1R tjekkes fra næste 1m-bar. Gælder kernen, N1, N2 og strejf-diagnosen — de deler funktionen |
| 2 | N2 flytter E, men stoppet bliver stående, så risikoen skrumper eller bliver negativ | N2 flytter **hele zonen** — zone_high, zone_low og E — med samme forskydning. Stopafstanden bevares |
| 3 | "Holder" findes ikke som mål | Ny kolonne `holder_pct`: andel handler hvor +1R nås før stoppet (fyldningsbaren undtaget, jf. 1). Tidsexit tæller som holder hvis +1R blev nået før 21:50 |

## Målingen

**Kun kernen**, 6 varianter, samme data og samme commit-kæde. Kernen er deterministisk, så
det tager sekunder. N1 og N2 køres **ikke** — de køres med den rettede motor i trin 2.

Pr. variant rapporteres: `handler_n`, `middel_R_netto` før og efter med forskel,
`handler_ramt_af_rettelse_1_n`, `holder_pct` med Wilson-CI.

## Forventning, skrevet før kørslen

Få handler rammes af rettelse 1 i varianten uden BE — målet kræver et udsving på over 2R
inden for ét minut. Flere rammes i BE-varianterne, fordi triggeren ligger nærmere.
**Middel netto-R falder med under 0,02 R i alle seks varianter.** Falder den mere, er
trin A's niveau mere forvrænget end antaget, og det skal stå i trin 2's grundlinje.

## Efter kørslen

Stop. Tabellen i chatten. Ingen ændring af andet end de tre rettelser.
