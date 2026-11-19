# RESULTS-TEMPO: is "tempo" a real, discrete axis of the sperm whale coda alphabet?

Graded 2026-11-19 by MV2, Munim, Inc. (mv2@munimtech.com) against
[TEMPO-PREREG.md](TEMPO-PREREG.md) (registered before the job ran; the job recorded its SHA-256
dba8d18d238bc9b9d6b4781be7132f836d6578d45d9d0bde00b690e426917e96 at 2026-11-19T15:21:01Z, before
reading any data). Job `coda-tempo-v1` (tempo.py, tempo-1.0, Python 3.12.16), raw output
[results/tempo/tempo_results.json](results/tempo/tempo_results.json). Every line below that
the grader [test_tempo_results.py](test_tempo_results.py) fixes in advance is printed exactly as
it requires; the grader re-derives every decision from the raw output with its own code.
Made with AI agents; no human expert has checked this yet. Text CC BY 4.0, code Apache-2.0.

## Summary

Sharma et al. (2024, Nature Communications 15:3617) built the "sperm whale phonetic alphabet"
on five tempo types taken from the modes of one density of all coda durations pooled over
rhythms. We asked whether those modes, and the rhythm x tempo combinations, could simply come
from mixing rhythms that each have one typical duration. Reading rules fixed in advance
(TEMPO-PREREG.md section 7):

1. **The five pooled tempo modes are not a rhythm-mixing artefact.** We reproduce them exactly
   from the public data (both gates pass). When every rhythm is given a unimodal duration
   distribution of its own (the strongest version of the mixing explanation), the pooled
   density shows all five modes in 0 of 999 surrogates, while the same procedure recovers a
   true null's own modes 84.4% of the time (K4 ceiling). Same answer with the paper's own
   labels (RL).
2. **Duration is multimodal inside rhythms, including one the 2016 typology never split.**
   Silverman's test (Holm, 16 rhythms) rejects one mode in 5 rhythms: the three that the 2016
   coda types already split by duration (1+3, 4R, 5R; 5R is the pre-registered positive
   control) and two that it did not: **1+1+3**, the clan's most common coda (3,479 codas,
   rejected under both rhythm schemes), and 2+3 (rejected only under the tempo-free RF
   assignment, not under the paper's labels).
3. **It is a choice within social units, not only a difference between units.** In all five
   rejected rhythms at least one single social unit's own codas are multimodal; for 1+1+3
   that holds in 4 of its 10 eligible units (A, J, R, V).
4. **But the count of rhythm x tempo combinations is not evidence of free combination.**
   Cutting each rhythm's unimodal surrogate durations at the four tempo boundaries gives as
   many occupied combinations as the real data or more (real 34; null mean 37.5, range 35 to
   40; p = 1.000). The real codas sit in *fewer* rhythm x tempo cells than smooth durations
   would.

Reading: calibrated support for tempo as a real, discrete feature (T1 + T2 + T3, the
pre-registered reading for this outcome), concentrated in 5 of 16 rhythms, with the caveat
that counting realised combinations does not by itself show that rhythm and tempo combine
freely. 8 of 10 predictions came true.

## Prior work this connects to

Begus, Dabkowski, Sprouse, Gruber & Gero (2026, Proc. R. Soc. B 293:20252994; preprint
bioRxiv 10.1101/2025.06.09.658556) found, in DTAG recordings of four EC1 whales (628 codas),
that the duration of 1+1+3 codas with the "i" vowel is bimodal within whales (Hartigan's dip
test), and argued that part of the tempo distinction tracks vowel quality. Our finding 2-3 for
1+1+3 is an independent replication of within-1+1+3 duration multimodality on different data
(the 7,737-coda DominicaCodas set, units rather than tagged individuals), with a calibrated
test. Findings 1 and 4 (whether the pooled modes and the combination count could come from
mixing rhythms) were not tested there or in Sharma et al. We have not yet read the 2024
paper's supplementary PDF; if it holds a within-rhythm test, this is a replication of it.

## Gates and sample

Gate G1: n = 7,737 (paper 7,737): **pass**

Gate G2: maxima 0.33, 0.51, 0.80, 1.02, 1.26; minima 0.45, 0.61, 0.93, 1.08: **pass**

Tempo cut points used: 0.45, 0.61, 0.93, 1.08

Exploratory (a gate failed): **no**

Data: DominicaCodas.csv at commit 7228c8e (8,719 rows, SHA-256
53dd44fbfb0040da93656aa44883954f3abe18dd6539e90c625af86a96db6b45); sample S = EC1 clan,
0.1 s < duration < 1.75 s. Pooled tempo-type counts: 2,397, 625, 1,617, 811, 2,287.

## T2: is duration multimodal within rhythms? (Silverman k = 1, B = 999, Holm)

"power" is the calibrated K2 power (0.5/0.5 mixture) at the largest calibrated size not above
the rhythm's tested n: "low" means a non-rejection there is "not detected, low power", never
"unimodal".

RF rhythms: 18 found, 16 analysable (>= 30 codas); 7,727 codas assigned, 10 without a rhythm

| scheme | rhythm | codas | outliers | h_crit (s) | p | Holm reject | known 2016 split | power if not rejected | KDE maxima at 0.035 s |
|---|---|---|---|---|---|---|---|---|---|
| RF | 3D | 55 | 3 | 0.0120 | 0.305 | no | no | low | 0.31 |
| RF | 3R | 39 | 0 | 0.0979 | 0.167 | no | no | low | 0.14, 0.39, 0.77 |
| RF | 1+3 | 108 | 0 | 0.1147 | 0.001 | yes | yes | - | 0.39, 0.75 |
| RF | 4D | 251 | 33 | 0.0178 | 0.184 | no | no | ok | 0.52 |
| RF | 4R | 406 | 0 | 0.1947 | 0.001 | yes | yes | - | 0.23, 0.39, 0.50, 0.79, 0.96, 1.02, 1.24 |
| RF | 1+1+3 | 3,479 | 0 | 0.1352 | 0.001 | yes | no | - | 0.34, 0.83, 1.03, 1.27 |
| RF | 2+3 | 126 | 0 | 0.1319 | 0.001 | yes | no | - | 0.16, 0.27, 0.65, 0.86 |
| RF | 5R | 2,086 | 16 | 0.0982 | 0.001 | yes | yes | - | 0.33, 0.51, 0.76 |
| RF | 6i | 347 | 0 | 0.1858 | 0.009 | no | no | ok | 0.40, 0.76, 0.92, 1.01, 1.20, 1.36, 1.46, 1.70 |
| RF | 7D | 212 | 0 | 0.1473 | 0.007 | no | yes | ok | 0.41, 0.48, 0.80, 1.34, 1.57 |
| RF | 7i | 148 | 11 | 0.0823 | 0.097 | no | no | low | 0.32, 0.60, 0.93 |
| RF | 8R | 43 | 9 | 0.0824 | 0.090 | no | no | low | 0.87, 1.06, 1.25, 1.40, 1.52 |
| RF | 8i | 177 | 17 | 0.0298 | 0.027 | no | no | low | 0.35 |
| RF | 9R | 36 | 0 | 0.2560 | 0.034 | no | no | low | 0.38, 0.50, 0.63, 0.68, 0.97, 1.08, 1.21, 1.34, 1.54, 1.69 |
| RF | 9i | 129 | 10 | 0.0508 | 0.014 | no | no | low | 0.37, 0.61 |
| RF | 10i | 44 | 6 | 0.0225 | 0.453 | no | no | low | 0.37 |

T2 (RF): 5 of 16 rhythms Holm-rejected

RL rhythms: 19 found, 14 analysable (>= 30 codas); 7,263 codas assigned, 474 without a rhythm

| scheme | rhythm | codas | outliers | h_crit (s) | p | Holm reject | known 2016 split | power if not rejected | KDE maxima at 0.035 s |
|---|---|---|---|---|---|---|---|---|---|
| RL | 3D | 61 | 0 | 0.0284 | 0.223 | no | no | low | 0.31 |
| RL | 1+3 | 122 | 0 | 0.1309 | 0.001 | yes | yes | - | 0.39, 0.73 |
| RL | 4D | 219 | 2 | 0.0050 | 0.869 | no | no | ok | 0.52 |
| RL | 4R | 385 | 0 | 0.2154 | 0.001 | yes | yes | - | 0.23, 0.79, 0.96, 1.02, 1.23 |
| RL | 1+1+3 | 3,574 | 0 | 0.1198 | 0.001 | yes | no | - | 0.81, 1.03, 1.27 |
| RL | 2+3 | 77 | 0 | 0.0123 | 0.283 | no | no | low | 0.65 |
| RL | 5R | 1,816 | 287 | 0.0200 | 0.001 | yes | yes | - | 0.33 |
| RL | 6i | 182 | 0 | 0.0359 | 0.533 | no | no | low | 0.40, 0.61 |
| RL | 7D | 206 | 0 | 0.0528 | 0.408 | no | yes | ok | 1.15, 1.34, 1.57 |
| RL | 7i | 145 | 2 | 0.0438 | 0.331 | no | no | low | 0.32, 0.59 |
| RL | 8R | 41 | 2 | 0.0373 | 0.474 | no | no | low | 1.24, 1.40, 1.52 |
| RL | 8i | 178 | 12 | 0.0291 | 0.042 | no | no | low | 0.35 |
| RL | 9i | 135 | 10 | 0.0515 | 0.011 | no | no | low | 0.37, 0.61 |
| RL | 10i | 52 | 7 | 0.0218 | 0.765 | no | no | low | 0.37 |

T2 (RL): 4 of 14 rhythms Holm-rejected

T2 label (RF): **`TEMPO_DISCRETE_BEYOND_KNOWN_TYPES`**

## T1: are the five pooled modes reproduced when every rhythm is unimodal? (B = 999)

T1 (RF): f_all **0.000**; per-mode hit rates 0.999, 0.115, 0.298, 0.186, 0.035; null mean number of maxima 3.20

T1 (RL): f_all **0.000**; per-mode hit rates 1.000, 1.000, 0.007, 0.324, 0.031; null mean number of maxima 4.18

K4 ceiling: f_K4 **0.844** (pseudo-real maxima 0.35, 1.14)

T1 label (RF): **`TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO`**

T1 label (RL): **`TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO`**

Per mode (RF): the 0.33 s mode appears in 99.9% of unimodal surrogates (it is simply where the
short rhythms sit), but the 0.51, 0.80, 1.02 and 1.26 s modes appear in only 11.5%, 29.8%,
18.6% and 3.5% of them, and never all together. A unimodal-rhythm surrogate has 3.20 pooled
maxima on average, not five (4.18 under RL labels). Under RF, 4.9% of surrogates have exactly
five maxima and under RL 25.9% do, but in no surrogate do they fall on all five real
positions.

## T4: more rhythm x tempo combinations than cutting gives? (same 999 surrogates)

T4 (RF): C_obs 34; null mean 37.5 (range 35 to 40); p = 1.000

T4 (RL): C_obs 25; null mean 28.1 (range 26 to 31); p = 1.000

H(tempo | rhythm) / H(tempo) (RF): real 0.671; null mean 0.686

H(tempo | rhythm) / H(tempo) (RL): real 0.532; null mean 0.550

T4 label (RF): **`COMBINATIONS_MATCHED_BY_CUTTING`**

A cell (rhythm, tempo type) counts as occupied if it holds at least max(10, 5%) of the
rhythm's codas. In both schemes the real count lies below the whole null range: real rhythms
use fewer tempo types than unimodal durations cut at the same boundaries would, and tempo is
slightly more predictable from rhythm than in the null.

## T3: within single social units? (Silverman k = 1, B = 199, Holm within rhythm)

| rhythm | unit | codas | p | Holm reject | modal tempo type | tempo types used |
|---|---|---|---|---|---|---|
| 1+3 | N | 72 | 0.005 | yes | 0 | 1 |
| 4R | A | 320 | 0.005 | yes | 2 | 3 |
| 4R | F | 43 | 0.285 | no | 0 | 1 |
| 1+1+3 | A | 802 | 0.005 | yes | 2 | 3 |
| 1+1+3 | D | 87 | 0.010 | no | 2 | 3 |
| 1+1+3 | F | 588 | 0.015 | no | 4 | 3 |
| 1+1+3 | J | 696 | 0.005 | yes | 4 | 3 |
| 1+1+3 | N | 76 | 0.025 | no | 2 | 3 |
| 1+1+3 | R | 161 | 0.005 | yes | 4 | 3 |
| 1+1+3 | S | 165 | 0.110 | no | 4 | 2 |
| 1+1+3 | T | 72 | 0.015 | no | 4 | 4 |
| 1+1+3 | U | 662 | 0.065 | no | 4 | 2 |
| 1+1+3 | V | 170 | 0.005 | yes | 4 | 4 |
| 2+3 | F | 33 | 0.010 | yes | 0 | 2 |
| 2+3 | V | 39 | 0.110 | no | 2 | 1 |
| 5R | A | 256 | 0.005 | yes | 0 | 2 |
| 5R | D | 177 | 0.005 | yes | 0 | 2 |
| 5R | F | 312 | 0.025 | yes | 0 | 3 |
| 5R | J | 209 | 0.005 | yes | 0 | 2 |
| 5R | N | 115 | 0.010 | yes | 0 | 2 |
| 5R | R | 76 | 0.015 | yes | 0 | 2 |
| 5R | S | 241 | 0.010 | yes | 0 | 1 |
| 5R | T | 218 | 0.005 | yes | 0 | 1 |
| 5R | U | 306 | 0.005 | yes | 0 | 2 |
| 5R | V | 160 | 0.160 | no | 0 | 1 |

T3 1+3: **`WITHIN_UNIT`** (largest unit's share 0.67)

T3 4R: **`WITHIN_UNIT`** (largest unit's share 0.79)

T3 1+1+3: **`WITHIN_UNIT`** (largest unit's share 0.23)

T3 2+3: **`WITHIN_UNIT`** (largest unit's share 0.31)

T3 5R: **`WITHIN_UNIT`** (largest unit's share 0.15)

With B = 199 the smallest possible p is 0.005, so Holm across 10 units can reject at most a
few; non-rejections here are not evidence of unimodality.

## Calibration of Silverman's test (K1 negatives, K2 positives; 100 simulations each, B = 199)

| setting | n | rejections | rate |
|---|---|---|---|
| gauss | 50 | 1 of 100 | 0.01 |
| gauss | 200 | 0 of 100 | 0.00 |
| gauss | 800 | 0 of 100 | 0.00 |
| lognormal | 50 | 2 of 100 | 0.02 |
| lognormal | 200 | 1 of 100 | 0.01 |
| lognormal | 800 | 0 of 100 | 0.00 |
| mix50 | 50 | 68 of 100 | 0.68 |
| mix50 | 200 | 100 of 100 | 1.00 |
| mix50 | 800 | 100 of 100 | 1.00 |
| mix80 | 50 | 27 of 100 | 0.27 |
| mix80 | 200 | 72 of 100 | 0.72 |
| mix80 | 800 | 100 of 100 | 1.00 |

The test is conservative (at most 2% false rejections on unimodal data) and has full power
for an even two-tempo mixture from 200 codas. K3 (real positive control): 5R, which the 2016
typology split into 5R1/5R2/5R3, is rejected in T2 (p = 0.001).

## Predictions

| # | prediction | prior | outcome |
|---|---|---|---|
| P1 | Gates G1 and G2 both pass | 0.85 | **true** |
| P2 | 5R is Holm-rejected in T2 (RF) | 0.85 | **true** |
| P3 | T1 label is TEMPO_MODES_FROM_RHYTHM_MIX | 0.35 | **false** |
| P4 | T1 label is TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO | 0.35 | **true** |
| P5 | T2 label is TEMPO_DISCRETE_BEYOND_KNOWN_TYPES | 0.40 | **true** |
| P6 | T4 p < 0.05 | 0.50 | **false** |
| P7 | K1 rejection rate <= 0.10 in all six negative settings | 0.85 | **true** |
| P8 | K2 power >= 0.8 for the 0.5/0.5 mixture at n = 200 | 0.70 | **true** |
| P9 | At least one T2-rejected rhythm is WITHIN_UNIT in T3 | 0.60 | **true** |
| P10 | The RL T1 label equals the RF T1 label | 0.70 | **true** |

8 of 10 graded predictions true

Brier score **0.156** (the exact value is 1.5625 / 10 = 0.15625, a tie at three decimals,
shown here rounded half to even). Rounding note: the grader re-derives the score with plain
floating-point sums, which on some Python versions end one unit in the last place above the
tie and then print it as Brier score **0.157**. Both describe the same number.

## Things we did not predict

* **2+3 depends on the rhythm scheme.** Under the tempo-free RF assignment 2+3 is rejected
  (126 codas, 44 of them labelled "5-NOISE" in the 2016 typology); under the paper's own
  labels (77 codas) it is not (p = 0.283, low power). We therefore rest the "beyond the known
  types" finding on 1+1+3, which is rejected in both schemes, not on 2+3.
* **Under RL labels the 5R positive control is tested without 5R2.** The 3-IQR outlier rule set
  aside 287 of 1,816 5R codas, exactly the number labelled 5R2, so the RL 5R rejection
  (p = 0.001, h_crit 0.0200 s, one mode at 0.035 s) comes from finer structure within
  5R1 + 5R3. Under RF only 16 codas were set aside and the 0.33/0.51/0.76 s modes all show.
* **Fewer combinations than cutting, not just "not more".** Real C lies below the minimum of
  999 surrogates in both schemes (34 vs 35 to 40; 25 vs 26 to 31).
* **Which modes need explaining differs by scheme.** Under RF the 0.51 s and 1.26 s modes are
  the hardest for unimodal rhythms to make (11.5%, 3.5%); under RL the 0.33 and 0.51 s modes
  always appear and the 0.80 s mode almost never does (0.7%).

## Limits

Silverman's test is conservative and depends on a kernel bandwidth; T1 and T4 use the paper's
hand-chosen 0.035 s. Our RF rhythm assignment uses centroids of the 2016 coda types, not the
paper's own rhythm labels (stored as Python pickles, which we do not execute). Social units are
not individuals, and the codas of a unit are not independent of each other (bouts, exchanges),
so unit-level p values are optimistic in the same way as every coda-level analysis of these
data. One clan, one data set. Rubato and ornamentation were not tested. Nothing here says what
a tempo type means to a whale.

## Reproduce

```
python -m unittest -v test_tempo test_tempo_results
python tempo.py --out-dir out
```

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed this.
