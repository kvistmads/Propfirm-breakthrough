# B4 kandidat 1 — trin A, tillæg: to huller i beslutningsreglen §7

**Skrevet:** 2026-09-23 ca. 13:30 UTC af overblikssessionen.

**Status, ærligt.** Skrevet **efter** at prøvekørslens rapport lå på disken (13:01 UTC), og
efter at jeg ved en fejl så én linje af den. Skrevet **før** R = 500-kørslens p_FWE og
nulmodelfordeling findes. Kernens middel netto-R er deterministisk og er dermed kendt i
forvejen; N1, N2 og p_FWE er det ikke. Tillægget skal læses i det lys.

---

## Hvad jeg så

En grep efter metadata i `research/output/b4_k1_trinA.md` (prøvekørslen: 6 N1- og 3
N2-gentagelser, commit f94a2ea) ramte også denne linje:

> Bedste variant: **buffer_0/ingen**. middel netto-R = 0,0948 R (CI95 [0,0096; 0,1800]).
> p_FWE = 0,2857. N1's median = 0,0219, N1's 5%-fraktil = -0,0213.

p_FWE og N1-tallene betyder intet ved 6 gentagelser — den mindst mulige p-værdi er
1/7 = 0,14. Middel netto-R og dens CI bliver de samme i den rigtige kørsel, fordi kernen
ikke har tilfældighed i sig og den eneste kodeændring derefter (29f3116) er en stiangivelse
i rapportteksten.

## Hullerne

§7's fire bånd dækker ikke alle udfald:

| hul | betingelse | hvorfor intet bånd dækker det |
|---|---|---|
| A | p_FWE ≤ 0,05 **og** middel netto-R < +0,10 | bånd 2 kræver ≥ +0,10; bånd 3 kræver p_FWE > 0,05 |
| B | p_FWE > 0,05 **og** N1's 5%-fraktil ≤ middel netto-R < N1's median | bånd 3 kræver ≥ N1's median; bånd 4 kræver < N1's 5%-fraktil |

**Den sete middel på 0,0948 R kan lande i hul A.** Tillægget er skrevet med den viden, ikke
uden, og det er derfor det står her.

## Hvorfor hullerne ikke ændrer nogen handling

Kun to af §7's grænser ændrer kursen:

| bånd | handling | betingelse |
|---|---|---|
| 1 | variant fryses, holdout købes | p_FWE ≤ 0,05, middel ≥ +0,20, CI-nedre > 0 |
| 4 | kandidaten parkeres | middel under N1's 5%-fraktil |

Bånd 2 og bånd 3 har **samme handling**: trin 2 præregistreres med trin A som grundlinje.
Et resultat i hul A eller hul B opfylder hverken bånd 1's eller bånd 4's betingelse. Dets
handling er derfor den samme som bånd 2's og bånd 3's.

## Reglen

Et resultat i et hul får **ingen båndetiket**. Det beskrives ved sine tal — middel netto-R
med CI, p_FWE og afstanden til N1's median og 5%-fraktil — og handlingen er trin 2.

**Bånd 1 og bånd 4 er uændrede.** Intet i tillægget gør det lettere at fryse en variant
eller sværere at parkere kandidaten.
