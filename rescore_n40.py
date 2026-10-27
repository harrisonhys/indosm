"""Rescore the n=41 run with an n:1-neutral metric (from cache, no new LLM calls).

The convention says gt_n1 and ambiguous pairs are "not scored", but the strict metric still counts such predictions
as false positives when they rank in the top-|GT| (R@GT) or take a 1:1 slot (F1). Here they are removed from the
predictions before scoring, i.e. neither rewarded nor penalised. Writes results/n40_neutral.csv.
Usage: python rescore_n40.py
"""
import json

import pandas as pd

from ablation_gloss import QWEN, SMALL_PAIRS
from hybrid import CACHE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from two_stage import LARGE_PAIRS, two_stage


def neutral(scores: dict, p: dict) -> dict:
    skip = {(s, t) for s, t, *_ in p["gt_n1"] + p["ambiguous"]}
    return {k: v for k, v in scores.items() if k not in skip}


def main():
    n0 = len(json.loads(CACHE.read_text()))
    small = {p["id"]: p for p in json.loads(SMALL_PAIRS.read_text())}
    rows = []
    for p in json.loads(LARGE_PAIRS.read_text()):
        pid = p["id"].removesuffix("L")
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        runs = {"llm-full+dict": llm_full(src, tgt, True)[0],
                "two-stage+dict": two_stage(src, tgt, True)[0],
                "two-stage+qgloss@12": two_stage(src, tgt, QWEN)[0]}
        sp = small[pid]
        osc = llm_full(columns(sp["source"]), columns(sp["target"]), True)[0]
        for name, sc in runs.items():
            rows.append({"pair": pid, "config": name, "R@GT": recall_at_gt(neutral(sc, p), gt),
                         "F1": f1_one_to_one(neutral(sc, p), gt)})
        ogt = {tuple(x) for x in sp["gt"]}
        rows.append({"pair": pid, "config": "oracle+dict", "R@GT": recall_at_gt(neutral(osc, sp), ogt),
                     "F1": f1_one_to_one(neutral(osc, sp), ogt)})
    assert len(json.loads(CACHE.read_text())) == n0, "rescoring must not call the LLM"
    strict = pd.read_csv("results/n40.csv")[["pair", "config", "resource"]]
    df = pd.DataFrame(rows).merge(strict, on=["pair", "config"])
    df.to_csv("results/n40_neutral.csv", index=False)
    print("rescored", len(df), "rows from cache (0 new LLM calls)")


if __name__ == "__main__":
    main()
