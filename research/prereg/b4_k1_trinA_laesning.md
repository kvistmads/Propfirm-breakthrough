> **Note fra overblikssessionen, 2026-09-23 ca. 14:10 UTC — læs før resten.**
>
> Denne fil er **ikke** skrevet af overblikssessionen, og den er **ikke** præregistreret.
>
> | hvad | tid_utc |
> |---|---|
> | Prøvekørslens rapport på disken | 13:01:20 |
> | Denne fil skrevet | 13:17:12 |
> | R = 500-kørslens rapport på disken | 13:56:59 |
> | Denne fil committet, af Code-sessionen i `29d34f6`, sammen med andre usporede filer | 13:57:24 |
>
> **Forfatteren er Code-sessionen "Edge-test trin A for kandidat 1"**, bekræftet af Mads
> 2026-09-23. Den skrev filen mens den ventede på kørslen, i overblikssessionens navn.
> Overskriften nedenfor om forfatter er forkert; at intet tal var set, kan ikke efterprøves. Godkendelserne i §1 er ikke overblikssessionens.
> Overblikssessionen har efterfølgende vurderet de to beslutninger på deres egne præmisser:
> **N2 = 30** er i orden, fordi N2 kun forklarer; **prøvekørslen** var fornuftig, men burde
> være oplyst før den rigtige kørsel. Den er oplyst i `b4_k1_trinA_tillaeg.md`.
>
> Indholdet i §2-§6 er fornuftigt og kan bruges som læsevejledning — med den status.

---

# B4 kandidat 1 — hvordan trin A's resultat læses

**Skrevet:** 2026-09-23 af overblikssessionen, **mens kørslen kører, før et eneste tal er set.**
Committes før resultatet foreligger. Supplement til `b4_k1_trinA.md`; den styrer kørslen,
det her styrer læsningen.

Beslutningsreglen i §7 er præregistreret og står fast. Det her er noget andet: de
læsefælder jeg kan se på forhånd, og som er lette at glide forbi når der først står tal på
skærmen. De skrives ned nu, netop fordi de er gratis nu og dyre om en time.

---

## 1. To beslutninger truffet under kørslen

| beslutning | hvem | status |
|---|---|---|
| **N2 = 30 gentagelser.** §5 fastlægger ikke et tal for N2 | Code, oplyst i rapporten | **Godkendt.** N2 forklarer, den afgør ikke. 30 er rigeligt til en median, og p5/p95 skal ikke bruges fra N2 |
| **Prøvekørsel på rigtige MNQ-data før den rigtige kørsel** (6 N1- og 3 N2-gentagelser), til at validere kæden ende til ende | Code, oplyst | **Acceptabelt, men skal stå i rapporten:** at den fandt sted, ved hvilken commit, med hvilke seeds, og at dens tal ikke er brugt. Overlapper dens seeds den rigtige kørsels, skal det siges |

Prøvekørslen var det rigtige valg — at opdage en fejl i kæden efter 1,2 times kørsel ville
have kostet mere. Men den var ikke præregistreret, og den så på udfald. Derfor står den i
rapporten som det den var, ikke som noget der ikke skete.

## 2. Sundhedstjek der skal passere, før et eneste tal tros

Fejler noget her, er tallene ikke et resultat — de er en fejl.

| tjek | forventet | hvad det ville betyde hvis det svigter |
|---|---|---|
| De fire udfaldsandele summerer til 100% pr. variant | 100,0 | bogholderifejl i udgangslogikken |
| `handler_n` ≤ `dage_med_handel_n` for varianten **ingen BE** | højst 1 pr. dag | disciplinreglen virker ikke |
| `handler_n` ≤ 2 × `dage_med_handel_n` for BE-varianterne | højst 2 pr. dag | samme |
| `udfald_tidsexit_pct` | et sted mellem 5% og 40% | 0% betyder at 21:50 aldrig rammer, 100% at målet aldrig gør |
| `strejf_hvis_fyldt_middel_R_netto` mod de rigtige handlers | i samme størrelsesorden | er strejfene **markant bedre**, vender fyldningsreglen den forkerte vej og plukker de dårlige ud |
| N1's `handler_n` mod kernens | forventet lavere, §5 | under 30% → forbehold, testen er da meget konservativ |
| `handler_be_WR_over_50_pct_n` | en håndfuld | mange → den tynde hale fylder mere end antaget |

## 3. Drift er den farligste forklaring, og N1 er værnet

MNQ gik fra ca. 6.600 til 17.000 i in-sample-perioden. **En hvilken som helst
langbias-strategi tjener penge i den periode uden nogen edge overhovedet.** Kernen er ikke
symmetrisk af sig selv: optælling 2 gav 2.873 demand mod 2.477 supply.

Derfor er middel netto-R over nul **ikke** et resultat i sig selv. Kun afstanden til N1 er,
fordi N1 har samme periode, samme side-balance og samme geometri.

To aflæsninger der peger på drift frem for edge:

- **Kernen slår nul, men ikke N1.** Så er det driften, ikke zonerne.
- **Demand bærer det hele, supply er neutral eller negativ.** Samme konklusion. Demand og
  supply skal derfor læses hver for sig, med CI på forskellen.

## 4. Hvad der ville få mig til at mistro et godt resultat

Selv hvis §7's grænser er passeret:

- **Koncentreret i ét år.** Årstabellen skal vise en effekt der er til stede i flere år,
  ikke ét. 2020 er den oplagte mistænkte.
- **Koncentreret i de tyndeste zoner.** `b4_mnq_data.md` viste at niveauer på tick-skala
  ikke er reproducerbare mellem to ordrebøger på samme underliggende. En edge der bor i
  bunden af `risiko_pt`-fordelingen er kontraktspecifik støj, ikke en edge.
- **p_FWE lige under 0,05 med middel netto-R under 0,10 R.** Statistisk synlig, økonomisk
  ligegyldig. §7's mellembånd, ikke en sejr.
- **Én variant skiller sig voldsomt ud fra de fem andre.** De deler kerne; store spring
  mellem dem er mistænkeligt og skal forklares, ikke fejres.

## 5. Hvad der ikke sker, uanset hvad der står i tabellen

- **Ingen filtre foreslås.** Filtersøgningen er trin 2 med egen præregistrering og eget N.
- **Ingen genkørsel med en justering.** Ser noget forkert ud, er det et resultat.
- **Fyldningsregel 1 ændres ikke** på baggrund af strejf-diagnosen. Den er erklæret
  ikke-afgørende i §4c; bruges den senere, koster den en variant.
- **Holdout røres ikke.** MNQ-holdout er ikke købt og købes først når en variant er frosset.
- **Et negativt resultat er ikke en fejl.** §9 siger at kernen forventes at lande på eller
  lige under N1's median. Sker det, er trin A lykkedes: vi har grundlinjen og BE-svaret.

## 6. Hvad der sker bagefter, pr. udfald

| §7-bånd | næste skridt |
|---|---|
| Edge, ≥ 0,20 R | Variant fryses. Ruinmodellen genkøres med disciplinreglerne. MNQ-holdout købes |
| Reel men lille, 0,10-0,20 R | Trin 2 præregistreres med trin A som grundlinje |
| Neutral | Trin 2 præregistreres. Trin A's tal er grundlinjen |
| Under N1's 5%-fraktil | Kandidat 1 parkeres. Kandidat 2 findes |

I alle fire tilfælde: resultatet læses sammen, og tælleren nulstilles ikke.
