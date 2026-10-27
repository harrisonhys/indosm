"""Pre-registered confirmation run (PREREG_CONFIRM.md) on the held-out non-Khanza set, large target (289 elements).

Frozen configs: llm-full+dict, union[def], primary[rank1] (def catalog, no hint), oracle+dict. Refuses to run if
the GT files no longer match the hashes frozen in PREREG_CONFIRM.md. Writes results/confirm.csv (n:1-neutral).
Usage: python run_confirm.py
"""
import hashlib
import json
import pathlib

import pandas as pd

from draft_confirm import OUT as SMALL, OUT_LARGE as LARGE
from hybrid import CACHE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from rescore_n40 import neutral
from stage1_rich import catalogs
from two_stage import select_resources, two_stage

PREREG = pathlib.Path("PREREG_CONFIRM.md")


def frozen():
    text = PREREG.read_text()
    for f in (SMALL, LARGE):
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        assert h in text, f"{f.name} changed after pre-registration (sha256 {h})"


def main():
    frozen()
    n_cached, cat, rows = len(json.loads(CACHE.read_text())), catalogs()["def"], []
    small = {p["id"]: p for p in json.loads(SMALL.read_text())}
    for p in json.loads(LARGE.read_text()):
        pid = p["id"].removesuffix("L")
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        right = p["gt"][0][1].split(".")[0]
        runs = {}
        sc, r = llm_full(src, tgt, True)
        runs["llm-full+dict"] = (sc, r["prompt_tokens"], r.get("sec", 0.0), None)
        sc, picked, r1, r2 = two_stage(src, tgt, True, catalog=cat)
        runs["union[def]"] = (sc, r1["prompt_tokens"] + r2["prompt_tokens"], r1.get("sec", 0.0) + r2.get("sec", 0.0),
                              picked)
        picked, r1 = select_resources(src, True, catalog=cat)  # cache hit: same stage-1 prompt as union[def]
        sc, r2 = llm_full(src, [t for t in tgt if t.split(".")[0] == picked[0]], True) if picked \
            else ({}, {"prompt_tokens": 0})
        runs["primary[rank1]"] = (sc, r1["prompt_tokens"] + r2["prompt_tokens"],
                                  r1.get("sec", 0.0) + r2.get("sec", 0.0), picked)
        sp = small[pid]
        osc, r = llm_full(columns(sp["source"]), columns(sp["target"]), True)
        ogt = {tuple(x) for x in sp["gt"]}
        for name, (sc, tok, sec, pk) in runs.items():
            rows.append({"pair": pid, "config": name, "system": p["source"].split("__")[0], "resource": right,
                         "R@GT_neutral": recall_at_gt(neutral(sc, p), gt), "F1_neutral": f1_one_to_one(neutral(sc, p), gt),
                         "picked": "|".join(pk) if pk is not None else "",
                         "hit": (right in pk) if pk is not None else None,
                         "hit@1": (bool(pk) and pk[0] == right) if pk is not None else None,
                         "prompt_tokens": tok, "sec": sec})
        rows.append({"pair": pid, "config": "oracle+dict", "system": p["source"].split("__")[0], "resource": right,
                     "R@GT_neutral": recall_at_gt(neutral(osc, sp), ogt), "F1_neutral": f1_one_to_one(neutral(osc, sp), ogt),
                     "prompt_tokens": r["prompt_tokens"], "sec": r.get("sec", 0.0)})
        print(f"done {pid}", flush=True)
    df = pd.DataFrame(rows).astype({"hit": float, "hit@1": float})
    df.to_csv("results/confirm.csv", index=False)
    print(f"new LLM calls: {len(json.loads(CACHE.read_text())) - n_cached}")
    print(df.groupby("config", sort=False)[["R@GT_neutral", "F1_neutral", "hit", "hit@1", "prompt_tokens"]]
          .mean().round(3).to_string())


if __name__ == "__main__":
    main()
