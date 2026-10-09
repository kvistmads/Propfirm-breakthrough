# B4 kandidat 6 — tillæg: optællingen godkendt, før kørslen

**Skrevet:** 2026-10-09 af overblikssessionen. Det er skrevet efter Code's trin 1 (kode
2f48756, optælling a8cd76b) og **før** den rigtige kørsel. Der er ikke set P&L, hit ratio
eller udfald.

**Gyldighed:** tillægget gælder, når ejeren committer det. Commit'en er ejerens
godkendelse. `b4_k6_overnight.md` gælder uændret. Tillægget ændrer ingen definitioner og
kræver ingen kodeændring.

## 1. Optællingen er godkendt

| variant | nætter, NQ | σ_nat $ | MDE_sidak4 $ | styrke mod N-nat ved $8,6 / $17,2 | styrke for CI-nedre > 0 ved $8,6 / $17,2 |
|---|---|---|---|---|---|
| V1 · alle | 2.011 | 117,5 | 8,1 | 85% / 100% | 59% / 100% |
| V1 · salg | 902 | 126,5 | 13,0 | 42% / 97% | 28% / 93% |
| V2 · alle | 2.011 | 177,3 | 12,2 | 48% / 98% | 31% / 95% |
| V2 · salg | 902 | 193,2 | 19,8 | 18% / 67% | 14% / 61% |

- **Data:**
  - 2.012 nætter, hvoraf 1 er udelukket (2020-03-16, nætterne efter limit-down i marts
    2020).
  - 44,9% af nætterne følger en salgsdag.
  - 0 ruller i vinduerne. Alle ruller ligger kl. 18–19 CT.
- **Styrken:**
  - V1 · alle kan se artiklens effekt på $8,6 mod nulmodellen med 85%.
  - Salgsvarianterne har halvt så mange nætter. De kan kun se en effekt, der er cirka
    dobbelt så stor. Artiklen fandt, at effekten er større efter salg, men opgav den ikke
    i bp.
  - V2 · salg er den svageste.
  - **Kørslen godkendes på trods af det.** Præregistreringen satte ingen fast grænse, og
    varianterne er bestemt på forhånd.
- **Omkostningen** var 3,14 bp pr. round trip i 2016 (median L 4.541) og 0,96 bp i 2023,
  mod 0,49 bp ved dagens niveau. Normeringen i §4f betyder altså meget for 2016–2019.
- **Tælleren forbliver 45.**

## 2. Code's læsninger — godkendt

Alle 23 i docstringen i `research/b4_k6_overnight.py` er godkendt. De seks markerede:

| nr | læsning | hvorfor den er rigtig |
|---|---|---|
| 5 | En forsinkelse over 5 minutter i ét af de fire punkter udelukker natten i alle varianter og i N-nat | Det står sådan i §4b. På disse data giver begge læsninger det samme |
| 9 | N-nat må røre variantens vindue, men ikke overlappe det | Ingen bar deles. Det er det, "overlapper ikke" betyder |
| 10 | N-nat normeres med den trukne indgangsbars egen L | Samme princip som modellen. Forskellen er ubetydelig |
| 12 | Δclose for vinduets første bar regnes mod forrige bar | Samme valg som kandidat 5 og den forsigtige side |
| 13 | Styrken regnes mod N-nat (omkostningen går ud) og for CI-nedre > 0 (netto = effekt − $2,85) | Det svarer til de to krav i §8 |
| 19 | Tercilerne deles blandt salgsnætterne | Spørgsmålet er, om større salg giver større effekt |

**Læsning 3** (MNQ hentes uafskåret med `load_in_sample("MNQ.v.0")`) er også godkendt. Den
rammer kun den første nat i kontrolserien.

**Bemærk:** V2-indgangen kl. 00:30 CT var forsinket 1–5 minutter i 28 nætter på NQ. Det er
inden for reglen og rapporteres.

## 3. Betingelser for den rigtige kørsel

1. **Ingen kodeændringer.** Kørslen sker fra den committede kode, og rapporten oplyser
   commit-hash.
2. Regressionstjekket i §11.3 køres igen og skal holde.
3. **R = 500**, for både NQ og MNQ.
4. **Afgørelsen efter §8 tages på NQ.** MNQ rapporteres som kontrol og afgør intet.
5. **Rapport efter §10 og §9.** Bagefter: stop. §8 anvendes mekanisk og læses sammen med
   ejeren.
