"""Correspondence-level analysis (exploratory; the pre-registered unit was the pair) of the four headline configs on
dev41 (pairs_e_large) and confirm18 (pairs_confirm_large), rebuilt from cache (asserts 0 new LLM calls).

Unit = one gt correspondence; hit = it is in the config's top-|GT| (R@|GT|, n:1-neutral). Micro recall per set.
Differences: cluster bootstrap over pairs (95% CI, 10k, seed 0) and a cluster sign-flip permutation test (two-sided),
so correlated correspondences inside one table are not treated as independent. Writes results/correspondence.csv.
Usage: python analyze_correspondence.py
"""
import json

import numpy as np
import pandas as pd

from draft_confirm import OUT as CONF_SMALL, OUT_LARGE as CONF_LARGE
from hybrid import CACHE, columns, llm_full
from rescore_n40 import neutral
from stage1_rich import catalogs
from two_stage import LARGE_PAIRS, select_resources, two_stage
from ablation_gloss import SMALL_PAIRS

CONFIGS = ["llm-full+dict", "union[def]", "primary[rank1]", "oracle+dict"]
COMPARE = [("primary[rank1]", "llm-full+dict"), ("primary[rank1]", "union[def]"), ("union[def]", "llm-full+dict")]
RNG_SEED, N_RESAMPLE = 0, 10_000


def top_hits(scores: dict, p: dict) -> set:
    gt = {tuple(x) for x in p["gt"]}
    sc = neutral(scores, p)
    return set(sorted(sc, key=sc.get, reverse=True)[: len(gt)]) & gt


def rows_for(large_file, small_file, set_name, cat):
    small = {p["id"]: p for p in json.loads(small_file.read_text())}
    out = []
    for p in json.loads(large_file.read_text()):
        pid = p["id"].removesuffix("L")
        src, tgt = columns(p["source"]), columns(p["target"])
        picked, _ = select_resources(src, True, catalog=cat)
        sp = small[pid]
        hits = {"llm-full+dict": top_hits(llm_full(src, tgt, True)[0], p),
                "union[def]": top_hits(two_stage(src, tgt, True, catalog=cat)[0], p),
                "primary[rank1]": top_hits(llm_full(src, [t for t in tgt if t.split(".")[0] == picked[0]], True)[0], p)}
        ohits = top_hits(llm_full(columns(sp["source"]), columns(sp["target"]), True)[0], sp)
        res = p["gt"][0][1].split(".")[0]
        for s, t in p["gt"]:
            r = {"set": set_name, "pair": pid, "source_col": s, "target": t, "resource": res}
            r |= {c: (s, t) in hits[c] for c in hits}
            r["oracle+dict"] = (s, t.split(".", 1)[1]) in ohits
            out.append(r)
    return out


def cluster_stats(df: pd.DataFrame, a: str, b: str):
    g = df.groupby("pair").agg(da=(a, "sum"), db=(b, "sum"), n=(a, "size"))
    d, n = (g.da - g.db).to_numpy(), g.n.to_numpy()
    obs = d.sum() / n.sum()
    rng = np.random.default_rng(RNG_SEED)
    idx = rng.integers(0, len(g), (N_RESAMPLE, len(g)))
    boot = d[idx].sum(1) / n[idx].sum(1)
    flips = rng.choice([-1, 1], (N_RESAMPLE, len(g)))
    perm = (flips * d).sum(1) / n.sum()
    p = (np.sum(np.abs(perm) >= abs(obs) - 1e-12) + 1) / (N_RESAMPLE + 1)
    return obs, np.percentile(boot, [2.5, 97.5]), p


def main():
    n0, cat = len(json.loads(CACHE.read_text())), catalogs()["def"]
    df = pd.DataFrame(rows_for(LARGE_PAIRS, SMALL_PAIRS, "dev41", cat) + rows_for(CONF_LARGE, CONF_SMALL, "confirm18", cat))
    assert len(json.loads(CACHE.read_text())) == n0, "must not call the LLM"
    df.to_csv("results/correspondence.csv", index=False)
    for name, sub in (("dev41", df[df.set == "dev41"]), ("confirm18", df[df.set == "confirm18"]), ("pooled59", df)):
        print(f"\n== {name}: {sub.pair.nunique()} pairs, {len(sub)} correspondences; micro recall ==")
        print("  " + "  ".join(f"{c} {sub[c].mean():.3f}" for c in CONFIGS))
        for a, b in COMPARE:
            obs, ci, p = cluster_stats(sub, a, b)
            print(f"  {a:>15} - {b:<14} {obs:+.3f}  cluster-boot CI [{ci[0]:+.3f}, {ci[1]:+.3f}]  perm p={p:.4f}")


if __name__ == "__main__":
    main()
