"""Small vs large FHIR target on the same 15 pairs (E01-E14, E20): accuracy, token cost, resource confusion.

Usage: python analyze_large.py <k>   (needs results/hybrid_scores_k<k>.csv and results/hybrid_scores_large_k<k>.csv)
Resource confusion re-reads the cached LLM answers (no new LLM calls; embeddings are recomputed).
"""
import json
import pathlib
import sys

import pandas as pd

from analyze_hybrid import compare
from hybrid import CONFIGS, columns

LARGE_PAIRS = pathlib.Path("data/subset_e/pairs_e_large.json")
LLM_CONFIGS = ["llm-full", "llm-full+dict", "hybrid", "hybrid+dict"]


def resource_confusion(k: int) -> pd.DataFrame:
    rows = []
    for p in json.loads(LARGE_PAIRS.read_text()):
        right = p["gt"][0][1].split(".")[0]
        src, tgt = columns(p["source"]), columns(p["target"])
        for name in LLM_CONFIGS:
            fn, use_dict = CONFIGS[name]
            scores, _ = fn(src, tgt, use_dict, k)
            rows += [{"pair": p["id"], "config": name, "other_resource": t.split(".")[0] != right} for (_, t) in scores]
    return pd.DataFrame(rows).groupby("config").other_resource.mean().rename("share of predictions in another resource")


def main(k: int):
    small = pd.read_csv(f"results/hybrid_scores_k{k}.csv")
    large = pd.read_csv(f"results/hybrid_scores_large_k{k}.csv")
    ids = {i.removesuffix("L") for i in large.pair}
    small = small[small.pair.isin(ids)]
    both = pd.concat([small.assign(target="small"), large.assign(target="large", pair=large.pair.str.removesuffix("L"))])
    print(f"== k={k}: mean over {len(ids)} pairs (small = one FHIR resource, large = union of 11, 289 elements) ==")
    print(both.pivot_table(index="config", columns="target", values=["R@GT", "F1"]).round(3).to_string())
    llm = both[both.prompt_tokens > 0]
    print("\n== cost per table pair ==")
    print(llm.pivot_table(index="config", columns="target", values=["prompt_tokens", "completion_tokens", "sec"])
          .round(0).to_string())
    for metric in ("R@GT", "F1"):
        compare(large.assign(pair=large.pair.str.removesuffix("L")), metric, "large target")
    print("\n== resource confusion (large target) ==")
    print(resource_confusion(k).round(3).to_string())


if __name__ == "__main__":
    main(int(sys.argv[1]))
