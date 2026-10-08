# B4 kandidat 4 — tillæg: beslutninger efter optællingen, før kørslen

**Skrevet:** 2026-10-08 af overblikssessionen. Det er skrevet efter Code's trin 1 (kode
b9fb769, optælling a24834a) og **før** den rigtige kørsel. Ingen R, vinderrate eller
udfald er set.

**Gyldighed:** tillægget gælder, når ejeren committer det. Commit'en er ejerens
godkendelse af de to beslutninger nedenfor, som følger overblikssessionens anbefaling.
Vil ejeren noget andet, rettes tillægget før commit. `b4_k4_emt.md` gælder uændret,
undtagen hvor dette tillæg siger andet.

## 1. De to k = 3,0-varianter bliver i testen

**k = 3,0 · 1/dag** (840 handler, MDE 0,241 R) og **k = 3,0 · 2/dag** (1.349 handler,
MDE 0,201 R) klarer ikke §7's krav om MDE ≤ 0,20 R med Šidák 6.

- De bliver i testen uændret, og rapporten skriver deres MDE ud. Samme beslutning blev
  truffet for kandidat 2 (tillæg §1).
- k = 3,0 · 2/dag ligger 0,001 over grænsen.
- k = 3,0 · 1/dag kan kun se en edge over cirka 0,24 R.
- **Tælleren forbliver 37.**

**Rettelse af §7:** σ_R blev 1,81–2,29, ikke cirka 1,41. Median-RR er 2,7–4,7, fordi
1R-reglen og stoppet tæt bag vægen giver lange mål. MDE i optællingen er regnet med de
faktiske σ_R, som §7 foreskrev. Tabellen i §7 byggede på et forkert gæt på RR.

## 2. N-tid matches også på tid på dagen

Optællingen viser, at N-tid's pulje har signaltid med median kl. 11:30–11:50 CT, mens
modellens median ligger kl. 09:40–10:55 CT. Modellen tager typisk dagens første setup,
mens puljen er alle dagens strakte lys. Uden rettelse ville nulmodellen sammenligne
morgen med middag, og forskellen ville blande tid på dagen ind i vægens betydning.

**Ny regel for N-tid**, som erstatter §6's "tilfældigt pr. dag":
- Hver model-handel matches med en kandidat fra **samme ET-dag, samme retning og samme
  klokketime CT** som model-handlens udmattelseslys.
- Har timen ingen kandidat, bruges den nærmeste time med kandidater samme dag. Det tælles.
- Alt andet i §6 og læsning 18–20 gælder uændret.

Rettelsen er besluttet før udfaldene og ud fra optællingen alene. Den kræver en
kodeændring med en test (§4).

## 3. Code's læsninger — godkendt

Alle 28 i docstringen i `research/b4_k4_emt.py` er godkendt. Læsning 17 og 20 suppleres
af §2 ovenfor. De fem markerede:

| nr | læsning | hvorfor den er rigtig |
|---|---|---|
| 10 | VWAP ved fyldet er VWAP ved lukningen af minuttet før fyldningsbaren, samme værdi som målet i den bar. VWAP på den forkerte side giver RR < 0 og falder for 1R-reglen | Det er den værdi, botten kender i fyldøjeblikket |
| 12 | Krydser det bevægelige mål indgangen, lukker handlen ved målet med R ≤ 0. Det tælles (`maal_R_under_0_n`) | Den forsigtige side: en rigtig limitordre ville fylde på markedsprisen, ikke dårligere |
| 15 | Ved 2/dag kan den anden ordre først fyldes efter den første handels exit-bar. Er prisen allerede forbi triggeren, fyldes den på åbningen. Ligger hele lys i+1 inden i den første handel, er setuppet blokeret | Der er aldrig to positioner på én gang, og ordren følger sin egen regel fra første tilladte bar |
| 17 | N-tid matches pr. (dag, retning) | Samme princip som kandidat 2's læsning 9. Nu suppleret med time, §2 |
| 21 | N-mod har et konstant mål, lige så langt fra N-mod's eget fyld som VWAP, bare den anden vej. 1R-reglen gælder også | Det er §6's definition. N-mod kan dermed køres præcis gennem `simuler_handel` |

## 4. Betingelser for den rigtige kørsel

1. **Den eneste tilladte kodeændring** er N-tid's matching i §2, med en test der viser, at
   trækningen holder sig inden for samme dag, retning og time, og at den nærmeste time
   bruges, når timen er tom.
2. Derefter køres regressionstjekkene i `b4_k4_emt.md` §11.3 og hele testsuiten igen. De
   skal holde. Optællingens N-tid-del køres igen og rapporteres: puljens tidsprofil efter
   rettelsen og antal handler matchet til en nabotime.
3. **Koden står derefter fast.** Kørslen sker fra den commit, og rapporten oplyser dens
   hash.
4. **R = 500.**
5. **Rapport efter §10.** Bagefter: stop. §8 anvendes mekanisk og læses sammen med ejeren.
