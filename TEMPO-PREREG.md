# TEMPO-PREREG: is "tempo" a real, discrete axis of the sperm whale coda alphabet?

Registered 2026-11-19 by MV2, Munim, Inc. (mv2@munimtech.com), before any analysis below has
been run. Made with AI agents; no human expert has checked this design yet. Text CC BY 4.0,
code Apache-2.0. The job (`coda-tempo-v1`, `tempo.py`) waits until this file is public on
GitHub and records its SHA-256 before it reads any data. This file is never edited after
publication; any change goes in a dated AMENDMENT file.

## 1. The claim under test

Sharma, Gero, Payne, Gruber, Rus, Torralba & Andreas (2024), "Contextual and combinatorial
structure in sperm whale vocalisations", *Nature Communications* 15:3617
(doi:10.1038/s41467-024-47221-8), report that the codas of the Eastern Caribbean clan are
built from two context-independent features, **rhythm** (18 normalised inter-click-interval
patterns) and **tempo** (5 discrete duration categories), plus rubato and ornamentation. This
"sperm whale phonetic alphabet" was widely reported; it raises the estimated repertoire from 21
coda types to "at least 143 combinations frequently realised".

The evidence for five discrete tempo types is, in the paper and its code
(`code/2-tempo.ipynb`, repository pratyushasharma/sw-combinatoriality, commit 7228c8e):

* a Gaussian kernel density estimate (bandwidth 0.035 s, chosen by hand) of the durations of
  all 7,737 EC1-clan codas with 0.1 s < duration < 1.75 s, **pooled over all rhythms**;
* its five local maxima (0.33, 0.51, 0.80, 1.02, 1.26 s) and four minima (0.45, 0.61, 0.93,
  1.08 s), which define the tempo types.

No multimodality test, no within-rhythm analysis and no null model for the tempo modes or
for the claimed free combination of rhythm and tempo is reported in the main text or in that
notebook (we could not extract text from the supplementary PDF; if it holds such a test, our
result is a replication of it, and we will say so).

**The gap.** Rhythm types differ in click number, so they differ in duration. A pooled
duration density is a mixture of the rhythms' own duration distributions, and it can have
several modes even if **no single rhythm comes in more than one tempo**. Likewise, cutting
each rhythm's continuous duration distribution at fixed boundaries "realises" several
rhythm x tempo combinations whether or not tempo is a discrete choice. Prior-art search
(2026-11-19: Google Scholar-style web search, arXiv, bioRxiv, Nature Matters Arising, the
2026 reanalyses of the same data by Assayag et al., Bioacoustics 35:472, and Sinha & Chavan,
arXiv:2606.16084, and the public repo Ardjano/whale-coda-dynamics) found no test of either.

## 2. Question and the "wow" either way

Are the five sperm whale tempo types a discrete axis of their own, or what you get by mixing
rhythm types that each have one characteristic duration?

* If the pooled modes and the rhythm x tempo combinations are reproduced when every rhythm is
  forced to be unimodal in duration, the alphabet's second axis is not supported by the
  evidence offered, and the repertoire estimate shrinks back towards the coda types.
* If they are not, and duration is multimodal within rhythms that the 2016 coda typology did
  not already split, this is the first calibrated evidence that tempo is a discrete,
  combinable feature, which strengthens one of the most publicised claims in animal
  communication.

## 3. Data

`data/DominicaCodas.csv` at commit 7228c8eed2cc27ddd23b74c51aeccec9d762389e of
github.com/pratyushasharma/sw-combinatoriality (CC BY 4.0, Zenodo 10.5281/zenodo.10817697;
8,719 codas recorded by the Dominica Sperm Whale Project). The job downloads it and records its
SHA-256; it is not redistributed. Columns used: nClicks, Duration, ICI1-ICI9, CodaType
(Gero, Whitehead & Rendell 2016 type), Clan, Unit.

**Sample S:** Clan = EC1 and 0.1 < Duration < 1.75 (as in the notebook).

**Gate G1:** |S| = 7,737. **Gate G2:** the exact Gaussian KDE (bandwidth 0.035) of S on the grid
0.10, 0.11, ..., 1.75 has strict interior maxima [0.33, 0.51, 0.80, 1.02, 1.26] and minima
[0.45, 0.61, 0.93, 1.08], each within 0.011 s. If a gate fails, everything still runs and is
reported, but every label is marked exploratory. Tempo type of a coda = number of our
G2 minima below its duration (the four printed minima are used if ours are not four).

## 4. Rhythm labels

The 2016 coda types were made by OPTICS clustering of **absolute** ICIs (Gero et al. 2016,
RSOS 3:150372), so they already contain tempo: 5R1/5R2/5R3, 4R1/4R2, 1+31/1+32, 7D1/7D2
are one rhythm at different durations. Using those labels to look for tempo would be
partly circular.

* **RF (primary, tempo-free):** merged rhythm m = CodaType with a trailing tempo index removed
  (regex `^(\d+[RDi]|1\+3)([1-9])$` -> group 1). Centroid of each (nClicks, m) with >= 5
  labelled codas in S = mean normalised ICI vector (ICI_j / sum of ICIs, j = 1..n-1). Every
  coda in S with 3-10 clicks and positive ICIs (labelled or "NOISE") is assigned to the
  nearest centroid with the same click count. Only normalised ICIs are used, so assignment
  never sees duration.
* **RL (secondary):** labelled codas only, rhythm = (nClicks, m).
* **Known variants K:** rhythms whose codas carry >= 2 different 2016 labels with >= 5 codas
  each (expected: 5R, 4R, 1+3, 7D).
* A rhythm is analysable if it has >= 30 codas in S. Codas without a rhythm keep their real
  durations in every null.

Within a rhythm, durations outside [Q1 - 3 IQR, Q3 + 3 IQR] are set aside as outliers for
the multimodality tests (counted and reported; in T1 they keep their real values).

## 5. Tests (all seeded; exact code in tempo.py)

**Silverman's test** (Silverman 1981) of H0 "at most k modes": h_crit = smallest Gaussian KDE
bandwidth with <= k modes (bisection on log h in [0.001, 1] s, 24 steps; modes counted on
bins of max(1 ms, h/20)); smoothed bootstrap y = mean + (x* - mean + h_crit e) / sqrt(1 +
h_crit^2 / s^2); p = (1 + #{bootstrap KDE at h_crit has > k modes}) / (B + 1).

* **T1 (main; the pooled tempo modes from rhythm mixture?).** Null U: each analysable RF rhythm's
  non-outlier durations are replaced by a Silverman smoothed bootstrap at its own h_crit for
  k = 1 (a unimodal draw of the same size); outliers, small rhythms and unassigned codas keep
  their real durations. For each of B = 999 surrogates, the pooled KDE (bandwidth 0.035, same
  grid) is computed. A real maximum is reproduced if the surrogate has a maximum within
  0.03 s. f_all = share of surrogates reproducing all five. Per-mode rates are reported.
  **K4 (ceiling):** one data set drawn from null U itself is treated as "real" and T1 is
  repeated on it (B = 199); its f_all, f_K4, is the best a true null can score.
  Label: f_K4 < 0.2 -> `T1_UNDERPOWERED`; else f_all >= 0.5 f_K4 -> `TEMPO_MODES_FROM_RHYTHM_MIX`;
  else f_all < 0.05 -> `TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO`; else
  `TEMPO_MODES_PARTLY_FROM_RHYTHM_MIX`.
* **T2 (discrete tempo within rhythms?).** Silverman k = 1, B = 999, for every analysable RF
  rhythm (non-outliers), Holm at alpha 0.05 across rhythms. Label: no rejection ->
  `NO_WITHIN_RHYTHM_TEMPO_MODES`; a rejection in a rhythm outside K ->
  `TEMPO_DISCRETE_BEYOND_KNOWN_TYPES`; rejections only in K ->
  `TEMPO_DISCRETE_ONLY_IN_KNOWN_TYPES`. Descriptive: each rhythm's KDE maxima at 0.035.
* **T3 (a whale-unit choice or a unit signature?).** For each T2-rejected rhythm, Silverman
  k = 1 (B = 199) within each social unit with >= 30 of its codas, Holm within the rhythm.
  Rhythm label: any rejection -> `WITHIN_UNIT`; else >= 2 eligible units with different modal
  tempo types -> `BETWEEN_UNITS`; else `UNRESOLVED`. Unit share of the largest unit reported.
* **T4 (more rhythm x tempo combinations than cutting gives?).** A cell (rhythm, tempo type)
  of an analysable rhythm with n codas is occupied if it holds >= max(10, ceil(5% of n))
  codas. C_obs = occupied cells; null = the same 999 T1 surrogates; one-sided p = (1 +
  #{C_null >= C_obs}) / 1000. p < 0.05 -> `MORE_COMBINATIONS_THAN_CUTTING`, else
  `COMBINATIONS_MATCHED_BY_CUTTING`. Descriptive: H(tempo | rhythm) / H(tempo), real and null.
* T1, T2 and T4 are repeated with RL labels (secondary).

**Calibration of Silverman's test (K1, K2)**, 100 simulations each, B = 199, n = 50, 200, 800,
after the same trimming: negatives N(0.42, 0.08) and lognormal (median 0.4 s, sigma 0.25);
positives 0.5/0.5 and 0.8/0.2 mixtures of N(0.33, 0.045) and N(0.51, 0.045) (the two lowest
tempo modes). **K3 (real positive control):** rhythm 5R, which the 2016 typology split into
5R1/5R2/5R3, must be rejected in T2.

## 6. Predictions (priors fixed now; Brier score over graded ones)

| # | prediction | prior |
|---|---|---|
| P1 | Gates G1 and G2 both pass | 0.85 |
| P2 | 5R is Holm-rejected in T2 (RF) | 0.85 |
| P3 | T1 label is TEMPO_MODES_FROM_RHYTHM_MIX | 0.35 |
| P4 | T1 label is TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO | 0.35 |
| P5 | T2 label is TEMPO_DISCRETE_BEYOND_KNOWN_TYPES | 0.40 |
| P6 | T4 p < 0.05 | 0.50 |
| P7 | K1 rejection rate <= 0.10 in all six negative settings | 0.85 |
| P8 | K2 power >= 0.8 for the 0.5/0.5 mixture at n = 200 | 0.70 |
| P9 | At least one T2-rejected rhythm is WITHIN_UNIT in T3 | 0.60 |
| P10 | The RL T1 label equals the RF T1 label | 0.70 |

A prediction whose inputs are missing is "not graded".

## 7. How results will be read (fixed now)

* `TEMPO_MODES_FROM_RHYTHM_MIX` + `COMBINATIONS_MATCHED_BY_CUTTING`: the published evidence for
  five discrete tempo types and for free rhythm x tempo combination is reproduced by rhythms
  with one duration distribution each. Whatever T2 finds then marks where tempo is real.
* `TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO` + `TEMPO_DISCRETE_BEYOND_KNOWN_TYPES` + a `WITHIN_UNIT`
  rhythm: calibrated support for tempo as a discrete, combinable axis.
* If K2 power at a rhythm's size is below 0.8, a non-rejection there is reported as "not
  detected, low power", never as "unimodal".
* Rubato and ornamentation are not tested here.

## 8. Limits known in advance

Silverman's test is conservative and h_crit-based nulls are broad; KDE mode counts depend on
bandwidth (we keep the paper's 0.035 s for T1 and T4). The rhythm assignment uses the 2016
centroids, not the paper's own rhythm labels (stored there as Python pickles, which we do not
execute). Units are not independent of rhythm use. One clan, one data set.
