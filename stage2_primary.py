"""Stage 2 with ONE primary resource: match each stage-1 resource separately (catalog `def`), then keep only the
matches of a single resource instead of the union. Motivated by the Encounter-absorption finding: the GT puts all
of a table's correspondences in one resource, so a union lets Encounter swallow the predictions.

Selection rules (no extra LLM calls):
  rank1     stage-1 order, first pick
  sum_conf  resource with the largest total match confidence
  coverage  resource that matches the most distinct source columns (ties: sum_conf)
  best      resource with the highest R@GT (selection ceiling given the picks; not a method)
Scored n:1-neutral. Writes results/stage2_primary.csv. Usage: python stage2_primary.py
"""
import json

import pandas as pd

from hybrid import CACHE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from rescore_n40 import neutral
from stage1_rich import MISSED, catalogs
from two_stage import LARGE_PAIRS, select_resources

RULES = {
    "rank1": lambda per, picked: picked[0],
    "sum_conf": lambda per, picked: max(picked, key=lambda r: sum(per[r].values())),
    "coverage": lambda per, picked: max(picked, key=lambda r: (len({s for s, _ in per[r]}), sum(per[r].values()))),
}


def main():
    n_cached, cat, rows = len(json.loads(CACHE.read_text())), catalogs()["def"], []
    for p in json.loads(LARGE_PAIRS.read_text()):
        pid = p["id"].removesuffix("L")
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        right = p["gt"][0][1].split(".")[0]
        picked, r1 = select_resources(src, True, catalog=cat)
        per, tokens, sec = {}, r1["prompt_tokens"], r1.get("sec", 0.0)
        for r in picked:
            sc, r2 = llm_full(src, [t for t in tgt if t.split(".")[0] == r], True)
            per[r] = sc  # raw: selection rules must not see GT-derived n:1/ambiguous lists
            tokens, sec = tokens + r2["prompt_tokens"], sec + r2.get("sec", 0.0)
        r_at = {r: recall_at_gt(neutral(per[r], p), gt) for r in picked}
        chosen = {name: rule(per, picked) for name, rule in RULES.items() if picked}
        chosen["best"] = max(picked, key=r_at.get) if picked else None
        for name, r in chosen.items():
            sc = neutral(per.get(r, {}), p)
            rows.append({"pair": pid, "config": f"primary[{name}]", "resource": right, "picked": "|".join(picked),
                         "chosen": r, "chosen_right": r == right, "hit": right in picked,
                         "missed_before": pid in MISSED, "R@GT_neutral": recall_at_gt(sc, gt),
                         "F1_neutral": f1_one_to_one(sc, gt), "prompt_tokens": tokens, "sec": sec})
        print(f"done {pid}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/stage2_primary.csv", index=False)
    print(f"new LLM calls: {len(json.loads(CACHE.read_text())) - n_cached}")
    print(df.groupby("config", sort=False)[["chosen_right", "R@GT_neutral", "F1_neutral", "prompt_tokens", "sec"]]
          .mean().round(3).to_string())


if __name__ == "__main__":
    main()
