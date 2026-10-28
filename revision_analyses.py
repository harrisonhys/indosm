"""Analyses requested by the IJCCS review (all from cache; asserts 0 new LLM calls). Run once per model:
  python revision_analyses.py                                   # Qwen3-8B (local cache)
  INDOSM_LLM=neuralwatt:glm-5.3-flash python revision_analyses.py   # GLM (its own cache)
Writes results/revision__<model>.csv (per table x config: threshold-free P/R/F1, R@GT, Encounter share) and
prints stage-1 diagnostics. Threshold-free = every prediction with confidence > 0, greedy one-to-one assignment by
confidence, no knowledge of |GT| (pilot.f1_one_to_one), n:1-neutral.
"""
import json

import pandas as pd

from ablation_gloss import SMALL_PAIRS
from draft_confirm import OUT as CONF_SMALL, OUT_LARGE as CONF_LARGE
from hybrid import CACHE, LOCAL_MODEL, REMOTE, columns, llm_full
from pilot import recall_at_gt
from rescore_n40 import neutral
from stage1_rich import catalogs
from two_stage import LARGE_PAIRS, select_resources, two_stage


def assign(scores: dict) -> set:
    """Greedy one-to-one assignment by confidence, same rule as pilot.f1_one_to_one."""
    used_s, used_t, out = set(), set(), set()
    for s, t in sorted((k for k, v in scores.items() if v > 0), key=scores.get, reverse=True):
        if s not in used_s and t not in used_t:
            out.add((s, t)); used_s.add(s); used_t.add(t)
    return out


def prf(scores: dict, gt: set) -> tuple[float, float, float]:
    pred = assign(scores)
    tp = len(pred & gt)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gt)
    return p, r, 2 * p * r / (p + r) if p + r else 0.0


def enc_share(scores: dict, gt: set) -> float:
    top = sorted(scores, key=scores.get, reverse=True)[: len(gt)]
    return sum(t.startswith("Encounter.") for _, t in top) / max(len(top), 1)


def main():
    model, cat, rows = REMOTE or LOCAL_MODEL, catalogs()["def"], []
    n0 = len(json.loads(CACHE.read_text()))
    for set_name, large_f, small_f in (("dev41", LARGE_PAIRS, SMALL_PAIRS), ("confirm18", CONF_LARGE, CONF_SMALL)):
        small = {p["id"]: p for p in json.loads(small_f.read_text())}
        for p in json.loads(large_f.read_text()):
            pid = p["id"].removesuffix("L")
            src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
            right = p["gt"][0][1].split(".")[0]
            picked, _ = select_resources(src, True, catalog=cat)
            runs = {"llm-full": llm_full(src, tgt, True)[0],
                    "union": two_stage(src, tgt, True, catalog=cat)[0],
                    "primary": llm_full(src, [t for t in tgt if t.split(".")[0] == picked[0]], True)[0] if picked else {}}
            sp = small[pid]
            osc = {(s, f"{right}.{t}"): v for (s, t), v in llm_full(columns(sp["source"]), columns(sp["target"]), True)[0].items()}
            runs["oracle"] = osc
            for name, sc in runs.items():
                sc = neutral(sc, p)
                pr, rc, f1 = prf(sc, gt)
                rows.append({"model": model, "set": set_name, "pair": pid, "config": name, "resource": right,
                             "picked": "|".join(picked), "rank1": picked[0] if picked else "",
                             "hit@1": bool(picked) and picked[0] == right, "hit@3": right in picked,
                             "enc_picked": "Encounter" in picked, "P": pr, "R": rc, "F1": f1,
                             "R@GT": recall_at_gt(sc, gt), "enc_share": enc_share(sc, gt),
                             "n_pred": len(assign(sc)), "n_gt": len(gt)})
    assert len(json.loads(CACHE.read_text())) == n0, "must not call the LLM"
    df = pd.DataFrame(rows)
    df.to_csv(f"results/revision__{model.replace(':', '_')}.csv", index=False)

    print(f"== {model}: threshold-free P / R / F1 and R@GT (mean over tables) ==")
    print(df.groupby(["set", "config"], sort=False)[["P", "R", "F1", "R@GT", "n_pred", "n_gt"]].mean().round(3).to_string())
    one = df[df.config == "primary"]
    print("\n== stage 1: top-1 / top-3 (any of the 1-3 picks) ==")
    print(one.groupby("set")[["hit@1", "hit@3"]].agg(["sum", "count"]).to_string())
    print("\n== wrong rank-1: gold resource -> picked rank-1 (counts) ==")
    w = one[~one["hit@1"]]
    print(pd.crosstab(w.resource, w.rank1).to_string())
    print("\n== stage 2 conditioned on stage 1 (R@GT; primary vs oracle on the same tables) ==")
    piv = df.pivot_table(index=["set", "pair"], columns="config", values="R@GT")
    hit = one.set_index(["set", "pair"])["hit@1"]
    for flag in (True, False):
        sub = piv[hit == flag]
        print(f"  rank-1 {'correct' if flag else 'wrong  '}: n={len(sub):2d}  primary {sub.primary.mean():.3f}  "
              f"oracle {sub.oracle.mean():.3f}  llm-full {sub['llm-full'].mean():.3f}")
    print("\n== Encounter absorption, union target (def catalogue), dev41, gold resource != Encounter, gold resource picked ==")
    u = df[(df.config == "union") & (df.set == "dev41") & (df.resource != "Encounter") & df["hit@3"]]
    o = df[df.config == "oracle"].set_index(["set", "pair"])["R@GT"]
    u = u.assign(oracle=[o[("dev41", x)] for x in u.pair])
    print(u.groupby("enc_picked")[["enc_share", "R@GT", "oracle"]].agg(["mean", "count"]).round(3).to_string())


if __name__ == "__main__":
    main()
