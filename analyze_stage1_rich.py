"""Analysis of the stage-1 catalog ablation (results/stage1_rich.csv). Usage: python analyze_stage1_rich.py"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

BASE = "two-stage+dict[short]"


def main():
    df = pd.read_csv("results/stage1_rich.csv")
    order = list(dict.fromkeys(df.config))
    print("== mean, 41 pairs (n:1-neutral) ==")
    print(df.groupby("config")[["hit", "hit@1", "R@GT_neutral", "F1_neutral", "stage1_prompt_tokens",
                                "prompt_tokens", "sec"]].mean().loc[order].round(3).to_string())
    print("\n== the 7 pairs missed by [short]: picks per variant ==")
    m = df[df.missed_before].pivot_table(index=["pair", "resource"], columns="config", values="picked",
                                         aggfunc="first")[order]
    print(m.to_string())
    print("\n== stage-1 hit on the 7 / on the other 34 ==")
    print(df.pivot_table(index="config", columns="missed_before", values="hit").loc[order].round(3).to_string())
    print("\n== R@GT_neutral on the 7 ==")
    print(df[df.missed_before].groupby("config")["R@GT_neutral"].mean().loc[order].round(3).to_string())
    wide = df.pivot_table(index="pair", columns="config", values="R@GT_neutral")
    print(f"\n== paired R@GT_neutral vs {BASE}, n={len(wide)} ==")
    for c in order[1:]:
        d = (wide[c] - wide[BASE]).to_numpy()
        p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
        print(f"{c:>26}  mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
              f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.4f}")
    print("\n== new stage-1 misses (hit under [short], miss under variant) ==")
    hit = df.pivot_table(index="pair", columns="config", values="hit")
    for c in order[1:]:
        lost = hit.index[(hit[BASE] == 1) & (hit[c] == 0)].tolist()
        print(f"{c:>26}: {lost}")


if __name__ == "__main__":
    main()
