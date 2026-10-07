# B4 kandidat 2 — tillæg: beslutninger efter optællingen, før kørslen

**Skrevet:** 2026-10-07 af overblikssessionen. Det er skrevet efter Code's trin 1 (kode
c2de5e5, optælling 7263fc6) og **før** den rigtige kørsel. Ingen R, vinderrate eller
udfald er set. `b4_k2_nowick.md` gælder uændret, undtagen hvor dette tillæg siger andet.
**Besluttet af ejeren 2026-10-07:** A på alle tre spørgsmål.

## 1. De to 2R-varianter med 3 lys bliver i testen (beslutning 1A)

**daily · 3 lys · 2R** (533 handler) og **4H · 3 lys · 2R** (559 handler) klarer ikke §7's
krav om mindst 603 handler ved 2R. Deres MDE med Šidák 12 er 0,213 og 0,208 R.

- De bliver i testen uændret og indgår i Westfall-Young som alle andre varianter.
- Rapporten skriver deres MDE ud. Det er kun en effekt mellem 0,20 og cirka 0,21 R, de to
  varianter ikke kan se.
- **Tælleren forbliver 28.**

## 2. Vinderraten (beslutning 2A)

§10's formel gav samme tal brutto og netto, fordi omkostningen ikke ændrer, om målet blev
ramt. Den erstattes af:

| kolonne | formel |
|---|---|
| `win_rate_pct_brutto` + Wilson-CI | andel af handler med `R_brutto > 0` |
| `win_rate_pct_netto` + Wilson-CI | andel af handler med `R_netto > 0` |
| `udfald_maal_pct` | mål ramt / handler_n, uændret |

## 3. Code's 15 læsninger — godkendt (beslutning 3A)

De står i docstringen i `research/b4_k2_nowick.py` og er godkendt uden ændringer. Disse fem
kan flytte noget:

| nr | læsning | hvorfor den er rigtig |
|---|---|---|
| 3 | Forskelsjusteringen sker på 1m, før HTF-lysene bygges | Alle 19 ruller ligger kl. 18 eller 19 CT, inde i et daily- og et 4H-lys. Spring på op til 210 point ville ellers give falske brud på daily |
| 5 | Lukker et HTF-lys både over toppen og under bunden, er tilstanden uændret | Sker 0 gange på daily og 1 gang på 4H |
| 7 | På halve dage annulleres hvilende ordrer kl. 11:30 CT | Samme grænse som `fl.vindue_mask` bruger for nye signaler |
| 9 | Nulmodellen følger §4d fuldt ud og matches pr. ET-dag og HTF-tilstand | Lys der selv er 10-lys-ekstremet, springes også over i nulmodellen. Så adskiller den sig fra modellen alene på væge, ikke på placering |
| 13 | +0,20 R gælder punktestimatet; CI-betingelsen er CI-nedre > 0 | Samme læsning som kandidat 1's trin 2-tillæg |

## 4. Rettelse

§7's krav ved 1R er **mindst 302 handler**, ikke 301. Grænsen er
`(3,4719 / 0,20)² = 301,35`, og det skal rundes op. Det ændrer intet: den laveste 1R-variant
har 533 handler.

## 5. Det optællingen viser — skrevet ned før udfaldene

Det her er optællinger, ikke udfald. Det skrives ned nu, så læsningen bagefter ikke kan
tilpasses resultatet.

- **Strejf er sjældne:** 4–8 pr. variant. Fyld ved berøring giver kun 1–6 handler mere.
  Min forventning i §12 om hyppige strejf var forkert. Diagnosen om køplacering i §9 kan
  derfor næsten ikke ændre afgørelsen.
- **Nulmodellen fyldes oftere:** 64–76% af signalerne mod 45–63% for modellen. Et lys med
  væge har sin åbning inde i lysets eget spænd, tættere på prisen. Testen måler pr.
  handel, så forskellen i antal er ikke en skævhed i testen. Den skrives dog som forbehold
  ved fortolkningen: nulmodellens handler er retests af nærmere niveauer.
- **Cirka en handel hver anden dag:** hovedvarianten har 611 handler på 1.173 dage.
  - Det økonomiske krav på +0,20 R blev udledt ved 0,9 handler om dagen. Kravet står
    uændret.
  - Hvis en variant fryses, tager Combinen ved det tempo cirka 1,7 gange så lang tid som
    regnet i `b4_k1_trinA.md` §6. Det skrives med i læsningen.
- **Dyr hale:** `risiko_pt_p10` er 4,25 point, og `omk_R_netto_p90` er 0,31 R. Halen er
  ikke filtreret, men den er synlig.

## 6. Betingelser for den rigtige kørsel

1. **Den eneste tilladte kodeændring før kørslen** er vinderratens formel i §2 med en test.
   Derefter køres regressionstjekkene i `b4_k2_nowick.md` §11.3 igen, og de skal holde.
2. **Koden står derefter fast.** Kørslen sker fra den commit, og rapporten oplyser dens
   hash.
3. **R = 500.** Tidsmålingen forventer cirka 26 sekunder.
4. **Rapport efter §10 og dette tillæg.** Bagefter: stop. Ingen ændringer og ingen
   forslag. §8 anvendes mekanisk og læses sammen med ejeren.
