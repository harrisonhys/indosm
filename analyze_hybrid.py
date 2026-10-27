"""Paired comparison of hybrid configs on sub-set E, focus group khanza-fhir.

Usage: python analyze_hybrid.py results/hybrid_scores_k5.csv
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

FOCUS = "khanza-fhir"
COMPARISONS = [("hybrid", "llm-full"), ("llm-full+dict", "llm-full"), ("hybrid+dict", "hybrid"),
               ("hybrid+dict", "llm-full"), ("emb+dict", "emb")]


def boot_ci(diff: np.ndarray, n: int = 10000, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = rng.choice(diff, (n, len(diff))).mean(axis=1)
    return tuple(np.percentile(means, [2.5, 97.5]).round(3))


def compare(df: pd.DataFrame, metric: str, label: str):
    wide = df.pivot_table(index="pair", columns="config", values=metric)
    print(f"\n-- {label}: {metric}, n={len(wide)} pairs --")
    for a, b in COMPARISONS:
        d = (wide[a] - wide[b]).to_numpy()
        p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
        print(f"{a:>14} - {b:<9} mean {d.mean():+.3f}  95% CI {boot_ci(d)}  wins/ties/losses "
              f"{(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  Wilcoxon p={p:.3f}")


def main(path: str):
    df = pd.read_csv(path)
    focus = df[df.group == FOCUS]
    print(f"== {FOCUS}: per-pair R@GT ==")
    print(focus.pivot_table(index="pair", columns="config", values="R@GT").round(2).to_string())
    for metric in ("R@GT", "F1"):
        compare(focus, metric, FOCUS)
        compare(df, metric, "all sub-set E")
    llm = df[df.prompt_tokens > 0]
    print("\n== cost per table pair (mean over all 28 pairs) ==")
    print(llm.groupby("config")[["prompt_tokens", "completion_tokens", "sec"]].mean().round(0).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
