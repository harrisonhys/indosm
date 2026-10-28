"""Second-model arm: the four headline configs (llm-full+dict, union[def], primary[rank1], oracle+dict) on dev41 and
confirm18 with whatever backend hybrid.py is set to (INDOSM_LLM). Same prompts, same scoring (n:1-neutral).
Writes results/model2__<model>.csv. Usage: INDOSM_LLM=neuralwatt:glm-5.3-flash python run_model2.py
"""
import json

import pandas as pd

from ablation_gloss import SMALL_PAIRS
from draft_confirm import OUT as CONF_SMALL, OUT_LARGE as CONF_LARGE
from hybrid import CACHE, LOCAL_MODEL, REMOTE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from rescore_n40 import neutral
from stage1_rich import catalogs
from two_stage import LARGE_PAIRS, select_resources, two_stage

USE = ("prompt_tokens", "completion_tokens", "sec")


def add(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) + b.get(k, 0) for k in USE}


def main():
    model, cat, rows = REMOTE or LOCAL_MODEL, catalogs()["def"], []
    n0 = len(json.loads(CACHE.read_text())) if CACHE.exists() else 0
    for set_name, large_f, small_f in (("dev41", LARGE_PAIRS, SMALL_PAIRS), ("confirm18", CONF_LARGE, CONF_SMALL)):
        small = {p["id"]: p for p in json.loads(small_f.read_text())}
        for p in json.loads(large_f.read_text()):
            pid = p["id"].removesuffix("L")
            src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
            right = p["gt"][0][1].split(".")[0]
            sc, r = llm_full(src, tgt, True)
            runs = {"llm-full+dict": (sc, add(r, {}), None)}
            sc, picked, r1, r2 = two_stage(src, tgt, True, catalog=cat)
            runs["union[def]"] = (sc, add(r1, r2), picked)
            picked, r1 = select_resources(src, True, catalog=cat)
            sc, r2 = llm_full(src, [t for t in tgt if t.split(".")[0] == picked[0]], True) if picked else ({}, {})
            runs["primary[rank1]"] = (sc, add(r1, r2), picked)
            sp = small[pid]
            for name, (sc, use, pk) in runs.items():
                rows.append({"model": model, "set": set_name, "pair": pid, "config": name, "resource": right,
                             "R@GT_neutral": recall_at_gt(neutral(sc, p), gt),
                             "F1_neutral": f1_one_to_one(neutral(sc, p), gt), "picked": "|".join(pk or []),
                             "hit": float(right in pk) if pk is not None else None,
                             "hit@1": float(bool(pk) and pk[0] == right) if pk is not None else None} | use)
            osc, r = llm_full(columns(sp["source"]), columns(sp["target"]), True)
            ogt = {tuple(x) for x in sp["gt"]}
            rows.append({"model": model, "set": set_name, "pair": pid, "config": "oracle+dict", "resource": right,
                         "R@GT_neutral": recall_at_gt(neutral(osc, sp), ogt),
                         "F1_neutral": f1_one_to_one(neutral(osc, sp), ogt)} | add(r, {}))
            print(f"done {set_name} {pid}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"results/model2__{model.replace(':', '_')}.csv", index=False)
    print(f"new LLM calls: {len(json.loads(CACHE.read_text())) - n0}")
    print(df.groupby(["set", "config"], sort=False)[["R@GT_neutral", "F1_neutral", "hit@1", "prompt_tokens"]]
          .mean().round(3).to_string())


if __name__ == "__main__":
    main()
