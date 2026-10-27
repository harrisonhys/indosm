"""Analysis of the stage-1 rank-1 ablation (results/stage1_primary_hint.csv). Usage: python analyze_stage1_primary_hint.py"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

BASE = "rank1[def|none]"


def test(wide: pd.DataFrame, a: str, b: str) -> str:
    d = (wide[a] - wide[b]).to_numpy()
    p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
    return f"mean {d.mean():+.3f}  95% CI {boot_ci(d)}  w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.4f}"


def main():
    df = pd.read_csv("results/stage1_primary_hint.csv")
    base = pd.read_csv("results/n40_neutral.csv").rename(columns={"R@GT": "R@GT_neutral", "F1": "F1_neutral"})
    ref = base[base.config.isin(["llm-full+dict", "oracle+dict"])]
    order = list(dict.fromkeys(df.config))
    print("== mean, 41 pairs (n:1-neutral) ==")
    print(df.groupby("config")[["hit", "hit@1", "R@GT_neutral", "F1_neutral", "prompt_tokens"]].mean().loc[order]
          .round(3).to_string())
    print("\n== hit@1 count; rank-1 resource when wrong ==")
    for c in order:
        x = df[df.config == c]
        print(f"{c:>24} hit@1 {int(x['hit@1'].sum())}/41  wrong rank1: "
              f"{x[~x['hit@1'].astype(bool)].picked.str.split('|').str[0].value_counts().to_dict()}")
    print("\n== hit@1 by right resource ==")
    print(df.pivot_table(index="resource", columns="config", values="hit@1", aggfunc="sum")[order]
          .assign(n=df[df.config == BASE].groupby("resource").size()).to_string())
    allc = pd.concat([df, ref], ignore_index=True)
    for metric in ("R@GT_neutral", "F1_neutral"):
        wide = allc.pivot_table(index="pair", columns="config", values=metric)
        print(f"\n== paired {metric}, n={len(wide)} ==")
        for c in order[1:]:
            print(f"{c:>24} - {BASE:<16} {test(wide, c, BASE)}")
        best = max(order, key=lambda c: wide[c].mean())
        print(f"{best:>24} - {'llm-full+dict':<16} {test(wide, best, 'llm-full+dict')}")
        print(f"{'oracle+dict':>24} - {best:<16} {test(wide, 'oracle+dict', best)}")
    print("\n== pairs whose rank-1 changed vs base ==")
    w = df.pivot_table(index=["pair", "resource"], columns="config", values="picked", aggfunc="first")[order]
    w = w.apply(lambda col: col.str.split("|").str[0])
    print(w[w.nunique(axis=1) > 1].to_string())


if __name__ == "__main__":
    main()
