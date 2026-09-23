# B4 kandidat 1 — motorrettelse efter trin A

Kørt 2026-09-23 15:41 UTC fra commit `f8aa5fa` af Code, med modul, tests og præregistrering committet og uændrede. Præregistrering `research/prereg/b4_k1_motorrettelse.md` (commit `396b025`). Kode `research/b4_k1_trinA.py` (commit `f8aa5fa`).

Serie: MNQ.v.0, samme som trin A. 1638282 1m-barer → 109598 15m-barer. **Kun kernen, 6 varianter. N1 og N2 kørt ikke.**

**Regressionstjek: OK**, `b4_k1_optaelling_v2.csv` gengivet byte for byte fra kerne v2 på NQ, uændret modul.

## Tre rettelser

1. Fyldningsbaren: kun stoppet kan rammes der. Mål, BE-trigger og +1R tjekkes fra næste 1m-bar. Gælder overalt `simuler_handel` bruges (kerne, N1, N2, strejf).

2. N2: hele zonen (zone_high, zone_low, E) forskydes med samme beløb, så stopafstanden bevares.

3. `holder_pct`: andel handler hvor +1R nås før stoppet, fyldningsbaren undtaget. Tidsexit tæller som holder hvis +1R blev nået før 21:50. Wilson-CI.

## Målingen — før/efter, kun kernen

| buffer | BE | handler_n (før/efter) | middel_R_netto før | efter | forskel | ramt af rettelse 1 | holder_pct [CI95] |
|---|---|---|---|---|---|---|---|
| buffer_10 | ingen | 1095/1095 | 0,0599 | -0,0035 | -0,0634 | 23 | 50,9 [47,9; 53,8] |
| buffer_10 | BE_1_0R | 1375/1276 | 0,0688 | -0,0192 | -0,0881 | 154 | 50,7 [48,0; 53,4] |
| buffer_10 | BE_1_2R | 1303/1226 | 0,0573 | -0,0115 | -0,0688 | 124 | 50,2 [47,4; 53,0] |
| buffer_0 | ingen | 1100/1100 | 0,0948 | -0,0177 | -0,1125 | 41 | 50,7 [47,8; 53,7] |
| buffer_0 | BE_1_0R | 1407/1302 | 0,0847 | -0,0458 | -0,1305 | 185 | 50,3 [47,6; 53,0] |
| buffer_0 | BE_1_2R | 1318/1256 | 0,0729 | -0,0438 | -0,1168 | 136 | 50,3 [47,6; 53,1] |

`handler_ramt_af_rettelse_1_n` i alt: 663 (samme udfald eller R_brutto før og efter, matchet på zonens `basis_i`, tæller ikke med). Handler der kun findes i én af de to kørsler (dagsdisciplinen kaskaderede): 373 kun før, 30 kun efter.

Største ændring i middel_R_netto blandt de 6 varianter: 0,1305 R.

## Efter kørslen

Stop. Ingen ændring af andet end de tre rettelser.
