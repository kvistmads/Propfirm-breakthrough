# B4 — edge-kravet, tillæg: Code's spørgsmål besvaret, før kørslen

**Skrevet:** 2026-10-09 af overblikssessionen, efter Code's trin 1 (8774973) og **før**
gitteret er kørt.

**Gyldighed:** tillægget gælder, når ejeren committer det. Commit'en er ejerens
godkendelse. `b4_edgekrav.md` gælder uændret, undtagen hvor dette tillæg siger andet.

## 1. Trin 1 er godkendt

- Alle 8 tests i §7.2 består, og det gør hele testsuiten også (1.156 bestået).
- Gambler's ruin giver 0,4004 mod forventet 0,40.
- Krydstjekket mod `mll_ruin.py` ligger inden for Wilson-intervallet ved WR 0,40 og 0,34.
- **Én celle er set under udviklingen:** Sharpe 1,0 med σ = $300. Beslutningsreglen i §6
  ligger fast og kan ikke flyttes af det. Det noteres her for gennemsigtighedens skyld.

## 2. Svar på de fem spørgsmål

| nr | spørgsmål | svar |
|---|---|---|
| 1 | Lige langt til DLL og MLL | **Det tæller som brud**, som Code har læst det. Når saldoen rammer MLL, er kontoen brudt, uanset om DLL rammes samtidig. En egen daglig grænse i botten, der ligger før MLL, er punkt C5 og hører ikke til denne model |
| 2 | Abonnement og reset | **Rettes.** Topstep: "Resetting your account pushes your Rebill date out 30 days". Et reset til $49 erstatter altså næste månedsbetaling. **Betalingerne i Combine:** $49 ved start, $49 ved hvert reset, og ellers $49, når der er gået 21 handelsdage siden seneste betaling. På $95-planen er det samme med $95 |
| 3 | XFA starter dagen efter beståelse | **Godkendt.** Det er en smule optimistisk, men effekten er lille |
| 4 | XFA-saldo, der ikke er udbetalt ved årets slut | **Godkendt: den tæller ikke med** (konservativt). Ny diagnose: forventet ikke-udbetalt XFA-saldo ved horisonten, så vi kan se, hvor meget der ligger uden for tallet |
| 5 | Størrelsen for S_hurtig | **Hovedlæsning:** ved den størrelse, der giver højest forventet nettoværdi. Den anden læsning, størrelsen der maksimerer P(første udbetaling ≤ 63 dage), rapporteres ved siden af. Beslutningen i §6 tages på S_min_EV |

## 3. To tilføjelser

1. **Den bedste celle regnes igen med nye frø.**
   - For hver Sharpe vælges den bedste størrelse på de oprindelige 20.000 stier.
   - Derefter regnes cellen igen på 20.000 nye stier, og **det tal er hovedtallet** for
     forventet nettoværdi og dens interval.
   - Det fjerner den lille optimisme, der kommer af at vælge den bedste af 100 celler.
   - S_min_EV regnes på de nye tal.
2. **Interpolationen i kravet får en test.**

## 4. Betingelser for kørslen

1. **De eneste tilladte kodeændringer:**
   - betalingsreglen i §2.2, med en test;
   - diagnosen i §2.4;
   - begge læsninger i §2.5;
   - genberegningen i §3.1;
   - testen i §3.2.
2. Hele testsuiten skal bestå igen. Koden committes, og kørslen sker fra den commit.
3. **Hovedgitteret og de seks følsomhedsgitre i §5 køres**, cirka 2,6 timer.
4. **Rapport efter §4 og §8:**
   - kravet;
   - kurven over Sharpe, ved den bedste størrelse og i disciplinzonen;
   - referencepunkterne;
   - følsomhederne.
5. Bagefter: stop. §6 anvendes mekanisk og læses sammen med ejeren.

## Kilde

- Topstep, *What is a Reset?* (2026-10-09): "Resetting your account pushes your Rebill date
  out 30 days" — https://help.topstep.com/en/articles/8284128-what-is-a-reset
