"""Qwen3-8B (local) vs a second model on the four headline configs. Exploratory for the second model (configs were
frozen on Qwen). Usage: python analyze_model2.py results/model2__qwen3_8b.csv results/model2__glm-5.3-flash.csv"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

ORDER = ["llm-full+dict", "union[def]", "primary[rank1]", "oracle+dict"]
COMPARE = [("primary[rank1]", "llm-full+dict"), ("primary[rank1]", "union[def]"), ("oracle+dict", "primary[rank1]")]


def main():
    df = pd.concat([pd.read_csv(f) for f in sys.argv[1:]], ignore_index=True)
    df["set"] = pd.Categorical(df["set"], ["dev41", "confirm18"])
    print("== R@GT_neutral (F1_neutral) by model x set ==")
    for metric in ("R@GT_neutral", "F1_neutral"):
        print(f"\n{metric}")
        print(df.pivot_table(index=["model", "set"], columns="config", values=metric, observed=True)[ORDER]
              .round(3).to_string())
    print("\n== stage 1 hit@1, mean prompt / completion tokens, median sec ==")
    print(df[df.config == "primary[rank1]"].groupby(["model", "set"], observed=True)["hit@1"].mean().round(3).to_string())
    print(df.groupby(["model", "config"])[["prompt_tokens", "completion_tokens"]].mean().round(0).to_string())
    print(df.groupby(["model", "config"])["sec"].median().round(1).to_string())
    for model in df.model.unique():
        for set_name in ("dev41", "confirm18", "pooled59"):
            sub = df[df.model == model] if set_name == "pooled59" else df[(df.model == model) & (df.set == set_name)]
            wide = sub.pivot_table(index="pair", columns="config", values="R@GT_neutral", observed=True)
            print(f"\n-- {model} / {set_name} (n={len(wide)}), R@GT_neutral, two-sided Wilcoxon --")
            for a, b in COMPARE:
                d = (wide[a] - wide[b]).to_numpy()
                p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
                print(f"   {a:>15} - {b:<14} {d.mean():+.3f}  CI {boot_ci(d)}  "
                      f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.4f}")
    if df.model.nunique() == 2:
        m1, m2 = df.model.unique()
        w = df.pivot_table(index=["set", "pair", "config"], columns="model", values="R@GT_neutral", observed=True).dropna()
        print(f"\n== {m2} - {m1} per config (pooled 59) ==")
        for c in ORDER:
            d = (w.xs(c, level="config")[m2] - w.xs(c, level="config")[m1]).to_numpy()
            print(f"   {c:>15} {d.mean():+.3f}  CI {boot_ci(d)}  p={wilcoxon(d).pvalue:.4f}")


if __name__ == "__main__":
    main()
