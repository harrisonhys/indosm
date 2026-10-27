"""Two-stage vs llm-full (large target, 289 elements) vs oracle (right resource given) on the same 15 pairs.

Usage: python compare_two_stage.py
"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

COMPARISONS = [("two-stage", "llm-full (large)"), ("two-stage+dict", "llm-full+dict (large)"),
               ("two-stage-per-res+dict", "llm-full+dict (large)"), ("two-stage-per-res+dict", "two-stage+dict"),
               ("two-stage+dict", "two-stage"), ("oracle+dict", "two-stage+dict")]


def load() -> pd.DataFrame:
    ts = pd.read_csv("results/two_stage.csv")
    large = pd.read_csv("results/hybrid_scores_large_k5.csv")
    small = pd.read_csv("results/hybrid_scores_k5.csv")
    large = large[large.config.isin(["llm-full", "llm-full+dict"])].assign(
        pair=lambda d: d.pair.str.removesuffix("L"), config=lambda d: d.config + " (large)")
    oracle = small[small.config.isin(["llm-full", "llm-full+dict"]) & small.pair.isin(ts.pair)].assign(
        config=lambda d: d.config.str.replace("llm-full", "oracle"))
    cols = ["pair", "config", "R@GT", "F1", "prompt_tokens", "completion_tokens", "sec"]
    return pd.concat([ts[cols], large[cols], oracle[cols]])


def main():
    df = load()
    order = ["llm-full (large)", "llm-full+dict (large)", "two-stage", "two-stage+dict", "two-stage-per-res",
             "two-stage-per-res+dict", "oracle", "oracle+dict"]
    print("== mean over 15 pairs ==")
    print(df.groupby("config")[["R@GT", "F1", "prompt_tokens", "completion_tokens", "sec"]].mean().loc[order].round(3).to_string())
    for metric in ("R@GT", "F1"):
        wide = df.pivot_table(index="pair", columns="config", values=metric)
        print(f"\n-- paired {metric}, n={len(wide)} --")
        for a, b in COMPARISONS:
            d = (wide[a] - wide[b]).to_numpy()
            p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
            print(f"{a:>15} - {b:<22} mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
                  f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.3f}")
    ts = pd.read_csv("results/two_stage.csv")
    print("\n== stage 1: resource selection ==")
    print(ts.groupby("config")[["hit", "hit@1", "n_targets", "stage1_tokens"]].mean().round(3).to_string())
    print(ts[["pair", "config", "right_resource", "picked", "hit", "R@GT"]].to_string(index=False))


if __name__ == "__main__":
    main()
