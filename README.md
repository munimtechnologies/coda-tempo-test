# coda-tempo-test

**Is "tempo" a real, discrete axis of the sperm whale coda alphabet?**

Sharma et al. (2024, *Nature Communications* 15:3617) report that sperm whale codas combine a
rhythm (18 click patterns) with one of five discrete **tempo types**, a key part of the
widely reported "sperm whale phonetic alphabet". The five tempo types come from the modes of
one kernel density estimate of all coda durations pooled over rhythms. Rhythms with different
numbers of clicks have different durations, so a pooled density can show several modes even
if no rhythm comes in more than one tempo.

This project tests that directly, with calibrated nulls, on the paper's own public data
(DominicaCodas.csv, CC BY 4.0):

* **T1:** are the five pooled tempo modes reproduced when every rhythm is forced to have a single,
  unimodal duration distribution?
* **T2:** is duration multimodal *within* rhythms (Silverman's test, Holm-corrected)? Rhythms
  are assigned from normalised click intervals only, so the assignment never sees duration.
* **T3:** where it is, do single social units switch between tempos?
* **T4:** are there more rhythm x tempo combinations than cutting unimodal durations at the
  tempo boundaries gives?

The design, decision rules and ten predictions with priors are fixed in
[TEMPO-PREREG.md](TEMPO-PREREG.md) before any analysis runs. `tempo.py` (pure Python
standard library) runs as job `coda-tempo-v1`. It waits until the pre-registration is
public, then downloads the data at a fixed commit. `test_tempo.py` holds its unit tests.
Results will be published here whichever way they fall.

Status (2026-11-19): registered and queued; no results yet.

```
python -m unittest -v test_tempo
python tempo.py --out-dir out
```

Related: [song-zipf-test](https://github.com/munimtechnologies/song-zipf-test), MV2's
calibrated test of "linguistic laws" in humpback whale and finch song.

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed
this yet. Code Apache-2.0; text CC BY 4.0. Data: Sharma et al. 2024 / Dominica Sperm Whale
Project (CC BY 4.0), downloaded by the job and not redistributed.
