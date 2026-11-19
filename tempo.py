#!/usr/bin/env python3
# coda-tempo-test: are the five "tempo types" of the sperm whale coda alphabet (Sharma et al.
# 2024, Nature Communications 15:3617) a discrete axis of their own, or what mixing rhythm
# types that each have one characteristic duration already gives? Registered in
# TEMPO-PREREG.md before this job runs; the job waits until that file is public.
# Data: DominicaCodas.csv from github.com/pratyushasharma/sw-combinatoriality at a fixed
# commit (CC BY 4.0, Zenodo 10.5281/zenodo.10817697); downloaded by the job, not redistributed.
# Pure standard library. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import argparse
import bisect
import csv
import hashlib
import io
import json
import math
import os
import random
import re
import sys
import time
import urllib.request

VERSION = "tempo-1.0"
DATA_SHA = "7228c8eed2cc27ddd23b74c51aeccec9d762389e"
DATA_URL = ("https://raw.githubusercontent.com/pratyushasharma/sw-combinatoriality/"
            + DATA_SHA + "/data/DominicaCodas.csv")
PREREG_URL = ("https://raw.githubusercontent.com/munimtechnologies/coda-tempo-test/main/"
              "TEMPO-PREREG.md")

BW = 0.035                                   # Sharma et al. notebook 2-tempo, cell 19
GRID = [round(0.10 + 0.01 * k, 2) for k in range(166)]   # 0.10 .. 1.75
SHARMA_MAX = [0.33, 0.51, 0.80, 1.02, 1.26]  # printed in that notebook, cell 20
SHARMA_MIN = [0.45, 0.61, 0.93, 1.08]
LO, HI = 0.1, 1.75                           # cell 16 filter (strict)
N_EXPECTED = 7737                            # cell 16 output
TOL_GATE = 0.011
TOL_MODE = 0.03
MIN_N = 30
DELTA = 0.001
ALPHA = 0.05
SEED = 20261119
B_T1 = 999
B_T2 = 999
B_T3 = 199
B_K4 = 199
N_SIM = 100
B_SIM = 199
SIZES = (50, 200, 800)
SIM_CONFIGS = (("gauss", False), ("lognormal", False), ("mix50", True), ("mix80", True))
PRIORS = {"P1": 0.85, "P2": 0.85, "P3": 0.35, "P4": 0.35, "P5": 0.40, "P6": 0.50,
          "P7": 0.85, "P8": 0.70, "P9": 0.60, "P10": 0.70}
TEMPO_RE = re.compile(r"^(\d+[RDi]|1\+3)([1-9])$")


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "coda-tempo-test (mv2@munimtech.com)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_rows(text):
    rows = []
    header = None
    idx = {}
    for rec in csv.reader(io.StringIO(text)):
        if not rec:
            continue
        if header is None:
            header = [h.replace(chr(0xFEFF), "").strip() for h in rec]
            idx = {h: i for i, h in enumerate(header)}
            continue

        def get(name):
            i = idx.get(name)
            return rec[i].strip() if i is not None and i < len(rec) else ""
        try:
            n = int(float(get("nClicks")))
            dur = float(get("Duration"))
            icis = [float(get("ICI%d" % k) or 0) for k in range(1, 10)]
        except ValueError:
            continue
        rows.append({"id": get("codaNUM2018"), "n": n, "dur": dur, "icis": icis,
                     "type": get("CodaType"), "clan": get("Clan"), "unit": get("Unit"),
                     "idn": get("IDN")})
    return rows


def select_sample(rows):
    return [r for r in rows if r["clan"] == "EC1" and LO < r["dur"] < HI]


def merged(t):
    m = TEMPO_RE.match(t)
    return m.group(1) if m else t


def labelled(t):
    return bool(t) and "noise" not in t.lower()


def norm_ici(row):
    n = row["n"]
    if n < 3 or n > 10:
        return None
    iv = row["icis"][:n - 1]
    if len(iv) != n - 1 or any(x <= 0 for x in iv):
        return None
    s = sum(iv)
    return [x / s for x in iv]


def build_centroids(sample, min_count=5):
    acc = {}
    labels = {}
    for r in sample:
        if not labelled(r["type"]):
            continue
        v = norm_ici(r)
        if v is None:
            continue
        key = (r["n"], merged(r["type"]))
        a = acc.setdefault(key, [0, [0.0] * len(v)])
        a[0] += 1
        for i, x in enumerate(v):
            a[1][i] += x
        lab = labels.setdefault(key, {})
        lab[r["type"]] = lab.get(r["type"], 0) + 1
    cents = {k: [s / a[0] for s in a[1]] for k, a in acc.items() if a[0] >= min_count}
    known = sorted(k for k in cents
                   if sum(1 for c in labels[k].values() if c >= min_count) >= 2)
    return cents, {k: labels[k] for k in cents}, known


def assign_rf(row, cents, keys=None):
    """Tempo-free rhythm: nearest centroid in normalised-ICI space, same click count."""
    v = norm_ici(row)
    if v is None:
        return None
    best, bd = None, None
    for key in (keys if keys is not None else sorted(cents)):
        if key[0] != row["n"]:
            continue
        d = sum((a - b) ** 2 for a, b in zip(v, cents[key]))
        if bd is None or d < bd:
            best, bd = key, d
    return best


def assign_rl(row):
    """Gero et al. label with the tempo index stripped (labelled codas only)."""
    if labelled(row["type"]) and 3 <= row["n"] <= 10:
        return (row["n"], merged(row["type"]))
    return None


def key_names(keys):
    by_m = {}
    for k in keys:
        by_m.setdefault(k[1], []).append(k)
    return {k: (k[1] if len(by_m[k[1]]) == 1 else "%s/n%d" % (k[1], k[0])) for k in keys}


def group(sample, assign):
    by, other = {}, []
    for r in sample:
        k = assign(r)
        if k is None:
            other.append(r["dur"])
        else:
            by.setdefault(k, []).append(r)
    return by, other


# --------------------------------------------------------------------------
# densities, modes, Silverman's test
# --------------------------------------------------------------------------
def kde_grid_exact(xs, h, grid):
    c = 1.0 / (len(xs) * h * math.sqrt(2.0 * math.pi))
    out = []
    for g in grid:
        s = 0.0
        for x in xs:
            z = (g - x) / h
            if -8.0 < z < 8.0:
                s += math.exp(-0.5 * z * z)
        out.append(s * c)
    return out


def kde_grid_binned(xs, h, grid, delta=DELTA):
    cnt = {}
    for x in xs:
        j = int(math.floor(x / delta + 0.5))
        cnt[j] = cnt.get(j, 0) + 1
    items = sorted(cnt.items())
    pos = [j * delta for j, _ in items]
    ws = [w for _, w in items]
    c = 1.0 / (len(xs) * h * math.sqrt(2.0 * math.pi))
    out = []
    for g in grid:
        a = bisect.bisect_left(pos, g - 8.0 * h)
        b = bisect.bisect_right(pos, g + 8.0 * h)
        s = 0.0
        for i in range(a, b):
            z = (g - pos[i]) / h
            s += ws[i] * math.exp(-0.5 * z * z)
        out.append(s * c)
    return out


def extrema(vals, grid):
    mx, mn = [], []
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i - 1] and vals[i] > vals[i + 1]:
            mx.append(grid[i])
        elif vals[i] < vals[i - 1] and vals[i] < vals[i + 1]:
            mn.append(grid[i])
    return mx, mn


def n_modes(xs, h):
    """Number of modes of the Gaussian KDE of xs at bandwidth h (bins of max(1 ms, h/20))."""
    delta = max(DELTA, h / 20.0)
    cnt = {}
    for x in xs:
        j = int(math.floor(x / delta + 0.5))
        cnt[j] = cnt.get(j, 0) + 1
    w = int(math.ceil(5.0 * h / delta))
    half = [math.exp(-0.5 * (k * delta / h) ** 2) for k in range(w + 1)]
    kern = half[:0:-1] + half
    js = sorted(cnt)
    lo = js[0] - w
    d = [0.0] * (js[-1] + w - lo + 1)
    for j in js:
        c = cnt[j]
        s = j - js[0]
        d[s:s + 2 * w + 1] = [u + c * v for u, v in zip(d[s:s + 2 * w + 1], kern)]
    m = 0
    for i in range(1, len(d) - 1):
        if d[i] > d[i - 1] and d[i] >= d[i + 1]:
            m += 1
    return m


def h_crit(xs, k, lo=1e-3, hi=1.0, iters=24):
    if n_modes(xs, lo) <= k:
        return lo
    if n_modes(xs, hi) > k:
        return hi
    a, b = math.log(lo), math.log(hi)
    for _ in range(iters):
        mid = 0.5 * (a + b)
        if n_modes(xs, math.exp(mid)) <= k:
            b = mid
        else:
            a = mid
    return math.exp(b)


def smooth_plan(xs, h):
    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    scale = 1.0 / math.sqrt(1.0 + h * h / var) if var > 0 else 1.0
    return {"keep": list(xs), "h": h, "mean": mean, "scale": scale}


def smooth_draw(p, rng):
    keep = p["keep"]
    m = len(keep)
    mean, h, s = p["mean"], p["h"], p["scale"]
    return [mean + (keep[int(rng.random() * m)] - mean + h * rng.gauss(0.0, 1.0)) * s
            for _ in range(m)]


def silverman(xs, k, B, rng):
    """Silverman (1981) test of H0: at most k modes; smoothed bootstrap at h_crit."""
    h = h_crit(xs, k)
    p = smooth_plan(xs, h)
    exceed = 0
    for _ in range(B):
        if n_modes(smooth_draw(p, rng), h) > k:
            exceed += 1
    return {"n": len(xs), "h_crit": h, "exceed": exceed, "B": B, "p": (1 + exceed) / (B + 1)}


def quantile(s, q):
    pos = q * (len(s) - 1)
    i = int(math.floor(pos))
    f = pos - i
    if i + 1 < len(s):
        return s[i] * (1 - f) + s[i + 1] * f
    return s[i]


def trim(xs):
    s = sorted(xs)
    q1, q3 = quantile(s, 0.25), quantile(s, 0.75)
    lo, hi = q1 - 3 * (q3 - q1), q3 + 3 * (q3 - q1)
    keep = [x for x in xs if lo <= x <= hi]
    out = [x for x in xs if not (lo <= x <= hi)]
    return keep, out, lo, hi


def holm(ps, alpha):
    m = len(ps)
    order = sorted(range(m), key=lambda i: (ps[i], i))
    rej = [False] * m
    for rank, i in enumerate(order):
        if ps[i] <= alpha / (m - rank):
            rej[i] = True
        else:
            break
    return rej


# --------------------------------------------------------------------------
# tempo cells
# --------------------------------------------------------------------------
def tempo_type(d, cuts):
    return sum(1 for c in cuts if d > c)


def cell_counts(durs, cuts):
    c = [0] * (len(cuts) + 1)
    for d in durs:
        c[tempo_type(d, cuts)] += 1
    return c


def occupied(counts, n, floor=10, pct=5):
    thr = max(floor, (pct * n + 99) // 100)
    return sum(1 for c in counts if c >= thr)


def entropy(counts):
    n = sum(counts)
    if n == 0:
        return 0.0
    return -sum(c / n * math.log2(c / n) for c in counts if c > 0)


def cond_entropy_ratio(cells):
    if not cells:
        return None
    width = len(next(iter(cells.values())))
    tot = [0] * width
    big_n = 0
    for counts in cells.values():
        big_n += sum(counts)
        for i, c in enumerate(counts):
            tot[i] += c
    if big_n == 0:
        return None
    hc = sum(sum(c) / big_n * entropy(c) for c in cells.values())
    ht = entropy(tot)
    return hc / ht if ht > 0 else None


# --------------------------------------------------------------------------
# tests T1-T4 and calibration
# --------------------------------------------------------------------------
def build_null(by, min_n=MIN_N):
    plan = {}
    for k in sorted(by):
        xs = [r["dur"] for r in by[k]]
        if len(xs) >= min_n:
            keep, out, _, _ = trim(xs)
            p = smooth_plan(keep, h_crit(keep, 1))
            p["out"] = out
            plan[k] = ("smooth", p, len(xs))
        else:
            plan[k] = ("fixed", xs, len(xs))
    return plan


def draw_surrogate(plan, rng):
    res = {}
    for k in sorted(plan):
        kind, p, _ = plan[k]
        res[k] = list(p) if kind == "fixed" else smooth_draw(p, rng) + list(p["out"])
    return res


def run_t1(by, other, real_max, cuts, analysable, B, seed, c_obs=None):
    plan = build_null(by)
    rng = random.Random(seed)
    hits = [0] * len(real_max)
    all_hit = 0
    nmax, cs, ratios = [], [], []
    for _ in range(B):
        sur = draw_surrogate(plan, rng)
        pooled = list(other)
        for k in sorted(sur):
            pooled.extend(sur[k])
        mx, _ = extrema(kde_grid_binned(pooled, BW, GRID), GRID)
        ok = [any(abs(m - r) <= TOL_MODE + 1e-9 for m in mx) for r in real_max]
        for i, o in enumerate(ok):
            hits[i] += 1 if o else 0
        all_hit += 1 if all(ok) else 0
        nmax.append(len(mx))
        cells = {k: cell_counts(sur[k], cuts) for k in analysable}
        cs.append(sum(occupied(cells[k], len(sur[k])) for k in analysable))
        ratios.append(cond_entropy_ratio(cells))
    res = {"B": B, "real_maxima": list(real_max), "mode_hit_rate": [h / B for h in hits],
           "f_all": all_hit / B, "null_n_maxima_mean": sum(nmax) / B,
           "null_share_exactly_5": sum(1 for x in nmax if x == 5) / B,
           "null_c_mean": sum(cs) / B, "null_c_max": max(cs), "null_c_min": min(cs),
           "null_ratio_mean": (sum(r for r in ratios if r is not None) /
                               max(1, sum(1 for r in ratios if r is not None)))}
    if c_obs is not None:
        res["c_obs"] = c_obs
        res["p_c"] = (1 + sum(1 for c in cs if c >= c_obs)) / (B + 1)
    return res


def run_t2(by, analysable, B, seed, names, known):
    rows = []
    for i, k in enumerate(analysable):
        xs = [r["dur"] for r in by[k]]
        keep, out, _, _ = trim(xs)
        t = silverman(keep, 1, B, random.Random(seed + 1000 * (i + 1)))
        mx, _ = extrema(kde_grid_binned(keep, BW, GRID), GRID)
        t.update({"key": [k[0], k[1]], "name": names[k], "n_all": len(xs),
                  "n_trimmed_out": len(out), "known_variant": k in known, "modes_at_bw": mx})
        rows.append(t)
    for r, z in zip(rows, holm([r["p"] for r in rows], ALPHA)):
        r["holm_reject"] = z
    return rows


def run_t3(by, rejected, cuts, B, seed, names):
    res = []
    for i, k in enumerate(rejected):
        _, _, lo, hi = trim([r["dur"] for r in by[k]])
        units = {}
        for r in by[k]:
            if lo <= r["dur"] <= hi:
                units.setdefault(r["unit"] or "?", []).append(r["dur"])
        total = sum(len(v) for v in units.values())
        rows = []
        for j, u in enumerate(sorted(units)):
            xs = units[u]
            if len(xs) < MIN_N:
                continue
            t = silverman(xs, 1, B, random.Random(seed + 100000 * (i + 1) + 100 * (j + 1)))
            cc = cell_counts(xs, cuts)
            t.update({"unit": u, "cells": cc, "tempo_types_used": occupied(cc, len(xs), 5, 10),
                      "modal_tempo": cc.index(max(cc))})
            rows.append(t)
        for r, z in zip(rows, holm([r["p"] for r in rows], ALPHA)):
            r["holm_reject"] = z
        if any(r["holm_reject"] for r in rows):
            label = "WITHIN_UNIT"
        elif len(rows) >= 2 and len(set(r["modal_tempo"] for r in rows)) >= 2:
            label = "BETWEEN_UNITS"
        else:
            label = "UNRESOLVED"
        top = max((len(v) for v in units.values()), default=0)
        res.append({"key": [k[0], k[1]], "name": names[k], "units": rows, "label": label,
                    "top_unit_share": top / total if total else None})
    return res


def sim_draw(cfg, n, rng):
    if cfg == "gauss":
        return [rng.gauss(0.42, 0.08) for _ in range(n)]
    if cfg == "lognormal":
        return [math.exp(math.log(0.4) + 0.25 * rng.gauss(0.0, 1.0)) for _ in range(n)]
    w = 0.5 if cfg == "mix50" else 0.8
    return [rng.gauss(0.33, 0.045) if rng.random() < w else rng.gauss(0.51, 0.045)
            for _ in range(n)]


def run_calib(nsim, B, seed, sizes, deadline):
    res = []
    for ci, (cfg, bimodal) in enumerate(SIM_CONFIGS):
        for n in sizes:
            rej = done = 0
            for s in range(nsim):
                if time.time() > deadline:
                    break
                rng = random.Random(seed + 100000 * ci + 1000 * n + s)
                xs = trim(sim_draw(cfg, n, rng))[0]
                if silverman(xs, 1, B, rng)["p"] <= ALPHA:
                    rej += 1
                done += 1
            res.append({"config": cfg, "bimodal": bimodal, "n": n, "sims": done,
                        "rejections": rej, "rate": rej / done if done else None})
    return res


# --------------------------------------------------------------------------
# grading (TEMPO-PREREG.md sections 5 and 6)
# --------------------------------------------------------------------------
def t1_label(f, fk):
    if f is None or fk is None:
        return None
    if fk < 0.2:
        return "T1_UNDERPOWERED"
    if f >= 0.5 * fk:
        return "TEMPO_MODES_FROM_RHYTHM_MIX"
    if f < 0.05:
        return "TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO"
    return "TEMPO_MODES_PARTLY_FROM_RHYTHM_MIX"


def t2_label(rows):
    rej = [r for r in rows if r["holm_reject"]]
    if not rej:
        return "NO_WITHIN_RHYTHM_TEMPO_MODES"
    if any(not r["known_variant"] for r in rej):
        return "TEMPO_DISCRETE_BEYOND_KNOWN_TYPES"
    return "TEMPO_DISCRETE_ONLY_IN_KNOWN_TYPES"


def t4_label(p):
    if p is None:
        return None
    return "MORE_COMBINATIONS_THAN_CUTTING" if p < ALPHA else "COMBINATIONS_MATCHED_BY_CUTTING"


def grade(out):
    g = {}
    gate = out.get("gate") or {}
    g["P1"] = (bool(gate.get("g1")) and bool(gate.get("g2"))) if gate else None
    rf = out.get("rf") or {}
    t2 = rf.get("t2")
    five = [r for r in (t2 or []) if r["key"][1] == "5R" and r["key"][0] == 5]
    g["P2"] = bool(five[0]["holm_reject"]) if five else None
    fk = (out.get("k4") or {}).get("f_all")
    l1 = t1_label((rf.get("t1") or {}).get("f_all"), fk)
    g["P3"] = (l1 == "TEMPO_MODES_FROM_RHYTHM_MIX") if l1 else None
    g["P4"] = (l1 == "TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO") if l1 else None
    l2 = t2_label(t2) if t2 is not None else None
    g["P5"] = (l2 == "TEMPO_DISCRETE_BEYOND_KNOWN_TYPES") if l2 else None
    p4 = (rf.get("t1") or {}).get("p_c")
    g["P6"] = (p4 < ALPHA) if p4 is not None else None
    cal = out.get("calibration") or []
    neg = [c for c in cal if not c["bimodal"] and c["rate"] is not None]
    g["P7"] = all(c["rate"] <= 0.10 for c in neg) if len(neg) == 6 else None
    pw = [c for c in cal if c["config"] == "mix50" and c["n"] == 200 and c["rate"] is not None]
    g["P8"] = (pw[0]["rate"] >= 0.8) if pw else None
    t3 = rf.get("t3")
    g["P9"] = any(r["label"] == "WITHIN_UNIT" for r in t3) if t3 else None
    lr = t1_label(((out.get("rl") or {}).get("t1") or {}).get("f_all"), fk)
    g["P10"] = (l1 == lr) if (l1 and lr) else None
    scored = [(PRIORS[p] - (1.0 if v else 0.0)) ** 2 for p, v in sorted(g.items())
              if v is not None]
    return {"labels": {"T1": l1, "T1_rl": lr, "T2": l2, "T4": t4_label(p4),
                       "T3": [r["label"] for r in (t3 or [])]},
            "predictions": g, "priors": PRIORS, "n_scored": len(scored),
            "brier": sum(scored) / len(scored) if scored else None}


# --------------------------------------------------------------------------
# job
# --------------------------------------------------------------------------
def wait_for_registration(max_minutes, fetcher=fetch):
    t0 = time.time()
    tries = 0
    last = None
    while True:
        tries += 1
        try:
            blob = fetcher(PREREG_URL)
            if b"TEMPO-PREREG" in blob:
                return {"found": True, "tries": tries,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(blob).hexdigest()}
        except Exception as e:                      # 404 until published
            last = repr(e)[:200]
        if time.time() - t0 > max_minutes * 60:
            return {"found": False, "tries": tries, "last_error": last}
        time.sleep(60)


def matches(got, want, tol=TOL_GATE):
    return len(got) == len(want) and all(abs(a - b) <= tol for a, b in zip(got, want))


def analyse_scheme(sample, assign, cuts, real_max, known, seed, with_t3, out_s, save):
    by, other = group(sample, assign)
    keys = sorted(by)
    names = key_names(keys)
    analysable = [k for k in keys if len(by[k]) >= MIN_N]
    rh = []
    for k in keys:
        comp = {}
        for r in by[k]:
            comp[r["type"]] = comp.get(r["type"], 0) + 1
        cc = cell_counts([r["dur"] for r in by[k]], cuts)
        rh.append({"key": [k[0], k[1]], "name": names[k], "n": len(by[k]),
                   "analysable": k in analysable, "known_variant": k in known, "cells": cc,
                   "occupied": occupied(cc, len(by[k])),
                   "gero_labels": dict(sorted(comp.items(), key=lambda kv: -kv[1])[:8])})
    out_s.update({"n_assigned": sum(len(v) for v in by.values()), "n_other": len(other),
                  "n_rhythms": len(keys), "n_analysable": len(analysable), "rhythms": rh})
    real_cells = {k: cell_counts([r["dur"] for r in by[k]], cuts) for k in analysable}
    c_obs = sum(occupied(real_cells[k], len(by[k])) for k in analysable)
    out_s["c_obs"] = c_obs
    out_s["ratio_obs"] = cond_entropy_ratio(real_cells)
    t = time.time()
    out_s["t2"] = run_t2(by, analysable, B_T2, seed + 10, names, known)
    out_s["t2_seconds"] = round(time.time() - t, 1)
    save()
    t = time.time()
    out_s["t1"] = run_t1(by, other, real_max, cuts, analysable, B_T1, seed + 1, c_obs)
    out_s["t1_seconds"] = round(time.time() - t, 1)
    save()
    if with_t3:
        rej = [tuple(r["key"]) for r in out_s["t2"] if r["holm_reject"]]
        out_s["t3"] = run_t3(by, rej, cuts, B_T3, seed + 30, names)
        save()
    return by, other, analysable


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--data-file", default="")
    ap.add_argument("--wait-minutes", type=float, default=120)
    ap.add_argument("--max-minutes", type=float, default=200)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    out_path = os.path.join(a.out_dir, "tempo_results.json")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "tempo.py"), "rb") as f:
        code_sha = hashlib.sha256(f.read()).hexdigest()
    out = {"version": VERSION, "python": sys.version.split()[0], "code_sha256": code_sha,
           "config": {"bw": BW, "lo": LO, "hi": HI, "min_n": MIN_N, "tol_mode": TOL_MODE,
                      "tol_gate": TOL_GATE, "alpha": ALPHA, "seed": SEED, "b_t1": B_T1,
                      "b_t2": B_T2, "b_t3": B_T3, "b_k4": B_K4, "n_sim": N_SIM,
                      "b_sim": B_SIM, "sizes": list(SIZES), "data_url": DATA_URL}}

    def save():
        tmp = out_path + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        os.replace(tmp, out_path)

    reg = wait_for_registration(a.wait_minutes)
    out["registration"] = reg
    if not reg["found"]:
        out["status"] = "not_run_unregistered"
        save()
        print("TEMPO-PREREG.md not public; nothing analysed")
        return 4
    t0 = time.time()
    if a.data_file:
        with open(a.data_file, "rb") as f:
            raw = f.read()
    else:
        raw = fetch(DATA_URL)
    out["data"] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    rows = parse_rows(raw.decode("utf-8-sig"))
    sample = select_sample(rows)
    durs = [r["dur"] for r in sample]
    out["data"].update({"rows": len(rows), "sample": len(sample)})
    exact = kde_grid_exact(durs, BW, GRID)
    mx, mn = extrema(exact, GRID)
    g1 = len(sample) == N_EXPECTED
    g2 = matches(mx, SHARMA_MAX) and matches(mn, SHARMA_MIN)
    cuts = mn if len(mn) == 4 else list(SHARMA_MIN)
    out["gate"] = {"g1": g1, "g2": g2, "n": len(sample), "maxima": mx, "minima": mn,
                   "cuts_used": cuts, "pooled_cells": cell_counts(durs, cuts)}
    print("GATE n=%d g1=%s g2=%s maxima=%s minima=%s" % (len(sample), g1, g2, mx, mn), flush=True)
    cents, labels, known = build_centroids(sample)
    out["centroids"] = [{"key": [k[0], k[1]], "labels": labels[k], "known_variant": k in known}
                        for k in sorted(cents)]
    save()
    keys_sorted = sorted(cents)
    out["rf"] = {}
    by, other, analysable = analyse_scheme(
        sample, lambda r: assign_rf(r, cents, keys_sorted), cuts, mx, known, SEED, True,
        out["rf"], save)
    print("RF T1 f_all %.3f hits %s | T4 C %d null %.1f p %.4f | T2 rejects %s" % (
        out["rf"]["t1"]["f_all"], out["rf"]["t1"]["mode_hit_rate"], out["rf"]["c_obs"],
        out["rf"]["t1"]["null_c_mean"], out["rf"]["t1"]["p_c"],
        [r["name"] for r in out["rf"]["t2"] if r["holm_reject"]]), flush=True)
    out["rl"] = {}
    analyse_scheme(sample, assign_rl, cuts, mx, known, SEED + 500, False, out["rl"], save)
    print("RL T1 f_all %.3f | T2 rejects %s" % (
        out["rl"]["t1"]["f_all"], [r["name"] for r in out["rl"]["t2"] if r["holm_reject"]]),
        flush=True)

    # K4: a pseudo-real data set drawn from the T1 null itself (machinery ceiling)
    pseudo = draw_surrogate(build_null(by), random.Random(SEED + 7))
    by_p = {k: [{"dur": d} for d in v] for k, v in pseudo.items()}
    pooled = list(other)
    for k in sorted(pseudo):
        pooled.extend(pseudo[k])
    mx_p, _ = extrema(kde_grid_binned(pooled, BW, GRID), GRID)
    k4 = run_t1(by_p, other, mx_p, cuts, analysable, B_K4, SEED + 8)
    out["k4"] = {"pseudo_maxima": mx_p, "f_all": k4["f_all"], "mode_hit_rate": k4["mode_hit_rate"],
                 "B": B_K4}
    save()
    print("K4 pseudo maxima %s f_all %.3f" % (mx_p, k4["f_all"]), flush=True)

    t = time.time()
    out["calibration"] = run_calib(N_SIM, B_SIM, SEED + 900, SIZES, t0 + a.max_minutes * 60)
    out["calibration_seconds"] = round(time.time() - t, 1)
    out["grade"] = grade(out)
    out["status"] = "ok"
    out["seconds"] = round(time.time() - t0, 1)
    save()
    print("GRADE", json.dumps(out["grade"]["labels"]), "brier", out["grade"]["brier"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
