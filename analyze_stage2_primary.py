"""Primary-resource stage 2 vs union stage 2, llm-full and oracle (all n:1-neutral, 41 pairs).
Usage: python analyze_stage2_primary.py"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

UNION = "union[def]"
COMPARE = [("primary[rank1]", UNION), ("primary[sum_conf]", UNION), ("primary[coverage]", UNION),
           ("primary[coverage]", "llm-full+dict"), ("oracle+dict", "primary[coverage]")]


def load() -> pd.DataFrame:
    prim = pd.read_csv("results/stage2_primary.csv")
    rich = pd.read_csv("results/stage1_rich.csv")
    union = rich[rich.config == "two-stage+dict[def]"].assign(config=UNION)
    base = pd.read_csv("results/n40_neutral.csv").rename(columns={"R@GT": "R@GT_neutral", "F1": "F1_neutral"})
    base = base[base.config.isin(["llm-full+dict", "oracle+dict"])]
    cols = ["pair", "config", "resource", "R@GT_neutral", "F1_neutral"]
    return pd.concat([prim, union[cols + ["prompt_tokens", "sec"]], base[cols]], ignore_index=True)


def main():
    df = load()
    order = ["llm-full+dict", UNION, "primary[rank1]", "primary[sum_conf]", "primary[coverage]",
             "primary[best]", "oracle+dict"]
    print("== mean, 41 pairs (n:1-neutral) ==")
    print(df.groupby("config")[["R@GT_neutral", "F1_neutral", "prompt_tokens", "sec"]].mean().loc[order]
          .round(3).to_string())
    prim = df[df.config.str.startswith("primary")]
    print("\n== chosen resource is the right one ==")
    print(prim.groupby("config")["chosen_right"].agg(["sum", "count"]).to_string())
    print("\n== wrong choices (chosen resource) ==")
    wrong = prim[(~prim.chosen_right.astype(bool)) & prim.hit.astype(bool)]
    print(wrong.groupby("config")["chosen"].value_counts().to_string())
    for metric in ("R@GT_neutral", "F1_neutral"):
        wide = df.pivot_table(index="pair", columns="config", values=metric)
        print(f"\n== paired {metric}, n={len(wide)} ==")
        for a, b in COMPARE:
            d = (wide[a] - wide[b]).to_numpy()
            p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
            print(f"{a:>18} - {b:<18} mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
                  f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.4f}")
    print("\n== R@GT_neutral by primary resource ==")
    print(df.pivot_table(index="resource", columns="config", values="R@GT_neutral")[order]
          .assign(n=df[df.config == "oracle+dict"].groupby("resource").size()).round(2).to_string())


if __name__ == "__main__":
    main()
