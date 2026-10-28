"""Unit tests for the evaluator (revision2_analyses.scores_for / revision_analyses.assign / pilot.recall_at_gt).
Plain asserts, no test framework. Usage: python tests/test_evaluation.py  (from the indosm directory)
Covers: unmatched tables, target collisions, gold n:1 and ambiguous predictions under the three policies, equal
confidences (ties keep the model's output order), R@|GT| cut-off ties, and, on the real result files, that the
strict and lenient policies share one assignment (same recall, lenient precision >= strict precision).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from pilot import recall_at_gt  # noqa: E402
from revision2_analyses import scores_for  # noqa: E402
from revision_analyses import assign  # noqa: E402

PAIR = {"gt": [["tgl", "R.period"], ["kd", "R.requester"]],
        "gt_n1": [["jam", "R.period"]],
        "ambiguous": [["pj", "R.account", "payer vs account"]]}


def close(a, b):
    return abs(a - b) < 1e-9


def test_unmatched():
    s = scores_for({}, PAIR)
    assert all(s[f"{m}_{p}"] == 0 for m in ("P", "R", "F1") for p in ("strict", "neutral", "lenient"))
    assert s["R@GT_strict"] == 0


def test_collision_keeps_higher_confidence():
    a = assign({("tgl", "R.period"): 0.6, ("kd", "R.period"): 0.9})
    assert a == {("kd", "R.period")}


def test_unmatched_source_and_zero_confidence():
    assert assign({("tgl", "R.period"): 0.0}) == set()


def test_n1_prediction_under_three_policies():
    # the n:1 column outranks the gold 1:1 column for the same element
    sc = {("jam", "R.period"): 0.9, ("tgl", "R.period"): 0.8, ("kd", "R.requester"): 0.7}
    s = scores_for(sc, PAIR)
    # strict: A = {jam->period (FP), kd->requester (TP)}
    assert close(s["P_strict"], 1 / 2) and close(s["R_strict"], 1 / 2)
    # lenient: same A, jam->period credited in precision only
    assert close(s["P_lenient"], 1.0) and close(s["R_lenient"], 1 / 2)
    # neutral: jam->period removed before assignment, so tgl->period takes the element
    assert close(s["P_neutral"], 1.0) and close(s["R_neutral"], 1.0)
    assert s["F1_neutral"] > s["F1_lenient"] > s["F1_strict"]


def test_ambiguous_prediction():
    sc = {("pj", "R.account"): 0.9, ("kd", "R.requester"): 0.8}
    s = scores_for(sc, PAIR)
    assert close(s["P_strict"], 1 / 2) and close(s["P_lenient"], 1.0) and close(s["P_neutral"], 1.0)
    assert close(s["R_strict"], 1 / 2) and close(s["R_lenient"], 1 / 2) and close(s["R_neutral"], 1 / 2)


def test_equal_confidence_keeps_output_order():
    first = {("tgl", "R.period"): 0.7, ("jam", "R.period"): 0.7}
    second = {("jam", "R.period"): 0.7, ("tgl", "R.period"): 0.7}
    assert assign(first) == {("tgl", "R.period")}
    assert assign(second) == {("jam", "R.period")}


def test_recall_at_gt_cutoff_and_ties():
    gt = {("tgl", "R.period"), ("kd", "R.requester")}
    sc = {("x", "R.status"): 0.9, ("tgl", "R.period"): 0.5, ("kd", "R.requester"): 0.5}
    assert close(recall_at_gt(sc, gt), 1 / 2)  # only the top |GT| = 2 are inspected


def test_strict_and_lenient_share_assignment_on_results():
    rows = 0
    for f in pathlib.Path(__file__).resolve().parents[1].glob("results/revision2__*.csv"):
        d = pd.read_csv(f)
        assert (d.R_strict == d.R_lenient).all(), f"{f.name}: recall differs between strict and lenient"
        assert (d.P_lenient >= d.P_strict - 1e-12).all(), f"{f.name}: lenient precision below strict"
        rows += len(d)
    assert rows > 0, "no result files found"
    print(f"  checked {rows} result rows")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)} tests passed")
