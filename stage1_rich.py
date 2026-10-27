"""Stage-1 catalog ablation on the n=41 large target: does a fuller FHIR resource description fix resource selection?

Catalog variants (data/fhir_catalog_rich.json, built by fhir_catalog.py), all two-stage+dict:
  short      root `short` (= the earlier two-stage+dict run, cache hit)
  def        root definition (+ comment)
  elements   short + top-level element names
  scope      definition + "Scope and Usage" section
  scope+bnr  definition + "Scope and Usage" + "Boundaries and Relationships"
Stage 2 is unchanged (union of picked resources); it only makes new calls when the picked set changes.
Scored strict and n:1-neutral. Writes results/stage1_rich.csv. Usage: python stage1_rich.py
"""
import json

import pandas as pd

from ablation_gloss import row
from fhir_catalog import OUT as RICH
from hybrid import CACHE, columns
from rescore_n40 import neutral
from pilot import f1_one_to_one, recall_at_gt
from two_stage import LARGE_PAIRS, two_stage

MISSED = {"E12", "E13", "E29", "E51", "E52", "E53", "E54"}


def catalogs() -> dict[str, dict[str, str]]:
    rich = json.loads(RICH.read_text())
    return {"short": {n: d["short"] for n, d in rich.items()},
            "def": {n: d["definition"] for n, d in rich.items()},
            "elements": {n: f"{d['short']}. Elements: {', '.join(d['elements'])}" for n, d in rich.items()},
            "scope": {n: f"{d['definition']} {d['scope']}" for n, d in rich.items()},
            "scope+bnr": {n: " ".join(filter(None, (d["definition"], d["scope"], d["boundaries"])))
                          for n, d in rich.items()}}


def main():
    n_cached = len(json.loads(CACHE.read_text()))
    cats, rows = catalogs(), []
    for variant, cat in cats.items():
        for p in json.loads(LARGE_PAIRS.read_text()):
            pid = p["id"].removesuffix("L")
            src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
            right = p["gt"][0][1].split(".")[0]
            # ponytail: "short" passes the catalog explicitly; same text as CATALOG so the prompt is byte-identical
            scores, picked, r1, r2 = two_stage(src, tgt, True, catalog=cat)
            use = {k: r1.get(k, 0) + r2.get(k, 0) for k in ("prompt_tokens", "completion_tokens", "sec")}
            rows.append(row(pid, f"two-stage+dict[{variant}]", scores, gt, use, picked, right)
                        | {"resource": right, "missed_before": pid in MISSED,
                           "stage1_prompt_tokens": r1["prompt_tokens"],
                           "R@GT_neutral": recall_at_gt(neutral(scores, p), gt),
                           "F1_neutral": f1_one_to_one(neutral(scores, p), gt)})
        print(f"done {variant}, new LLM calls so far {len(json.loads(CACHE.read_text())) - n_cached}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/stage1_rich.csv", index=False)
    print(df.groupby("config", sort=False)[["hit", "hit@1", "R@GT_neutral", "F1_neutral", "stage1_prompt_tokens",
                                            "prompt_tokens", "sec"]].mean().round(3).to_string())


if __name__ == "__main__":
    main()
