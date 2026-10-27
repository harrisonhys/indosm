"""Analysis of the table-name ablation (results/ablation_table.csv). Usage: python analyze_ablation_table.py"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

ORDER = ["llm-full+dict", "llm-full+dict+table", "two-stage+dict", "two-stage+dict+t1", "two-stage+dict+t12"]
COMPARISONS = [("llm-full+dict+table", "llm-full+dict"), ("two-stage+dict+t1", "two-stage+dict"),
               ("two-stage+dict+t12", "two-stage+dict+t1"), ("two-stage+dict+t12", "llm-full+dict+table"),
               ("oracle+dict", "two-stage+dict+t12")]


def main():
    df = pd.read_csv("results/ablation_table.csv")
    small = pd.read_csv("results/hybrid_scores_k5.csv")
    oracle = small[(small.config == "llm-full+dict") & small.pair.isin(df.pair)].assign(config="oracle+dict")
    allr = pd.concat([df, oracle[["pair", "config", "R@GT", "F1", "prompt_tokens", "completion_tokens", "sec"]]])
    print("== mean over 15 pairs ==")
    print(allr.groupby("config")[["R@GT", "F1", "prompt_tokens", "completion_tokens", "sec"]].mean()
          .loc[ORDER + ["oracle+dict"]].round(3).to_string())
    print("\n== stage 1 ==")
    print(df[df.config.str.startswith("two-stage")].groupby("config")[["hit", "hit@1"]].mean().round(3).to_string())
    for metric in ("R@GT", "F1"):
        wide = allr.pivot_table(index="pair", columns="config", values=metric)
        print(f"\n-- paired {metric}, n={len(wide)} --")
        for a, b in COMPARISONS:
            d = (wide[a] - wide[b]).to_numpy()
            p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
            print(f"{a:>20} - {b:<20} mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
                  f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.3f}")
    print("\n== per pair R@GT ==")
    print(allr.pivot_table(index="pair", columns="config", values="R@GT")[ORDER + ["oracle+dict"]].round(2).to_string())
    ts = df[df.config.str.startswith("two-stage")]
    print("\n== stage-1 picks ==")
    print(ts.pivot_table(index=["pair", "table"], columns="config", values="picked", aggfunc="first").to_string())


if __name__ == "__main__":
    main()
