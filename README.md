# coda-tempo-test

**Is "tempo" a real, discrete axis of the sperm whale coda alphabet?**

Sharma et al. (2024, *Nature Communications* 15:3617) report that sperm whale codas combine a
rhythm (18 click patterns) with one of five discrete **tempo types**, a key part of the
widely reported "sperm whale phonetic alphabet". The five tempo types come from the modes of
one kernel density estimate of all coda durations pooled over rhythms. Rhythms with different
numbers of clicks have different durations, so a pooled density can show several modes even
if no rhythm comes in more than one tempo.

## Result (graded 2026-11-19): [RESULTS-TEMPO.md](RESULTS-TEMPO.md)

* **The five pooled tempo modes are not a rhythm-mixing artefact.** Giving every rhythm a
  unimodal duration distribution of its own reproduces all five modes in 0 of 999 surrogates
  (a true null scores 0.844 by the same procedure). Same with the paper's own labels.
* **Duration is multimodal inside 5 of 16 rhythms** (Silverman's test, Holm): the three the
  2016 typology already split by duration (1+3, 4R, 5R; 5R is the positive control) and
  **1+1+3**, the clan's most common coda, which it never split (rejected under both rhythm
  schemes); 2+3 is rejected under one scheme only.
* **Within single social units**: every rejected rhythm is multimodal inside at least one
  unit (1+1+3 in 4 of 10 units).
* **But the rhythm x tempo combination count is not evidence of free combination**: cutting
  unimodal durations at the tempo boundaries gives as many occupied combinations or more
  (real 34, null 35 to 40, p = 1.000).
* Calibration: at most 2% false rejections on unimodal data; full power for an even
  two-tempo mixture from 200 codas. 8 of 10 pre-registered predictions true.

Reading: calibrated support for tempo as a real, discrete feature, concentrated in a few
rhythms; counting realised combinations does not by itself show free combination. For 1+1+3
this independently replicates, on different data and with a calibrated test, the
within-whale duration bimodality that Begus et al. (2026, Proc. R. Soc. B 293:20252994) tied
to coda vowel quality.

**Prior art ([PRIOR-ART.md](PRIOR-ART.md)).** After grading we read the 2024 paper's
supplement. It derives the five tempo types only from the pooled duration distribution and
never tests a rhythm-mixing null or multimodality within a single rhythm, so T1, T3 and T4 are
new as far as we can find, and T2 is new for every rhythm except 1+1+3.

## What is here

This project tests the claim directly, with calibrated nulls, on the paper's own public data
(DominicaCodas.csv, CC BY 4.0):

* **T1:** are the five pooled tempo modes reproduced when every rhythm is forced to have a single,
  unimodal duration distribution?
* **T2:** is duration multimodal *within* rhythms (Silverman's test, Holm-corrected)? Rhythms
  are assigned from normalised click intervals only, so the assignment never sees duration.
* **T3:** where it is, do single social units switch between tempos?
* **T4:** are there more rhythm x tempo combinations than cutting unimodal durations at the
  tempo boundaries gives?

The design, decision rules and ten predictions with priors were fixed in
[TEMPO-PREREG.md](TEMPO-PREREG.md) before any analysis ran. `tempo.py` (pure Python
standard library) ran as job `coda-tempo-v1`; it waited until the pre-registration was
public, then downloaded the data at a fixed commit. `test_tempo.py` holds its unit tests.
The raw output is [results/tempo/tempo_results.json](results/tempo/tempo_results.json).

**Grader, published before the result.** `test_tempo_results.py` does not import `tempo.py`.
With its own code it re-derives gates G1 and G2, every Holm decision, the T1-T4 labels, the
ten graded predictions and the Brier score from the job's raw output. It checks every p value,
occupancy count, entropy ratio, unit share and calibration rate for internal consistency, and
it fixed in advance the exact lines RESULTS-TEMPO.md must print.

```
python -m unittest -v test_tempo test_tempo_results
python tempo.py --out-dir out
```

Related: [song-zipf-test](https://github.com/munimtechnologies/song-zipf-test), MV2's
calibrated test of "linguistic laws" in humpback whale and finch song, and
[chimp-bigram-test](https://github.com/munimtechnologies/chimp-bigram-test) (chimpanzee call
combinations).

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed
this yet. Code Apache-2.0; text CC BY 4.0. Data: Sharma et al. 2024 / Dominica Sperm Whale
Project (CC BY 4.0), downloaded by the job and not redistributed (the results file holds
counts and statistics only).
