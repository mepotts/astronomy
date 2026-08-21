**Coverage: 19,874 deg² = 48.18% of the sky** (93 tiles). 'Paper expected' = Suazo et al. 2024 Table 4 all-sky counts × 0.4818. Intervals are exact Poisson 68% on the observed count.

| stage | γ ≥ 0.1 | γ ≥ 0.01 | paper expected | ratio (primary) |
|---|---|---|---|---|
| parent sample (Gaia <300 pc x 2MASS x AllWISE) | — | — | 2,408,854.2 | — |
| W3 and W4 both detected (C2a) | 220,632 | 220,632 | 154,166.7 | **1.43×** [1.43–1.43] |
| cc_flags clean (C2b) | 161,634 | 161,634 | — | — |
| ... with full 10-band photometry | 160,410 | 160,410 | — | — |
| ... inside the template M_G window | 158,097 | 158,097 | — | — |
| RMSE <= 0.2 star+DS grid fit (C3) | 4,773 | 27,828 | 5,416.5 | **0.88×** [0.87–0.89] |
| + Gvar, RUWE, ext_flg, classprob (C5b-e) | 4,257 | 20,292 | 2,474.9 | **1.72×** [1.69–1.75] |
| + W3 & W4 S/N >= 3.5 (C6) -- pre-visual survivors | 845 | 2,472 | 177.3 | **4.77×** [4.60–4.94] |
| final candidates (C4 CNN + C7 visual) | — | — | 3.4 | — |

**Sky-wide projections** (observed count ÷ sky fraction 0.4818; the projection is only as good as the unbiasedness of the tile order — see PR-1):

| stage | γ ≥ 0.1 projected | γ ≥ 0.01 projected | paper all-sky |
|---|---|---|---|
| W3 and W4 both detected (C2a) | 457,960 [456,985–458,938] | 457,960 [456,985–458,938] | 320,000 |
| cc_flags clean (C2b) | 335,500 [334,665–336,336] | 335,500 [334,665–336,336] | — |
| ... with full 10-band photometry | 332,959 [332,128–333,793] | 332,959 [332,128–333,793] | — |
| ... inside the template M_G window | 328,158 [327,333–328,986] | 328,158 [327,333–328,986] | — |
| RMSE <= 0.2 star+DS grid fit (C3) | 9,907 [9,764–10,053] | 57,762 [57,416–58,110] | 11,243 |
| + Gvar, RUWE, ext_flg, classprob (C5b-e) | 8,836 [8,701–8,974] | 42,120 [41,824–42,417] | 5,137 |
| + W3 & W4 S/N >= 3.5 (C6) -- pre-visual survivors | 1,754 [1,694–1,816] | 5,131 [5,028–5,236] | 368 |