# B4 kandidat 1 — trin 2, læst: kandidat 1 parkeres

**Skrevet:** 2026-09-25 af overblikssessionen, efter kørslen, læst sammen med ejeren.
Tallene står i `b4_k1_trin2.md` og `.csv` (commit 5048062, kørt fra 432d3d9). Intet er kørt
igen.

## 1. Kan tallene troes

| tjek | resultat |
|---|---|
| De tre regressionstjek i §10 | OK |
| 5m-testen (berøringsbarens længde) | fem tests, alle bestået |
| Udfaldsandele summerer til 100 | ja, alle otte varianter |
| Handler pr. dag | 1,04-1,15 i gennemsnit; højst to, som disciplinreglerne tillader |
| Røgtesten | oplyst; kun struktur læst, filerne slettet, intet ændret bagefter |

## 2. Afgørelsen efter §7 — række 1, stopreglen

| spor | β_R_pr_scoretrin | CI95 | p_ensidet |
|---|---|---|---|
| A, 15m/1h | −0,034 | [−0,072; 0,004] | 0,96 |
| B, 5m/15m | −0,029 | [−0,052; −0,005] | 0,99 |

**Middel netto-R stiger ikke med scoren. Den falder.** På spor B ligger hele intervallet under
nul: flere af videoens kriterier giver ringere handler, ikke bedre. Kandidat 1 parkeres.

## 3. Sikringerne mod at overse en edge — alle brugt, ingen ændrer afgørelsen

| sikring | udfald |
|---|---|
| Styrke | MDE 0,055 og 0,040 R pr. trin. Testen kunne se en stigning; den så et fald |
| Alle handler | 3.286 og 8.948 skyggehandler |
| Tvetydige minutter | 0,6% og 1,3% af handlerne. I bedste fald er β stadig negativ (p 0,95 og 0,91). Ingen tickdata nødvendig |
| Fyldningsreglen | strejf rapporteret; ændrer intet |

## 4. Hvad vi lærte — til de næste kandidater, ikke til at redde denne

- **Retesten holder omkring 50%, uanset score** (`holder_pct` 49-51% i alle otte varianter).
- **Kriterium 1 (brud på struktur) og 4 (inducement) er begge negative med CI klar af nul på
  begge spor.** Begge betyder at prisen er gået langt væk og derefter kommer hurtigt tilbage
  og tager bunde på vejen. En retest efter sådan en modbevægelse brydes oftere, end den
  holder. Det ligner kortsigtet momentum snarere end ordrer der forsvarer niveauet. Det er en
  iagttagelse fra in-sample-data, ikke et fund der kan bygges direkte på.
- **Rigtige zoner klarer sig bedre end tilfældigt placerede med samme score** (spor A −0,002
  mod −0,081; spor B −0,084 mod −0,204), men ikke signifikant efter korrektion, og alt er
  negativt. Niveauet rummer måske lidt information, men langt fra nok til omkostninger og
  2:1-geometri.
- **Designlektie:** Westfall-Young over rå middelværdier på tværs af spor med forskelligt
  nulniveau lader sporet med det højeste nulniveau dominere. Næste gang standardiseres
  statistikken, fx som afstand til nulmodellens median.
- Spor B's omkostninger (median 0,10 R pr. handel) vejer tungt ved backtestens prisniveau.

## 5. Status

| emne | status |
|---|---|
| Kandidat 1 | **Parkeret** 2026-09-25 |
| Tælleren | 16 forsøg; følger med til næste kandidat |
| Holdout (2024 →) | uåbnet og ukøbt for MNQ — ren til næste kandidat |
| Genbrugeligt | data, motor, sizing, disciplinregler, nulmodel, Westfall-Young, rapportvej, holdout-segl |
