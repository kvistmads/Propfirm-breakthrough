# Lånte moduler

To filer i `research/` er ikke skrevet her. De er løftet fra
[HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) (MIT), som en del af
gennemgangen 2026-09-17.

| fil her | oprindelse | uændret? |
|---|---|---|
| `research/multipletesting.py` | `agent/src/quantlib/multipletesting.py` | kun import ændret |
| `research/crossvalidation.py` | `agent/src/quantlib/crossvalidation.py` | ja |
| `tests/test_multipletesting.py` | `agent/tests/quantlib/test_multipletesting.py` | kun import ændret |
| `tests/test_crossvalidation.py` | `agent/tests/quantlib/test_crossvalidation.py` | kun import ændret |

`research/normal.py` og `tests/test_normal.py` er vores egne.

## Hvorfor de blev hentet

`multipletesting.py` leverer Deflated Sharpe Ratio, Probability of Backtest
Overfitting (CSCV), Benjamini-Hochberg FDR og den forventede maksimale Sharpe
under nulhypotesen. `crossvalidation.py` leverer purged k-fold med embargo,
kombinatorisk purged CV og lækagedetektion ved foldgrænser.

Det er præcis det apparat B4 mangler: en måde at sige hvor meget af en observeret
edge der er søgeheld. Alternativet var at skrive det selv. Bailey og López de
Prados formler er ikke svære at skrive forkert, og disse er dækket af tests der
viser at korrektionen rent faktisk bider — en Sharpe der består ukorrigeret og
falder når antallet af forsøg lægges på bordet.

## Hvad der blev ændret

Kun én ting: `from scipy.stats import norm` blev til `from research.normal import
norm`. Repoet har ikke scipy med vilje (se `requirements.txt`), og de to moduler
brugte kun to funktioner derfra — `norm.cdf` og `norm.ppf`. De er skrevet i
`research/normal.py` med `math.erfc` og Wichuras AS241.

Intet andet er rørt. Ingen omskrivning af logik, ingen oversættelse af
docstrings.

## Hvordan de blev verificeret

De medfølgende tests blev kørt, og derudover blev importen af scipy blokeret på
fortolkerniveau under en kørsel, for at vise at ingen sti falder tilbage på den:

| kørsel | resultat |
|---|---|
| deres 79 tests, som de kom | 79 passed |
| efter importændringen, plus 37 egne for `normal.py` | 116 passed |
| samme, med `import scipy` hårdt blokeret | 116 passed |

`research/normal.py` blev målt mod scipy over 20.001 punkter på cdf og 24.001 på
ppf:

| funktion | maks afvigelse mod scipy |
|---|---|
| `cdf` | 2,220e-16 absolut |
| `ppf` | 7,594e-16 relativt |

Det er maskinpræcisionens gulv. Testene i `tests/test_normal.py` holder dog
**ikke** mod scipy — de holder mod referenceværdier beregnet i 60 decimaler med
mpmath og skrevet ind som konstanter, så de også består på en maskine uden scipy.

## Hvad der IKKE blev hentet

Platformen. Vibe-Trading vil have 13 LLM-udbydere, 10 broker-connectors og 27
datakilder. Vi har vores eget apparat.

Og ikke deres tal. Deres futures-motor har MNQ med multiplikator 2 — samme som
vores verificerede $2 pr. indekspoint — men kommissionen står som $0,62 pr. side,
hvilket er en generisk broker-sats og ikke Topsteps. Rul og udløb er ikke
modelleret, og deres standardinterval er dagsbarer. Metoden er værd at låne.
Tallene er ikke.

## Licens

MIT. Ophavsret 2026 Vibe-Trading Contributors. Fuld licenstekst:
https://github.com/HKUDS/Vibe-Trading/blob/main/LICENSE
