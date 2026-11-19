# Prior art for coda-tempo-test (checked 2026-11-19, after grading)

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Text CC BY 4.0.

## What the 2024 paper's own supplement does

Sharma et al. 2024 (Nat Commun 15:3617), Supplementary Information
(`41467_2024_47221_MOESM1_ESM.pdf`, 17 pages, sha256 7e9ea853...1b88; text extracted by our
job `coda-si-text-v1` with pypdf 5.1.0), section 3 "Tempo":

* **3.1 Clustering.** The tempo types are the modes of one Gaussian kernel density estimate of
  all DSWP coda durations, pooled over rhythms, with bandwidth h = 0.035 chosen to minimise
  the mean integrated squared error. It finds 5 peaks at 0.33, 0.51, 0.8, 1.02 and 1.26 s with
  end points 0.45, 0.61, 0.93 and 1.08 s (our gate G1 reproduces these).
* **Why five.** Merging tempo clusters 4 and 5 would leave a bimodal distribution of durations
  inside the merged cluster; merging clusters 1 and 2 would make rubato bimodal inside the
  new cluster 1 (Supplementary Figs. 8 and 9).
* A footnote says rhythm and tempo are not statistically independent: some rhythm types are
  more likely to have certain tempo types.
* Sections 2 and 4 test duration matching between adjacent and overlapping codas against
  permutation nulls that resample durations within each discrete coda type.

## What it does not do, and what is new here

* **No rhythm-mixing null.** Every argument for the five modes uses the pooled duration
  distribution. Nothing tests whether a mixture of rhythms, each with one typical duration,
  would give the same pooled peaks. That is our T1 (0 of 999 surrogates reproduce all five).
* **No within-rhythm multimodality test.** The supplement never asks whether any single
  rhythm's durations have more than one mode. That is our T2 (5 of 16 rhythms, including
  1+1+3) and T3 (inside single social units).
* **No null for the combination count.** The supplement's combinatorial inventory (section
  6.2) counts rhythm x tempo combinations. Our T4 shows smooth, single-tempo durations cut at
  the same boundaries give as many or more (real 34, null 35 to 40).

So T1, T3 and T4 are new as far as we can find, and T2 is new for every rhythm except 1+1+3, where Begus,
Dabkowski, Sprouse, Gruber and Gero (2026, Proc. R. Soc. B 293:20252994) had already found
bimodal durations within 3 of 4 tagged whales on different recordings (Hartigan's dip test,
628 codas). Our 1+1+3 result independently replicates theirs with a calibrated test.

Begus et al. point out the problem in passing ("different coda types have different intrinsic
lengths") and therefore restrict their analysis to durations within coda types. They do not
test whether the five pooled tempo modes survive a rhythm-mixing null.

Searches on 2026-11-18 and 2026-11-19 (web search, Europe PMC, bioRxiv) found no other
published test of the tempo types against a rhythm-mixing null. Related work that uses the
tempo types without testing them: "Vowel- and Diphthong-Like Spectral Patterns in Sperm Whale Codas" (Open Mind) and the
2025 Scientific Reports description of a sperm whale birth.
