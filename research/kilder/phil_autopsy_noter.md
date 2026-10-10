# Noter: Phil og "autopsy loop" — selvforbedrende AI-tradere

**Skrevet:** 2026-10-10 af overblikssessionen på ejerens forespørgsel. Kun læst, intet
installeret eller kørt.

**Kilder:**
- Phil, https://github.com/bennyjo/phil (Apache-2.0): README, `CLAUDE.md`, `CYCLE.md` og
  `strategy/playbook.md` læst. Ejerens indsatte quick start fra @seb.ai.
- Vektor, "autopsy loop"-guiden: https://vektor-fm.github.io/vektor-site/files/autopsy-loop-guide.md
  (kun læst som tekst).
- Vektors plugin ("Claude Code that improves itself from its sessions", .zip): **ikke hentet.**

## 1. Hvad de er

| | Phil | Autopsy loop |
|---|---|---|
| Marked | Polymarket, korte markeder, papirhandel | SPY via Alpaca, papirhandel |
| Sløjfe | afregn → scor mod markedets pris (Brier-delta) → retro → ret playbook og risiko → research → bet → commit | idé → `strategy.py` → backtest → en "kritiker" obducerer de værste tab og omskriver reglerne → igen, op til 5 runder |
| Beskyttet | motoren (`core/`), lofterne (`config/protected.json`) og proceduren. `loop.sh` ruller ændringer tilbage, og CI blokerer | risikoregler, beståelseskriterier, holdout og ordrevagten |
| Mål | `brier_delta`: er agentens sandsynlighed bedre end prisen? | beståelseskriterier, som brugeren skriver |
| Egne forbehold | "Past performance … predicts nothing" | "en startskitse", ikke kørt som helt system. Backtesten ignorerer gebyrer og slippage. Advarer selv om overfitting |

## 2. Hvad de viser

- **Phil har ingen edge.** Ifølge dens egen playbook lå agentens egne sandsynligheder i
  gennemsnit bag markedet (Brier-delta cirka +0,118). Sammenligning med bookmakere var flad.
  Bets med påstået edge over 0,10 gav 0 af 8.
- **Mange regler hviler på 1–3 observationer**, selv om Phil selv kræver cirka 15 afregninger,
  før den reagerer på en kategori.
- **Autopsy-sløjfen er en automatiseret søgning på samme data.** Hver omskrivning efter at have
  set de værste tab er et nyt forsøg, som ingen tæller. Det er præcis den fejl, vores
  præregistrering og tæller er bygget til at undgå. Vores syv kandidater viser, hvor let
  in-sample-mønstre opstår og forsvinder.

## 3. Hvad vi kan låne

Ingen af dem har en strategi, vi kan bruge på Topstep. Men tre ting i arbejdsformen er gode,
og de passer til fase 4–6 (bot, forward-test og live):

1. **Commit-hash på hver handel.** Phil stempler hvert bet med den strategiversion, det blev
   lavet under. Hos os: hver handel i forward-test og live logges med commit-hashen for den
   frosne strategi. Hører til punktet "logning".
2. **Retro pr. afvigelse med en årsag.** Phil klassificerer hvert tab som forkert skøn, dårlig
   fill eller normal varians. Hos os: i forward-testen klassificeres hver afvigelse fra
   backtesten som signalforskel, fill/slippage (C4) eller varians.
3. **Spærre for frosne filer i CI.** Phil lader CI fejle, hvis en agent-commit rører
   beskyttede filer. Vi har forseglingen i `data/holdout.py`, men kunne også lade en test
   fejle, hvis en frossen præregistrering ændres efter, at dens holdout er åbnet.

## 4. Hvad vi ikke tager

- **En strategi, der retter sig selv efter resultater.** Den bryder metodereglerne: stop efter
  hver kørsel, præregistrering og tælleren.
- **Vektors plugin.** Ukendt afsender, en .zip, og pluginnet læser alle Claude Code-sessioner.
  Sessionerne kan indeholde nøgler, og projektet har allerede haft en lækket nøgle.

## 5. Uden for dette projekt

Phils "information race" og "fact-final" (handel, når det afgørende faktum allerede er
offentligt) hører til prediction markets og er mere relevant for Polymarket-sporet end for
Topstep.
