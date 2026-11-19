# SPDX-License-Identifier: Apache-2.0
# test_tempo_results.py: the grader for coda-tempo-test (TEMPO-PREREG.md, job coda-tempo-v1),
# written and published BEFORE the job has produced any result. It does not import tempo.py.
# With its own code it re-derives gates G1/G2, every Holm decision, the T1/T2/T3/T4 labels, the
# ten graded predictions and the Brier score from the raw output; checks every p value, count,
# share and ceiling for internal consistency; checks them against the job's own grading; and
# fixes now the exact lines RESULTS-TEMPO.md must print (render_md_lines).
# Until results/tempo/tempo_results.json exists the result tests are skipped; the toy-data
# tests always run. Stdlib only. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import copy
import hashlib
import json
import math
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "tempo", "tempo_results.json")
MD = os.path.join(HERE, "RESULTS-TEMPO.md")
PREREG = os.path.join(HERE, "TEMPO-PREREG.md")
HAVE = os.path.exists(RES)

VERSION = "tempo-1.0"
DATA_SHA = "7228c8eed2cc27ddd23b74c51aeccec9d762389e"
ALPHA = 0.05
N_EXPECTED = 7737
SHARMA_MAX = [0.33, 0.51, 0.80, 1.02, 1.26]
SHARMA_MIN = [0.45, 0.61, 0.93, 1.08]
TOL_GATE = 0.011
MIN_N = 30
B = {"t1": 999, "t2": 999, "t3": 199, "k4": 199, "sim": 199}
N_SIM = 100
SIZES = (50, 200, 800)
CONFIGS = (("gauss", False), ("lognormal", False), ("mix50", True), ("mix80", True))
ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10")
PRIORS = {"P1": 0.85, "P2": 0.85, "P3": 0.35, "P4": 0.35, "P5": 0.40, "P6": 0.50,
          "P7": 0.85, "P8": 0.70, "P9": 0.60, "P10": 0.70}
PRED_TEXT = {"P1": "Gates G1 and G2 both pass",
             "P2": "5R is Holm-rejected in T2 (RF)",
             "P3": "T1 label is TEMPO_MODES_FROM_RHYTHM_MIX",
             "P4": "T1 label is TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO",
             "P5": "T2 label is TEMPO_DISCRETE_BEYOND_KNOWN_TYPES",
             "P6": "T4 p < 0.05",
             "P7": "K1 rejection rate <= 0.10 in all six negative settings",
             "P8": "K2 power >= 0.8 for the 0.5/0.5 mixture at n = 200",
             "P9": "At least one T2-rejected rhythm is WITHIN_UNIT in T3",
             "P10": "The RL T1 label equals the RF T1 label"}
MIX, PART = "TEMPO_MODES_FROM_RHYTHM_MIX", "TEMPO_MODES_PARTLY_FROM_RHYTHM_MIX"
NEED, UNDER = "TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO", "T1_UNDERPOWERED"


# --------------------------------------------------------------------------
# independent re-implementation of TEMPO-PREREG.md sections 3 to 6
# --------------------------------------------------------------------------
def holm2(ps, alpha=ALPHA):
    """Holm step-down; ties broken by position."""
    idx = sorted(range(len(ps)), key=lambda i: (ps[i], i))
    out = [False] * len(ps)
    for j, i in enumerate(idx):
        if ps[i] > alpha / (len(ps) - j):
            break
        out[i] = True
    return out


def need(n):
    """Occupancy threshold max(10, ceil(5% of n)), in integers."""
    return max(10, -(-5 * n // 100))


def need_unit(n):
    """T3 'tempo types used' threshold max(5, ceil(10% of n))."""
    return max(5, -(-10 * n // 100))


def h2(counts):
    n = sum(counts)
    return 0.0 if n == 0 else -sum(c / n * math.log2(c / n) for c in counts if c)


def ratio(cells):
    """H(tempo | rhythm) / H(tempo) over a list of per-rhythm count vectors."""
    if not cells:
        return None
    n = sum(sum(c) for c in cells)
    if n == 0:
        return None
    tot = [sum(col) for col in zip(*cells)]
    ht = h2(tot)
    return None if ht <= 0 else sum(sum(c) / n * h2(c) for c in cells) / ht


def close(a, b, tol):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def p_ok(p, b):
    """p = (1 + k) / (1 + b) for an integer 0 <= k <= b."""
    k = p * (b + 1) - 1
    return abs(k - round(k)) < 1e-6 and 0 <= round(k) <= b


def lab_t1(f, fk):
    if f is None or fk is None:
        return None
    if fk < 0.2:
        return UNDER
    if f >= 0.5 * fk:
        return MIX
    return NEED if f < 0.05 else PART


def is_5r(row):
    return row["key"][0] == 5 and row["key"][1] == "5R"


def regate(gate):
    g1 = gate["n"] == N_EXPECTED
    g2 = close(gate["maxima"], SHARMA_MAX, TOL_GATE) and close(gate["minima"], SHARMA_MIN,
                                                               TOL_GATE)
    return g1, g2


def t3_label(units):
    rej = holm2([u["p"] for u in units])
    if any(rej):
        return "WITHIN_UNIT"
    if len(units) >= 2 and len({u["cells"].index(max(u["cells"])) for u in units}) >= 2:
        return "BETWEEN_UNITS"
    return "UNRESOLVED"


def regrade(r):
    g = {}
    gate = r.get("gate")
    g1, g2 = regate(gate) if gate else (None, None)
    g["P1"] = (g1 and g2) if gate else None
    rf = r.get("rf") or {}
    t2 = rf.get("t2")
    rej = holm2([x["p"] for x in t2]) if t2 is not None else None
    five = [i for i, x in enumerate(t2 or []) if is_5r(x)]
    g["P2"] = rej[five[0]] if five else None
    fk = (r.get("k4") or {}).get("f_all")
    l1 = lab_t1((rf.get("t1") or {}).get("f_all"), fk)
    g["P3"] = None if l1 is None else l1 == MIX
    g["P4"] = None if l1 is None else l1 == NEED
    if t2 is None:
        l2 = None
    elif not any(rej):
        l2 = "NO_WITHIN_RHYTHM_TEMPO_MODES"
    elif any(z and not x["known_variant"] for z, x in zip(rej, t2)):
        l2 = "TEMPO_DISCRETE_BEYOND_KNOWN_TYPES"
    else:
        l2 = "TEMPO_DISCRETE_ONLY_IN_KNOWN_TYPES"
    g["P5"] = None if l2 is None else l2 == "TEMPO_DISCRETE_BEYOND_KNOWN_TYPES"
    pc = (rf.get("t1") or {}).get("p_c")
    g["P6"] = None if pc is None else pc < ALPHA
    l4 = None if pc is None else ("MORE_COMBINATIONS_THAN_CUTTING" if pc < ALPHA
                                  else "COMBINATIONS_MATCHED_BY_CUTTING")
    cal = r.get("calibration") or []
    neg = [c for c in cal if c["config"] in ("gauss", "lognormal") and c["rate"] is not None]
    g["P7"] = all(c["rate"] <= 0.10 for c in neg) if len(neg) == 6 else None
    pw = [c for c in cal if c["config"] == "mix50" and c["n"] == 200 and c["rate"] is not None]
    g["P8"] = pw[0]["rate"] >= 0.8 if pw else None
    t3 = rf.get("t3") or []
    l3 = [t3_label(x["units"]) for x in t3]
    g["P9"] = ("WITHIN_UNIT" in l3) if t3 else None
    lr = lab_t1(((r.get("rl") or {}).get("t1") or {}).get("f_all"), fk)
    g["P10"] = (l1 == lr) if (l1 and lr) else None
    graded = [k for k in ORDER if g[k] is not None]
    brier = (sum((PRIORS[k] - (1.0 if g[k] else 0.0)) ** 2 for k in graded) / len(graded)
             if graded else None)
    return {"g": g, "graded": graded, "brier": brier, "g1": g1, "g2": g2,
            "exploratory": not (g1 and g2), "t2_reject": rej,
            "labels": {"T1": l1, "T1_rl": lr, "T2": l2, "T4": l4, "T3": l3}}


# --------------------------------------------------------------------------
# internal consistency of one rhythm scheme (RF or RL) and of the whole output
# --------------------------------------------------------------------------
def scheme_problems(s, gate, n_sample, tag, with_t3):
    bad = []
    rh = s["rhythms"]
    if s["n_assigned"] + s["n_other"] != n_sample:
        bad.append(tag + " assigned + other != sample")
    if sum(x["n"] for x in rh) != s["n_assigned"]:
        bad.append(tag + " rhythm sizes do not sum to n_assigned")
    keys = [tuple(x["key"]) for x in rh]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        bad.append(tag + " rhythms not in sorted key order")
    an = [x for x in rh if x["n"] >= MIN_N]
    if [x["analysable"] for x in rh] != [x["n"] >= MIN_N for x in rh]:
        bad.append(tag + " analysable flags")
    if (s["n_rhythms"], s["n_analysable"]) != (len(rh), len(an)):
        bad.append(tag + " rhythm counts")
    for x in rh:
        if sum(x["cells"]) != x["n"] or len(x["cells"]) != len(gate["cuts_used"]) + 1:
            bad.append(tag + " cells of " + x["name"])
        if x["occupied"] != sum(1 for c in x["cells"] if c >= need(x["n"])):
            bad.append(tag + " occupied of " + x["name"])
    c_obs = sum(x["occupied"] for x in an)
    if s["c_obs"] != c_obs or s["t1"].get("c_obs") != c_obs:
        bad.append(tag + " C_obs")
    ro = ratio([x["cells"] for x in an])
    if (ro is None) != (s["ratio_obs"] is None) or (ro is not None and
                                                     abs(ro - s["ratio_obs"]) > 1e-9):
        bad.append(tag + " entropy ratio")
    t2 = s["t2"]
    if [x["name"] for x in t2] != [x["name"] for x in an]:
        bad.append(tag + " T2 rows are not the analysable rhythms")
    for x, z, a in zip(t2, holm2([x["p"] for x in t2]), an):
        if x["B"] != B["t2"] or not p_ok(x["p"], x["B"]) or \
                abs(x["p"] - (1 + x["exceed"]) / (x["B"] + 1)) > 1e-12:
            bad.append(tag + " T2 p of " + x["name"])
        if x["holm_reject"] != z:
            bad.append(tag + " T2 Holm of " + x["name"])
        if x["n"] + x["n_trimmed_out"] != x["n_all"] or x["n_all"] != a["n"]:
            bad.append(tag + " T2 sizes of " + x["name"])
        if x["known_variant"] != a["known_variant"]:
            bad.append(tag + " T2 known flag of " + x["name"])
    t1 = s["t1"]
    if t1["B"] != B["t1"] or not p_ok(t1["p_c"], t1["B"]):
        bad.append(tag + " T1 B or p_c")
    if t1["real_maxima"] != gate["maxima"] or len(t1["mode_hit_rate"]) != len(gate["maxima"]):
        bad.append(tag + " T1 real maxima")
    if any(h < t1["f_all"] - 1e-12 for h in t1["mode_hit_rate"]) or not 0 <= t1["f_all"] <= 1:
        bad.append(tag + " T1 f_all above a per-mode rate")
    if not t1["null_c_min"] <= t1["null_c_mean"] <= t1["null_c_max"]:
        bad.append(tag + " T1 null C range")
    if with_t3:
        rejected = [x for x, z in zip(t2, holm2([x["p"] for x in t2])) if z]
        t3 = s.get("t3", [])
        if [x["name"] for x in t3] != [x["name"] for x in rejected]:
            bad.append(tag + " T3 rhythms are not the T2-rejected ones")
        for e, x in zip(t3, rejected):
            for u in e["units"]:
                if u["n"] < MIN_N or sum(u["cells"]) != u["n"]:
                    bad.append(tag + " T3 unit size " + e["name"] + "/" + u["unit"])
                if u["B"] != B["t3"] or abs(u["p"] - (1 + u["exceed"]) / (u["B"] + 1)) > 1e-12:
                    bad.append(tag + " T3 p " + e["name"] + "/" + u["unit"])
                if u["modal_tempo"] != u["cells"].index(max(u["cells"])):
                    bad.append(tag + " T3 modal tempo " + e["name"] + "/" + u["unit"])
                if u["tempo_types_used"] != sum(1 for c in u["cells"] if c >= need_unit(u["n"])):
                    bad.append(tag + " T3 types used " + e["name"] + "/" + u["unit"])
            for u, z in zip(e["units"], holm2([u["p"] for u in e["units"]])):
                if u["holm_reject"] != z:
                    bad.append(tag + " T3 Holm " + e["name"] + "/" + u["unit"])
            top = e["top_unit_share"] * x["n"]
            if abs(top - round(top)) > 1e-6 or round(top) < max([u["n"] for u in e["units"]]
                                                                  or [0]):
                bad.append(tag + " T3 top unit share " + e["name"])
            if e["label"] != t3_label(e["units"]):
                bad.append(tag + " T3 label " + e["name"])
    return bad


def problems(r):
    bad = []
    if r.get("status") != "ok" or r.get("version") != VERSION:
        bad.append("status or version")
    if not r.get("registration", {}).get("found"):
        bad.append("registration")
    c = r.get("config", {})
    want = {"bw": 0.035, "lo": 0.1, "hi": 1.75, "min_n": MIN_N, "tol_mode": 0.03,
            "tol_gate": TOL_GATE, "alpha": ALPHA, "seed": 20261119, "b_t1": B["t1"],
            "b_t2": B["t2"], "b_t3": B["t3"], "b_k4": B["k4"], "n_sim": N_SIM,
            "b_sim": B["sim"], "sizes": list(SIZES)}
    for k, v in want.items():
        if c.get(k) != v:
            bad.append("config " + k)
    if DATA_SHA not in c.get("data_url", ""):
        bad.append("data url not pinned")
    d = r.get("data", {})
    gate = r["gate"]
    if len(d.get("sha256", "")) != 64 or d.get("sample") != gate["n"]:
        bad.append("data record")
    if sum(gate["pooled_cells"]) != gate["n"]:
        bad.append("pooled cells")
    cuts = gate["minima"] if len(gate["minima"]) == 4 else SHARMA_MIN
    if gate["cuts_used"] != cuts:
        bad.append("cuts used")
    g1, g2 = regate(gate)
    if (gate["g1"], gate["g2"]) != (g1, g2):
        bad.append("gate flags")
    for x in r.get("centroids", []):
        kv = sum(1 for v in x["labels"].values() if v >= 5) >= 2
        if x["known_variant"] != kv:
            bad.append("known variant of centroid %s" % x["key"])
    known = {tuple(x["key"]) for x in r.get("centroids", []) if x["known_variant"]}
    for x in r["rf"]["rhythms"]:
        if x["known_variant"] != (tuple(x["key"]) in known):
            bad.append("RF known flag of " + x["name"])
    bad += scheme_problems(r["rf"], gate, gate["n"], "RF", True)
    bad += scheme_problems(r["rl"], gate, gate["n"], "RL", False)
    k4 = r["k4"]
    if k4["B"] != B["k4"] or not 0 <= k4["f_all"] <= 1:
        bad.append("K4")
    cal = r["calibration"]
    if [(x["config"], x["bimodal"], x["n"]) for x in cal] != \
            [(c_, b_, n_) for c_, b_ in CONFIGS for n_ in SIZES]:
        bad.append("calibration grid")
    for x in cal:
        if not 0 <= x["rejections"] <= x["sims"] <= N_SIM:
            bad.append("calibration counts %s %d" % (x["config"], x["n"]))
        if (x["rate"] is None) != (x["sims"] == 0) or \
                (x["sims"] and abs(x["rate"] - x["rejections"] / x["sims"]) > 1e-12):
            bad.append("calibration rate %s %d" % (x["config"], x["n"]))
    return bad


# --------------------------------------------------------------------------
# formats fixed before the result exists (RESULTS-TEMPO.md must contain these lines)
# --------------------------------------------------------------------------
def fl(v, f="%.2f"):
    return ", ".join(f % x for x in v) if v else "none"


def yn(b):
    return "**yes**" if b else "**no**"


def power_note(n, cal):
    """K2 power at the largest calibrated size not above n (0.5/0.5 mixture)."""
    ok = [c for c in cal if c["config"] == "mix50" and c["n"] <= n and c["rate"] is not None]
    if not ok:
        return "low"
    best = max(ok, key=lambda c: c["n"])
    return "ok" if best["rate"] >= 0.8 else "low"


def t2_row(tag, x, cal):
    """| scheme | rhythm | codas | outliers | h_crit (s) | p | Holm reject | known 2016 split |
    power if not rejected | KDE maxima at 0.035 s |"""
    return "| {} | {} | {:,} | {} | {:.4f} | {:.3f} | {} | {} | {} | {} |".format(
        tag, x["name"], x["n_all"], x["n_trimmed_out"], x["h_crit"], x["p"],
        "yes" if x["holm_reject"] else "no", "yes" if x["known_variant"] else "no",
        "-" if x["holm_reject"] else power_note(x["n"], cal), fl(x["modes_at_bw"]))


def t3_row(e, u):
    """| rhythm | unit | codas | p | Holm reject | modal tempo type | tempo types used |"""
    return "| {} | {} | {} | {:.3f} | {} | {} | {} |".format(
        e["name"], u["unit"], u["n"], u["p"], "yes" if u["holm_reject"] else "no",
        u["modal_tempo"], u["tempo_types_used"])


def cal_row(c):
    """| setting | n | rejections | rate |"""
    return "| {} | {} | {} of {} | {} |".format(
        c["config"], c["n"], c["rejections"], c["sims"],
        "n/a" if c["rate"] is None else "%.2f" % c["rate"])


def pred_end(k, v):
    return "| {:.2f} | **{}** |".format(
        PRIORS[k], "not graded" if v is None else ("true" if v else "false"))


def required_strings(r, rg):
    gate = r["gate"]
    rf, rl, k4 = r["rf"], r["rl"], r["k4"]
    lab = rg["labels"]
    s = ["Gate G1: n = {:,} (paper 7,737): {}".format(
            gate["n"], "**pass**" if rg["g1"] else "**fail**"),
         "Gate G2: maxima {}; minima {}: {}".format(
            fl(gate["maxima"]), fl(gate["minima"]), "**pass**" if rg["g2"] else "**fail**"),
         "Tempo cut points used: " + fl(gate["cuts_used"]),
         "Exploratory (a gate failed): " + yn(rg["exploratory"])]
    for tag, x in (("RF", rf), ("RL", rl)):
        s.append("{} rhythms: {} found, {} analysable (>= 30 codas); {:,} codas assigned, {:,} "
                 "without a rhythm".format(tag, x["n_rhythms"], x["n_analysable"],
                                           x["n_assigned"], x["n_other"]))
        for row in x["t2"]:
            s.append(t2_row(tag, row, r["calibration"]))
        s.append("T2 ({}): {} of {} rhythms Holm-rejected".format(
            tag, sum(1 for row in x["t2"] if row["holm_reject"]), len(x["t2"])))
        t1 = x["t1"]
        s.append("T1 ({}): f_all **{:.3f}**; per-mode hit rates {}; null mean number of maxima "
                 "{:.2f}".format(tag, t1["f_all"], fl(t1["mode_hit_rate"], "%.3f"),
                                 t1["null_n_maxima_mean"]))
        s.append("T4 ({}): C_obs {}; null mean {:.1f} (range {} to {}); p = {:.3f}".format(
            tag, x["c_obs"], t1["null_c_mean"], t1["null_c_min"], t1["null_c_max"], t1["p_c"]))
        s.append("H(tempo | rhythm) / H(tempo) ({}): real {}; null mean {:.3f}".format(
            tag, "n/a" if x["ratio_obs"] is None else "%.3f" % x["ratio_obs"],
            t1["null_ratio_mean"]))
    s.append("K4 ceiling: f_K4 **{:.3f}** (pseudo-real maxima {})".format(
        k4["f_all"], fl(k4["pseudo_maxima"])))
    s.append("T1 label (RF): **`{}`**".format(lab["T1"]))
    s.append("T1 label (RL): **`{}`**".format(lab["T1_rl"]))
    s.append("T2 label (RF): **`{}`**".format(lab["T2"]))
    s.append("T4 label (RF): **`{}`**".format(lab["T4"]))
    for e in rf.get("t3", []):
        for u in e["units"]:
            s.append(t3_row(e, u))
        s.append("T3 {}: **`{}`** (largest unit's share {:.2f})".format(
            e["name"], t3_label(e["units"]), e["top_unit_share"]))
    for c in r["calibration"]:
        s.append(cal_row(c))
    ntrue = sum(1 for k in rg["graded"] if rg["g"][k])
    s.append("%d of %d graded predictions true" % (ntrue, len(rg["graded"])))
    if rg["graded"]:
        s.append("Brier score **%.3f**" % rg["brier"])
    return s


def render_md_lines(r, rg):
    """Every fixed line, prediction rows included, for writing RESULTS-TEMPO.md."""
    return required_strings(r, rg) + ["| %s | %s %s" % (k, PRED_TEXT[k], pred_end(k, rg["g"][k]))
                                      for k in ORDER]


def check_md(md, r, rg):
    missing = [x for x in required_strings(r, rg) if x not in md]
    lines = md.splitlines()
    for k in ORDER:
        hits = [ln for ln in lines if ln.startswith("| %s |" % k)]
        if len(hits) != 1 or not hits[0].rstrip().endswith(pred_end(k, rg["g"][k])):
            missing.append("prediction row " + k)
    return missing


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --------------------------------------------------------------------------
# toy output (hand-built; the expected values are worked out in the comments)
# --------------------------------------------------------------------------
def toy():
    rh = [{"key": [4, "4R"], "name": "4R", "n": 3, "analysable": False, "known_variant": True,
           "cells": [3, 0, 0, 0, 0], "occupied": 0},                  # need(3) = 10
          {"key": [5, "1+1+3"], "name": "1+1+3", "n": 40, "analysable": True,
           "known_variant": False, "cells": [0, 0, 0, 30, 10], "occupied": 2},   # need 10
          {"key": [5, "5R"], "name": "5R", "n": 100, "analysable": True, "known_variant": True,
           "cells": [50, 0, 0, 45, 5], "occupied": 2}]                # need(100) = 10
    t2 = [{"key": [5, "1+1+3"], "name": "1+1+3", "n": 40, "n_all": 40, "n_trimmed_out": 0,
           "h_crit": 0.05, "exceed": 499, "B": 999, "p": 0.5, "known_variant": False,
           "modes_at_bw": [1.0], "holm_reject": False},
          {"key": [5, "5R"], "name": "5R", "n": 98, "n_all": 100, "n_trimmed_out": 2,
           "h_crit": 0.2, "exceed": 0, "B": 999, "p": 0.001, "known_variant": True,
           "modes_at_bw": [0.33, 0.8], "holm_reject": True}]
    # Holm over (0.5, 0.001): 0.001 <= 0.025 rejects; 0.5 > 0.05 stops -> [False, True]
    t3 = [{"key": [5, "5R"], "name": "5R", "label": "BETWEEN_UNITS", "top_unit_share": 50 / 98,
           "units": [{"unit": "A", "n": 40, "cells": [30, 0, 0, 10, 0], "modal_tempo": 0,
                      "tempo_types_used": 2, "exceed": 39, "B": 199, "p": 0.2,
                      "h_crit": 0.1, "holm_reject": False},
                     {"unit": "B", "n": 50, "cells": [10, 0, 0, 40, 0], "modal_tempo": 3,
                      "tempo_types_used": 2, "exceed": 59, "B": 199, "p": 0.3,
                      "h_crit": 0.1, "holm_reject": False}]}]
    # T3: Holm over (0.2, 0.3) rejects nothing; modal tempo 0 vs 3 -> BETWEEN_UNITS
    rf = {"n_assigned": 143, "n_other": 7594, "n_rhythms": 3, "n_analysable": 2, "rhythms": rh,
          "c_obs": 4, "ratio_obs": ratio([[0, 0, 0, 30, 10], [50, 0, 0, 45, 5]]), "t2": t2,
          "t1": {"B": 999, "real_maxima": list(SHARMA_MAX),
                 "mode_hit_rate": [0.9, 0.8, 0.7, 0.65, 0.6], "f_all": 0.6,
                 "null_n_maxima_mean": 5.2, "null_share_exactly_5": 0.5, "null_c_mean": 3.1,
                 "null_c_max": 5, "null_c_min": 2, "null_ratio_mean": 0.8, "c_obs": 4,
                 "p_c": 0.2},
          "t3": t3}
    rl = copy.deepcopy(rf)
    del rl["t3"]
    rl["t1"]["f_all"] = 0.02
    cal = []
    for cfg, bim in CONFIGS:
        for n in SIZES:
            rej = 2 if not bim else (90 if (cfg, n) == ("mix50", 200) else 50)
            cal.append({"config": cfg, "bimodal": bim, "n": n, "sims": 100, "rejections": rej,
                        "rate": rej / 100})
    return {"version": VERSION, "status": "ok",
            "registration": {"found": True, "sha256": "0" * 64},
            "config": {"bw": 0.035, "lo": 0.1, "hi": 1.75, "min_n": 30, "tol_mode": 0.03,
                       "tol_gate": 0.011, "alpha": 0.05, "seed": 20261119, "b_t1": 999,
                       "b_t2": 999, "b_t3": 199, "b_k4": 199, "n_sim": 100, "b_sim": 199,
                       "sizes": [50, 200, 800],
                       "data_url": "https://x/" + DATA_SHA + "/data/DominicaCodas.csv"},
            "data": {"sha256": "a" * 64, "sample": 7737},
            "gate": {"g1": True, "g2": True, "n": 7737, "maxima": [0.33, 0.51, 0.8, 1.02, 1.26],
                     "minima": [0.45, 0.61, 0.93, 1.08], "cuts_used": [0.45, 0.61, 0.93, 1.08],
                     "pooled_cells": [1000, 2000, 3000, 1000, 737]},
            "centroids": [{"key": [4, "4R"], "labels": {"4R1": 9, "4R2": 5},
                           "known_variant": True},
                          {"key": [5, "1+1+3"], "labels": {"1+1+3": 40}, "known_variant": False},
                          {"key": [5, "5R"], "labels": {"5R1": 50, "5R3": 7, "5R2": 4},
                           "known_variant": True}],
            "rf": rf, "rl": rl,
            "k4": {"B": 199, "f_all": 0.8, "pseudo_maxima": [0.33, 0.8],
                   "mode_hit_rate": [0.9, 0.9]},
            "calibration": cal,
            "grade": {"labels": {"T1": MIX, "T1_rl": NEED,
                                 "T2": "TEMPO_DISCRETE_ONLY_IN_KNOWN_TYPES",
                                 "T4": "COMBINATIONS_MATCHED_BY_CUTTING",
                                 "T3": ["BETWEEN_UNITS"]},
                      "predictions": {"P1": True, "P2": True, "P3": True, "P4": False,
                                      "P5": False, "P6": False, "P7": True, "P8": True,
                                      "P9": False, "P10": False},
                      "n_scored": 10, "brier": 0.19625}}


class TestToy(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(holm2([0.01, 0.04, 0.03]), [True, False, False])
        self.assertEqual(holm2([0.01, 0.02, 0.03]), [True, True, True])
        self.assertEqual(holm2([]), [])
        self.assertEqual((need(3), need(200), need(201), need(1000)), (10, 10, 11, 50))
        self.assertEqual((need_unit(40), need_unit(51), need_unit(30)), (5, 6, 5))
        self.assertAlmostEqual(ratio([[10, 0], [0, 10]]), 0.0)
        self.assertAlmostEqual(ratio([[5, 5], [5, 5]]), 1.0)
        self.assertIsNone(ratio([]))
        self.assertIsNone(ratio([[4, 0], [6, 0]]))           # H(tempo) = 0
        self.assertTrue(p_ok(0.001, 999) and p_ok(1.0, 999) and p_ok(0.2, 199))
        self.assertFalse(p_ok(0.0015, 999))

    def test_t1_label_boundaries(self):
        self.assertEqual(lab_t1(0.9, 0.19), UNDER)
        self.assertEqual(lab_t1(0.1, 0.2), MIX)                 # 0.1 >= 0.5 * 0.2: MIX
        self.assertEqual(lab_t1(0.4, 0.8), MIX)
        self.assertEqual(lab_t1(0.05, 0.8), PART)               # 0.05 is not < 0.05
        self.assertEqual(lab_t1(0.049, 0.8), NEED)
        self.assertIsNone(lab_t1(None, 0.8))

    def test_toy_regrade(self):
        r = toy()
        rg = regrade(r)
        # P1 gates; P2 5R rejected; T1 0.6 >= 0.4 -> MIX (P3 true, P4 false); T2 rejects only
        # 5R (known) -> ONLY_IN_KNOWN (P5 false); p_c 0.2 (P6 false); negatives 0.02 (P7 true);
        # mix50 n 200 rate 0.9 (P8 true); T3 BETWEEN_UNITS (P9 false); RL 0.02 -> NEED != MIX.
        self.assertEqual(rg["g"], r["grade"]["predictions"])
        self.assertEqual(rg["labels"]["T2"], "TEMPO_DISCRETE_ONLY_IN_KNOWN_TYPES")
        self.assertEqual(rg["labels"]["T3"], ["BETWEEN_UNITS"])
        # (.15^2 + .15^2 + .65^2 + .35^2 + .4^2 + .5^2 + .15^2 + .3^2 + .6^2 + .7^2) / 10
        self.assertAlmostEqual(rg["brier"], 0.19625, places=12)
        self.assertEqual(problems(r), [])

    def test_toy_problems_detected(self):
        r = toy()
        r["rf"]["t2"][1]["holm_reject"] = False
        self.assertIn("RF T2 Holm of 5R", problems(r))
        r = toy()
        r["rf"]["rhythms"][2]["occupied"] = 3
        self.assertIn("RF occupied of 5R", problems(r))
        r = toy()
        r["rf"]["t1"]["f_all"] = 0.7
        self.assertIn("RF T1 f_all above a per-mode rate", problems(r))
        r = toy()
        r["rf"]["t3"][0]["units"][1]["modal_tempo"] = 0
        self.assertIn("RF T3 modal tempo 5R/B", problems(r))
        r = toy()
        r["gate"]["maxima"] = [0.33, 0.51, 0.8, 1.02]
        r["rf"]["t1"]["real_maxima"] = r["gate"]["maxima"]
        r["rl"]["t1"]["real_maxima"] = r["gate"]["maxima"]
        self.assertIn("gate flags", problems(r))
        self.assertFalse(regrade(r)["g"]["P1"])
        r = toy()
        r["calibration"][0]["rate"] = 0.5
        self.assertIn("calibration rate gauss 50", problems(r))

    def test_beyond_known_and_missing(self):
        r = toy()
        r["rf"]["t2"][0].update({"p": 0.002, "exceed": 1})
        # Holm over (0.002, 0.001): 0.001 <= 0.025, then 0.002 <= 0.05 -> both rejected;
        # 1+1+3 is not a known 2016 split -> BEYOND_KNOWN_TYPES
        rg = regrade(r)
        self.assertEqual(rg["t2_reject"], [True, True])
        self.assertEqual(rg["labels"]["T2"], "TEMPO_DISCRETE_BEYOND_KNOWN_TYPES")
        self.assertTrue(rg["g"]["P5"])
        rg0 = regrade({})
        self.assertEqual(rg0["graded"], [])
        self.assertIsNone(rg0["brier"])

    def test_render_and_check(self):
        r = toy()
        rg = regrade(r)
        lines = render_md_lines(r, rg)
        self.assertIn("| P1 | Gates G1 and G2 both pass | 0.85 | **true** |", lines)
        self.assertIn("| P9 | At least one T2-rejected rhythm is WITHIN_UNIT in T3 | 0.60 | "
                      "**false** |", lines)
        self.assertIn("Gate G1: n = 7,737 (paper 7,737): **pass**", lines)
        self.assertIn("| RF | 5R | 100 | 2 | 0.2000 | 0.001 | yes | yes | - | 0.33, 0.80 |",
                      lines)
        # 1+1+3 not rejected, n 40 < 50: no calibrated size at or below it -> power "low"
        self.assertIn("| RF | 1+1+3 | 40 | 0 | 0.0500 | 0.500 | no | no | low | 1.00 |", lines)
        self.assertIn("| 5R | B | 50 | 0.300 | no | 3 | 2 |", lines)
        self.assertIn("T3 5R: **`BETWEEN_UNITS`** (largest unit's share 0.51)", lines)
        self.assertIn("| mix50 | 200 | 90 of 100 | 0.90 |", lines)
        self.assertIn("5 of 10 graded predictions true", lines)
        self.assertTrue(any(ln.startswith("Brier score **0.19") for ln in lines))
        md = "\n".join(lines)
        self.assertEqual(check_md(md, r, rg), [])
        self.assertIn("prediction row P3", check_md(md.replace("| P3 |", "| P 3 |"), r, rg))
        self.assertTrue(check_md(md.replace("Brier score", "Brier"), r, rg))


@unittest.skipUnless(HAVE, "results/tempo/tempo_results.json not published yet")
class TestTempoResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RES, encoding="utf-8") as f:
            cls.r = json.load(f)
        cls.rg = regrade(cls.r)

    def test_registration(self):
        if os.path.exists(PREREG):
            self.assertEqual(self.r["registration"]["sha256"], sha256_file(PREREG))

    def test_consistency(self):
        self.assertEqual(problems(self.r), [])

    def test_job_grade_matches_regrade(self):
        g = self.r["grade"]
        self.assertEqual(g["predictions"], self.rg["g"])
        self.assertEqual(g["labels"]["T1"], self.rg["labels"]["T1"])
        self.assertEqual(g["labels"]["T1_rl"], self.rg["labels"]["T1_rl"])
        self.assertEqual(g["labels"]["T2"], self.rg["labels"]["T2"])
        self.assertEqual(g["labels"]["T4"], self.rg["labels"]["T4"])
        self.assertEqual(g["labels"]["T3"], self.rg["labels"]["T3"])
        self.assertEqual(g["n_scored"], len(self.rg["graded"]))
        if self.rg["brier"] is not None:
            self.assertAlmostEqual(g["brier"], self.rg["brier"], places=12)

    def test_results_md(self):
        self.assertTrue(os.path.exists(MD), "RESULTS-TEMPO.md missing")
        with open(MD, encoding="utf-8") as f:
            md = f.read()
        self.assertEqual(check_md(md, self.r, self.rg), [])


if __name__ == "__main__":
    unittest.main()
