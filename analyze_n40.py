"""Analysis of the n=41 large-target run. Usage: python analyze_n40.py [results/n40.csv | results/n40_neutral.csv]"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

ORDER = ["llm-full+dict", "two-stage+dict", "two-stage+qgloss@12", "oracle+dict"]
COMPARISONS = [("two-stage+dict", "llm-full+dict"), ("two-stage+qgloss@12", "llm-full+dict"),
               ("two-stage+qgloss@12", "two-stage+dict"), ("oracle+dict", "two-stage+dict")]
OLD = {f"E{i:02d}" for i in range(1, 15)} | {"E20"}


def paired(df: pd.DataFrame, label: str):
    for metric in ("R@GT", "F1"):
        wide = df.pivot_table(index="pair", columns="config", values=metric)
        print(f"\n-- {label}: paired {metric}, n={len(wide)} --")
        for a, b in COMPARISONS:
            d = (wide[a] - wide[b]).to_numpy()
            p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
            print(f"{a:>20} - {b:<15} mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
                  f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.4f}")


def main():
    df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "results/n40.csv")
    df["subset"] = np.where(df.pair.isin(OLD), "old15", "new26")
    print("== mean, all 41 pairs ==")
    cols = [c for c in ("R@GT", "F1", "prompt_tokens", "completion_tokens", "sec") if c in df]
    print(df.groupby("config")[cols].mean().loc[ORDER].round(3).to_string())
    print("\n== R@GT by subset (old 15 must match earlier runs) ==")
    print(df.pivot_table(index="config", columns="subset", values="R@GT").loc[ORDER].round(3).to_string())
    ts = df[df.config.str.startswith("two-stage")]
    if "hit" in df:
        print("\n== stage 1 (two-stage configs) ==")
        print(ts.groupby(["config", "subset"])[["hit", "hit@1"]].mean().round(3).to_string())
    paired(df, "all 41")
    paired(df[df.pair != "E20"], "Khanza only (40)")
    print("\n== R@GT by primary resource ==")
    print(df.pivot_table(index="resource", columns="config", values="R@GT", aggfunc="mean")[ORDER]
          .assign(n=df[df.config == "oracle+dict"].groupby("resource").size()).round(2).to_string())
    if "hit" in df:
        print("\n== stage-1 misses (two-stage+dict) ==")
        miss = ts[(ts.config == "two-stage+dict") & (~ts.hit.astype(bool))]
        print(miss[["pair", "resource", "picked"]].to_string(index=False))


if __name__ == "__main__":
    main()
