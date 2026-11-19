# Unit tests for tempo.py (coda-tempo-test). Standard library only; no network, no data.
# MV2, Munim, Inc. Made with AI agents. Apache-2.0.
import random
import unittest


def T():
    import tempo
    return tempo


def row(n, icis, t, clan="EC1", unit="A"):
    icis = list(icis) + [0.0] * (9 - len(icis))
    return {"id": "x", "n": n, "dur": sum(icis), "icis": icis, "type": t, "clan": clan,
            "unit": unit, "idn": "0"}


def drow(d, unit="A"):
    return {"dur": d, "unit": unit}


class TestData(unittest.TestCase):
    def test_parse_and_select(self):
        t = T()
        text = (chr(0xFEFF) + "codaNUM2018,Date,nClicks,Duration,ICI1,ICI2,ICI3,ICI4,ICI5,ICI6,"
                "ICI7,ICI8,ICI9,CodaType,Clan,Unit,UnitNum,IDN\n"
                "1,04/03/2005,5,1.188,0.293,0.282,0.298,0.315,0,0,0,0,0,5R3,EC1,A,1,0\n"
                "2,25/03/2008,4,0.208,0.063,0.062,0.083,0,0,0,0,0,0,4R1,EC2,A,1,0\n"
                "3,25/03/2008,4,1.900,0.6,0.6,0.7,0,0,0,0,0,0,4R1,EC1,A,1,0\n")
        rows = t.parse_rows(text)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["id"], "1")
        self.assertEqual(rows[0]["n"], 5)
        self.assertAlmostEqual(rows[0]["dur"], 1.188)
        self.assertEqual(rows[0]["type"], "5R3")
        self.assertEqual(rows[0]["unit"], "A")
        s = t.select_sample(rows)
        self.assertEqual([r["id"] for r in s], ["1"])
        v = t.norm_ici(rows[0])
        self.assertEqual(len(v), 4)
        self.assertAlmostEqual(sum(v), 1.0, places=12)

    def test_merged_and_labelled(self):
        t = T()
        cases = {"5R1": "5R", "5R3": "5R", "4R2": "4R", "7D2": "7D", "1+31": "1+3",
                 "1+32": "1+3", "1+1+3": "1+1+3", "10R": "10R", "10i": "10i", "6i": "6i",
                 "2+3": "2+3", "3R": "3R", "8D": "8D"}
        for k, v in cases.items():
            self.assertEqual(t.merged(k), v, k)
        self.assertFalse(t.labelled("5-NOISE"))
        self.assertFalse(t.labelled(""))
        self.assertTrue(t.labelled("5R1"))

    def test_norm_ici_invalid(self):
        t = T()
        self.assertIsNone(t.norm_ici(row(2, [0.1], "x")))
        self.assertIsNone(t.norm_ici(row(4, [0.1, 0.0, 0.2], "x")))
        self.assertEqual(t.norm_ici(row(4, [0.1, 0.1, 0.2], "x")), [0.25, 0.25, 0.5])

    def test_centroids_known_and_assign(self):
        t = T()
        s = ([row(5, [0.07] * 4, "5R1") for _ in range(5)] +
             [row(5, [0.28] * 4, "5R3") for _ in range(5)] +
             [row(5, [0.4, 0.4, 0.1, 0.1], "1+1+3") for _ in range(2)] +
             [row(5, [0.2, 0.2, 0.2, 0.2], "5-NOISE")])
        cents, labels, known = t.build_centroids(s)
        self.assertEqual(sorted(cents), [(5, "5R")])
        self.assertEqual(labels[(5, "5R")], {"5R1": 5, "5R3": 5})
        self.assertEqual(known, [(5, "5R")])
        for x in cents[(5, "5R")]:
            self.assertAlmostEqual(x, 0.25)
        cents2 = {(5, "5R"): [0.25] * 4, (5, "1+1+3"): [0.4, 0.4, 0.1, 0.1]}
        self.assertEqual(t.assign_rf(row(5, [0.293, 0.282, 0.298, 0.315], "5-NOISE"), cents2),
                         (5, "5R"))
        self.assertEqual(t.assign_rf(row(5, [0.5, 0.45, 0.1, 0.12], "5R1"), cents2),
                         (5, "1+1+3"))
        self.assertIsNone(t.assign_rf(row(4, [0.1, 0.1, 0.1], "4R1"), cents2))
        self.assertEqual(t.assign_rl(row(5, [0.07] * 4, "5R2")), (5, "5R"))
        self.assertIsNone(t.assign_rl(row(5, [0.07] * 4, "5-NOISE")))

    def test_key_names_and_group(self):
        t = T()
        names = t.key_names([(5, "5R"), (4, "X"), (5, "X")])
        self.assertEqual(names, {(5, "5R"): "5R", (4, "X"): "X/n4", (5, "X"): "X/n5"})
        s = [row(5, [0.07] * 4, "5R1"), row(5, [0.07] * 4, "5-NOISE")]
        by, other = t.group(s, t.assign_rl)
        self.assertEqual(list(by), [(5, "5R")])
        self.assertEqual(len(other), 1)


class TestDensity(unittest.TestCase):
    def test_binned_matches_exact(self):
        t = T()
        xs = [0.3, 0.36, 0.8, 0.84, 1.2]          # maxima fall on grid points 0.33, 0.82, 1.20
        a = t.kde_grid_exact(xs, t.BW, t.GRID)
        b = t.kde_grid_binned(xs, t.BW, t.GRID)
        m = max(a)
        for u, v in zip(a, b):
            self.assertLess(abs(u - v), 1e-6 * m)
        self.assertEqual(t.extrema(a, t.GRID), t.extrema(b, t.GRID))

    def test_extrema(self):
        t = T()
        mx, mn = t.extrema([0, 1, 0, 2, 0], ["a", "b", "c", "d", "e"])
        self.assertEqual(mx, ["b", "d"])
        self.assertEqual(mn, ["c"])

    def test_n_modes_and_h_crit(self):
        t = T()
        xs = [0.3] * 20 + [0.9] * 20
        self.assertEqual(t.n_modes(xs, 0.02), 2)
        self.assertEqual(t.n_modes(xs, 0.25), 2)
        self.assertEqual(t.n_modes(xs, 1.0), 1)
        hc = t.h_crit(xs, 1)
        self.assertTrue(0.2 < hc < 0.4, hc)
        self.assertEqual(t.n_modes(xs, hc), 1)

    def test_silverman(self):
        t = T()
        rng = random.Random(1)
        xs = [rng.gauss(0.3, 0.02) for _ in range(100)] + [rng.gauss(0.9, 0.02) for _ in range(100)]
        r = t.silverman(xs, 1, 49, random.Random(2))
        self.assertLessEqual(r["p"], 0.05)
        self.assertEqual(r["B"], 49)
        u = [rng.gauss(0.42, 0.08) for _ in range(100)]
        r2 = t.silverman(u, 1, 19, random.Random(3))
        self.assertTrue(0 < r2["p"] <= 1)
        self.assertEqual(r2["n"], 100)

    def test_quantile_trim_holm(self):
        t = T()
        self.assertAlmostEqual(t.quantile([1, 2, 3, 4], 0.25), 1.75)
        keep, out, lo, hi = t.trim([1, 2, 3, 4, 100])
        self.assertEqual(keep, [1, 2, 3, 4])
        self.assertEqual(out, [100])
        self.assertAlmostEqual(hi, 10.0)
        self.assertEqual(t.holm([0.01, 0.04, 0.03], 0.05), [True, False, False])
        self.assertEqual(t.holm([0.01, 0.02, 0.03], 0.05), [True, True, True])
        self.assertEqual(t.holm([], 0.05), [])


class TestCells(unittest.TestCase):
    def test_tempo_cells(self):
        t = T()
        cuts = [0.45, 0.61, 0.93, 1.08]
        self.assertEqual(t.tempo_type(0.3, cuts), 0)
        self.assertEqual(t.tempo_type(0.45, cuts), 0)
        self.assertEqual(t.tempo_type(0.5, cuts), 1)
        self.assertEqual(t.tempo_type(1.2, cuts), 4)
        self.assertEqual(t.cell_counts([0.3, 0.5, 1.2, 1.3], cuts), [1, 1, 0, 0, 2])
        self.assertEqual(t.occupied([10, 9, 0, 0, 0], 100), 1)
        self.assertEqual(t.occupied([10, 10, 0, 0, 0], 200), 2)
        self.assertEqual(t.occupied([10, 10, 0, 0, 0], 201), 0)
        self.assertEqual(t.occupied([5, 4, 0, 0, 0], 40, 5, 10), 1)

    def test_entropy_ratio(self):
        t = T()
        self.assertAlmostEqual(t.cond_entropy_ratio({"a": [10, 0], "b": [0, 10]}), 0.0)
        self.assertAlmostEqual(t.cond_entropy_ratio({"a": [5, 5], "b": [5, 5]}), 1.0)
        self.assertIsNone(t.cond_entropy_ratio({}))


class TestPipeline(unittest.TestCase):
    def test_null_and_t1(self):
        t = T()
        by = {(5, "5R"): [drow(0.30 + 0.001 * i) for i in range(40)],
              (5, "1+1+3"): [drow(1.00 + 0.001 * i) for i in range(40)],
              (4, "4R"): [drow(0.2), drow(0.21), drow(0.22)]}
        plan = t.build_null(by)
        self.assertEqual(plan[(4, "4R")][0], "fixed")
        self.assertEqual(plan[(5, "5R")][0], "smooth")
        sur = t.draw_surrogate(plan, random.Random(1))
        self.assertEqual(len(sur[(5, "5R")]), 40)
        self.assertEqual(sur[(4, "4R")], [0.2, 0.21, 0.22])
        analysable = [(5, "1+1+3"), (5, "5R")]
        pooled = [r["dur"] for k in sorted(by) for r in by[k]]
        mx, _ = t.extrema(t.kde_grid_binned(pooled, t.BW, t.GRID), t.GRID)
        res = t.run_t1(by, [0.5], mx, list(t.SHARMA_MIN), analysable, 5, 7, c_obs=2)
        self.assertEqual(res["B"], 5)
        self.assertTrue(0 <= res["f_all"] <= 1)
        self.assertTrue(0 < res["p_c"] <= 1)
        self.assertEqual(len(res["mode_hit_rate"]), len(mx))

    def test_t2_t3(self):
        t = T()
        rng = random.Random(5)
        bi = ([drow(rng.gauss(0.3, 0.01), "A") for _ in range(30)] +
              [drow(rng.gauss(0.9, 0.01), "A") for _ in range(30)] +
              [drow(rng.gauss(0.3, 0.01), "B") for _ in range(10)])
        uni = [drow(rng.gauss(0.5, 0.05)) for _ in range(40)]
        by = {(5, "5R"): bi, (6, "6i"): uni}
        names = t.key_names(sorted(by))
        rows = t.run_t2(by, sorted(by), 19, 11, names, [(5, "5R")])
        self.assertEqual([r["name"] for r in rows], ["5R", "6i"])
        self.assertLessEqual(rows[0]["p"], 0.1)
        self.assertTrue(rows[0]["known_variant"])
        self.assertIn("holm_reject", rows[1])
        res = t.run_t3(by, [(5, "5R")], list(t.SHARMA_MIN), 19, 13, names)
        self.assertEqual(len(res), 1)
        self.assertEqual([u["unit"] for u in res[0]["units"]], ["A"])
        self.assertIn(res[0]["label"], ("WITHIN_UNIT", "BETWEEN_UNITS", "UNRESOLVED"))
        self.assertAlmostEqual(res[0]["top_unit_share"], 60 / 70)

    def test_calib_small(self):
        t = T()
        import time
        res = t.run_calib(1, 9, 3, (50,), time.time() + 600)
        self.assertEqual(len(res), 4)
        self.assertEqual([c["config"] for c in res], ["gauss", "lognormal", "mix50", "mix80"])
        self.assertTrue(all(c["sims"] == 1 for c in res))


class TestGrading(unittest.TestCase):
    def test_t1_label(self):
        t = T()
        self.assertIsNone(t.t1_label(None, 0.5))
        self.assertEqual(t.t1_label(0.5, 0.1), "T1_UNDERPOWERED")
        self.assertEqual(t.t1_label(0.3, 0.5), "TEMPO_MODES_FROM_RHYTHM_MIX")
        self.assertEqual(t.t1_label(0.04, 0.5), "TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO")
        self.assertEqual(t.t1_label(0.1, 0.5), "TEMPO_MODES_PARTLY_FROM_RHYTHM_MIX")
        self.assertEqual(t.t4_label(0.01), "MORE_COMBINATIONS_THAN_CUTTING")
        self.assertEqual(t.t4_label(0.5), "COMBINATIONS_MATCHED_BY_CUTTING")

    def test_grade_toy(self):
        t = T()
        cal = [{"config": c, "bimodal": False, "n": n, "rate": 0.02}
               for c in ("gauss", "lognormal") for n in (50, 200, 800)]
        cal.append({"config": "mix50", "bimodal": True, "n": 200, "rate": 0.9})
        out = {"gate": {"g1": True, "g2": True},
               "rf": {"t1": {"f_all": 0.6, "p_c": 0.2},
                      "t2": [{"name": "5R", "key": [5, "5R"], "holm_reject": True,
                              "known_variant": True},
                             {"name": "1+1+3", "key": [5, "1+1+3"], "holm_reject": False,
                              "known_variant": False}],
                      "t3": [{"label": "BETWEEN_UNITS"}]},
               "rl": {"t1": {"f_all": 0.02}},
               "k4": {"f_all": 0.8},
               "calibration": cal}
        g = t.grade(out)
        p = g["predictions"]
        self.assertEqual(p, {"P1": True, "P2": True, "P3": True, "P4": False, "P5": False,
                             "P6": False, "P7": True, "P8": True, "P9": False, "P10": False})
        self.assertEqual(g["labels"]["T1"], "TEMPO_MODES_FROM_RHYTHM_MIX")
        self.assertEqual(g["labels"]["T1_rl"], "TEMPO_MODES_NEED_WITHIN_RHYTHM_TEMPO")
        self.assertEqual(g["labels"]["T2"], "TEMPO_DISCRETE_ONLY_IN_KNOWN_TYPES")
        self.assertEqual(g["labels"]["T4"], "COMBINATIONS_MATCHED_BY_CUTTING")
        self.assertEqual(g["n_scored"], 10)
        self.assertAlmostEqual(g["brier"], 0.19625, places=9)

    def test_grade_missing(self):
        t = T()
        g = t.grade({})
        self.assertEqual(g["n_scored"], 0)
        self.assertIsNone(g["brier"])

    def test_registration(self):
        t = T()
        r = t.wait_for_registration(0, lambda url: b"# TEMPO-PREREG\n")
        self.assertTrue(r["found"])
        self.assertEqual(r["tries"], 1)
        self.assertTrue(t.matches([0.33, 0.51], [0.335, 0.50]))
        self.assertFalse(t.matches([0.33], [0.33, 0.51]))


if __name__ == "__main__":
    unittest.main()
