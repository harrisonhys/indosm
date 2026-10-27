"""Analysis of the glossary ablation (results/ablation_gloss.csv). Usage: python analyze_ablation_gloss.py"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

ORDER = ["llm-full+dict", "llm-full+gloss", "llm-full+qgloss", "two-stage+dict", "two-stage+gloss@1",
         "two-stage+gloss@12", "two-stage+qgloss@12", "oracle+dict", "oracle+gloss"]
COMPARISONS = [("two-stage+gloss@1", "two-stage+dict"), ("two-stage+gloss@12", "two-stage+gloss@1"),
               ("two-stage+gloss@12", "two-stage+dict"), ("two-stage+qgloss@12", "two-stage+dict"),
               ("two-stage+gloss@12", "two-stage+qgloss@12"), ("llm-full+gloss", "llm-full+dict"),
               ("llm-full+qgloss", "llm-full+dict"), ("oracle+gloss", "oracle+dict"),
               ("two-stage+gloss@12", "llm-full+gloss"), ("oracle+gloss", "two-stage+gloss@12")]
FOCUS = ["E04", "E12", "E13"]  # pairs whose stage-1 choice failed in earlier runs


def main():
    df = pd.read_csv("results/ablation_gloss.csv")
    print("== mean over 15 pairs ==")
    print(df.groupby("config")[["R@GT", "F1", "prompt_tokens", "completion_tokens", "sec"]].mean().loc[ORDER]
          .round(3).to_string())
    ts = df[df.config.str.startswith("two-stage")]
    print("\n== stage 1 ==")
    print(ts.groupby("config")[["hit", "hit@1"]].mean().round(3).to_string())
    for metric in ("R@GT", "F1"):
        wide = df.pivot_table(index="pair", columns="config", values=metric)
        print(f"\n-- paired {metric}, n={len(wide)} --")
        for a, b in COMPARISONS:
            d = (wide[a] - wide[b]).to_numpy()
            p = wilcoxon(d).pvalue if np.any(d != 0) else 1.0
            print(f"{a:>20} - {b:<20} mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
                  f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p={p:.3f}")
    print("\n== per pair R@GT ==")
    print(df.pivot_table(index="pair", columns="config", values="R@GT")[ORDER].round(2).to_string())
    print("\n== stage-1 picks on earlier failures ==")
    print(ts[ts.pair.isin(FOCUS)].pivot_table(index="pair", columns="config", values="picked", aggfunc="first").to_string())


if __name__ == "__main__":
    main()
