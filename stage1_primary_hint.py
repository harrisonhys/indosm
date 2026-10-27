"""Improve stage-1 rank 1 for primary[rank1]: 2x2 of catalog {def, elements} x hint {none, described}.

primary[rank1] = stage 1 (dict) -> stage 2 llm_full+dict on the elements of the FIRST picked resource only.
The hint asks for the resource the table describes, not one it only references through a foreign key. It is
written in generic FHIR terms (no Khanza column names), though it was motivated by the n=41 error analysis.
def/none reproduces primary[rank1] from stage2_primary.py (cache hit). Scored n:1-neutral.
Writes results/stage1_primary_hint.csv. Usage: python stage1_primary_hint.py
"""
import json

import pandas as pd

from hybrid import CACHE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from rescore_n40 import neutral
from stage1_rich import MISSED, catalogs
from two_stage import LARGE_PAIRS, select_resources

HINTS = {
    "none": "",
    "described": ("Put first the resource that the table itself describes, i.e. what one row of the table is an "
                  "instance of. Do not put first a resource the table only points to through a foreign key: a column "
                  "holding the identifier or code of a visit, a patient or a practitioner is a reference to an "
                  "Encounter, Patient or Practitioner, not evidence that the table is one."),
}


def main():
    n_cached, cats, rows = len(json.loads(CACHE.read_text())), catalogs(), []
    for cat_name in ("def", "elements"):
        for hint_name, hint in HINTS.items():
            for p in json.loads(LARGE_PAIRS.read_text()):
                pid = p["id"].removesuffix("L")
                src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
                right = p["gt"][0][1].split(".")[0]
                picked, r1 = select_resources(src, True, catalog=cats[cat_name], hint=hint)
                sc, r2 = llm_full(src, [t for t in tgt if t.split(".")[0] == picked[0]], True) if picked \
                    else ({}, {"prompt_tokens": 0})
                sc = neutral(sc, p)
                rows.append({"pair": pid, "config": f"rank1[{cat_name}|{hint_name}]", "resource": right,
                             "picked": "|".join(picked), "hit": right in picked,
                             "hit@1": bool(picked) and picked[0] == right, "missed_before": pid in MISSED,
                             "R@GT_neutral": recall_at_gt(sc, gt), "F1_neutral": f1_one_to_one(sc, gt),
                             "prompt_tokens": r1["prompt_tokens"] + r2["prompt_tokens"],
                             "sec": r1.get("sec", 0.0) + r2.get("sec", 0.0)})
            print(f"done {cat_name}|{hint_name}, new LLM calls so far "
                  f"{len(json.loads(CACHE.read_text())) - n_cached}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/stage1_primary_hint.csv", index=False)
    print(df.groupby("config", sort=False)[["hit", "hit@1", "R@GT_neutral", "F1_neutral", "prompt_tokens"]]
          .mean().round(3).to_string())


if __name__ == "__main__":
    main()
