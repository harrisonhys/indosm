"""Ablation: ID->EN domain-term glossary on top of the abbreviation dictionary, large FHIR target (289 elements).

Glossaries: manual (data/glossary_id_en_manual.json, Claude) and auto (data/glossary_id_en_qwen.json, Qwen3-8B).
  two-stage+dict            baseline (cache hits)
  two-stage+gloss@1         manual glossary in stage 1 only, stage 2 abbreviation dict only
  two-stage+gloss@12        manual glossary in both stages
  two-stage+qgloss@12       Qwen glossary in both stages
  llm-full+dict / +gloss / +qgloss    single prompt over all 289 elements
  oracle+dict / +gloss      right resource given (small target), isolates the stage-2 effect
No source table names anywhere. Writes results/ablation_gloss.csv. Usage: python ablation_gloss.py
"""
import json
import pathlib

import pandas as pd

from hybrid import CACHE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from two_stage import LARGE_PAIRS, two_stage

SMALL_PAIRS = pathlib.Path("data/subset_e/pairs_e.json")


def load_gloss(path: str) -> dict[str, str]:
    return {k: v for k, v in json.loads(pathlib.Path(path).read_text()).items() if not k.startswith("_")}


MANUAL = load_gloss("data/glossary_id_en_manual.json")
QWEN = load_gloss("data/glossary_id_en_qwen.json")


def row(pair_id, config, scores, gt, use, picked=None, right=None):
    return {"pair": pair_id, "config": config, "R@GT": recall_at_gt(scores, gt), "F1": f1_one_to_one(scores, gt),
            "picked": "|".join(picked) if picked is not None else "",
            "hit": (right in picked) if picked is not None else None,
            "hit@1": (bool(picked) and picked[0] == right) if picked is not None else None,
            "prompt_tokens": use.get("prompt_tokens", 0), "completion_tokens": use.get("completion_tokens", 0),
            "sec": use.get("sec", 0.0)}


def main():
    n_cached = len(json.loads(CACHE.read_text()))
    small = {p["id"]: p for p in json.loads(SMALL_PAIRS.read_text())}
    rows = []
    for p in json.loads(LARGE_PAIRS.read_text()):
        pid = p["id"].removesuffix("L")
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        right = p["gt"][0][1].split(".")[0]
        for config, d1, d2 in (("two-stage+dict", True, None), ("two-stage+gloss@1", MANUAL, True),
                               ("two-stage+gloss@12", MANUAL, None), ("two-stage+qgloss@12", QWEN, None)):
            scores, picked, r1, r2 = two_stage(src, tgt, d1, use_dict2=d2)
            use = {k: r1.get(k, 0) + r2.get(k, 0) for k in ("prompt_tokens", "completion_tokens", "sec")}
            rows.append(row(pid, config, scores, gt, use, picked, right))
        for config, d in (("llm-full+dict", True), ("llm-full+gloss", MANUAL), ("llm-full+qgloss", QWEN)):
            scores, use = llm_full(src, tgt, d)
            rows.append(row(pid, config, scores, gt, use))
        sp = small[pid]
        s_src, s_tgt, s_gt = columns(sp["source"]), columns(sp["target"]), {tuple(x) for x in sp["gt"]}
        for config, d in (("oracle+dict", True), ("oracle+gloss", MANUAL)):
            scores, use = llm_full(s_src, s_tgt, d)
            rows.append(row(pid, config, scores, s_gt, use))
        print(f"done {pid}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/ablation_gloss.csv", index=False)
    print(f"new LLM calls: {len(json.loads(CACHE.read_text())) - n_cached}")
    print(df.groupby("config", sort=False)[["R@GT", "F1", "hit", "hit@1", "prompt_tokens", "sec"]].mean().round(3))


if __name__ == "__main__":
    main()
