"""Pre-registered analysis (PREREG_CONFIRM.md) of results/confirm.csv, plus labelled exploratory analyses.
Usage: python analyze_confirm.py"""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from analyze_hybrid import boot_ci

ORDER = ["llm-full+dict", "union[def]", "primary[rank1]", "oracle+dict"]
HYP = {"H1": ("primary[rank1]", "llm-full+dict"), "H2": ("primary[rank1]", "union[def]")}


def holm(ps: dict) -> dict:
    adj, running = {}, 0.0
    for i, (k, p) in enumerate(sorted(ps.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, (len(ps) - i) * p))
        adj[k] = running
    return adj


def diff(wide, a, b):
    d = (wide[a] - wide[b]).to_numpy()
    p = wilcoxon(d, alternative="greater").pvalue if np.any(d != 0) else 1.0
    return d, p


def n41() -> pd.DataFrame:
    """Same four configs on the 41 development pairs (for the pooled exploratory view)."""
    base = pd.read_csv("results/n40_neutral.csv").rename(columns={"R@GT": "R@GT_neutral", "F1": "F1_neutral"})
    base = base[base.config.isin(["llm-full+dict", "oracle+dict"])]
    rich = pd.read_csv("results/stage1_rich.csv")
    union = rich[rich.config == "two-stage+dict[def]"].assign(config="union[def]")
    hint = pd.read_csv("results/stage1_primary_hint.csv")
    rank1 = hint[hint.config == "rank1[def|none]"].assign(config="primary[rank1]")
    cols = ["pair", "config", "resource", "R@GT_neutral", "F1_neutral"]
    return pd.concat([base[cols], union[cols], rank1[cols]], ignore_index=True).assign(set="dev41")


def main():
    df = pd.read_csv("results/confirm.csv")
    print(f"== CONFIRMATORY (n={df.pair.nunique()}, R@GT n:1-neutral, one-sided Wilcoxon, Holm) ==")
    print(df.groupby("config")[["R@GT_neutral", "F1_neutral", "prompt_tokens"]].mean().loc[ORDER].round(3).to_string())
    print("median sec:", df.groupby("config")["sec"].median().loc[ORDER].round(1).to_dict())
    for metric in ("R@GT_neutral", "F1_neutral"):
        wide = df.pivot_table(index="pair", columns="config", values=metric)
        res = {h: diff(wide, a, b) for h, (a, b) in HYP.items()}
        adj = holm({h: p for h, (_, p) in res.items()})
        tag = "primary" if metric == "R@GT_neutral" else "secondary"
        print(f"\n-- {metric} ({tag}) --")
        for h, (d, p) in res.items():
            a, b = HYP[h]
            print(f"{h}: {a} - {b}  mean {d.mean():+.3f}  95% CI {boot_ci(d)}  "
                  f"w/t/l {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}  p1={p:.4f}  p_holm={adj[h]:.4f}")
        d = (wide["oracle+dict"] - wide["primary[rank1]"]).to_numpy()
        print(f"   (descriptive) oracle - primary[rank1]  mean {d.mean():+.3f}  95% CI {boot_ci(d)}")

    print("\n== EXPLORATORY ==")
    ts = df[df.config == "primary[rank1]"]
    print(f"stage 1: hit {int(ts.hit.sum())}/{len(ts)}, hit@1 {int(ts['hit@1'].sum())}/{len(ts)}")
    print(ts[["pair", "system", "resource", "picked", "R@GT_neutral"]].to_string(index=False))
    print("\nR@GT by system:")
    print(df.pivot_table(index="system", columns="config", values="R@GT_neutral")[ORDER]
          .assign(n=ts.groupby("system").size()).round(2).to_string())
    pooled = pd.concat([n41(), df.assign(set="confirm18")], ignore_index=True)
    wide = pooled.pivot_table(index="pair", columns="config", values="R@GT_neutral")
    print(f"\npooled dev41 + confirm18 (n={len(wide)}), two-sided:")
    for a, b in HYP.values():
        d = (wide[a] - wide[b]).to_numpy()
        print(f"   {a} - {b}  mean {d.mean():+.3f}  95% CI {boot_ci(d)}  p={wilcoxon(d).pvalue:.4f}")


if __name__ == "__main__":
    main()
