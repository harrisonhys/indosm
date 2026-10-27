"""Re-run on the enlarged large-target set (40 Khanza->FHIR pairs + E20 OpenSID->FHIR = 41 pairs, 289 elements).

Configs: llm-full+dict, two-stage+dict, two-stage+qgloss@12 (Qwen glossary in both stages) on the large target,
plus oracle+dict (right resource given) as the stage-2 ceiling. The 15 original pairs hit the cache, so their
numbers are identical to the earlier runs. Writes results/n40.csv. Usage: python run_n40.py
"""
import json

import pandas as pd

from ablation_gloss import QWEN, SMALL_PAIRS, row
from hybrid import CACHE, columns, llm_full
from two_stage import LARGE_PAIRS, two_stage


def main():
    n_cached = len(json.loads(CACHE.read_text()))
    small = {p["id"]: p for p in json.loads(SMALL_PAIRS.read_text())}
    rows = []
    for p in json.loads(LARGE_PAIRS.read_text()):
        pid = p["id"].removesuffix("L")
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        right = p["gt"][0][1].split(".")[0]
        scores, use = llm_full(src, tgt, True)
        rows.append(row(pid, "llm-full+dict", scores, gt, use) | {"resource": right})
        for config, d in (("two-stage+dict", True), ("two-stage+qgloss@12", QWEN)):
            scores, picked, r1, r2 = two_stage(src, tgt, d)
            use = {k: r1.get(k, 0) + r2.get(k, 0) for k in ("prompt_tokens", "completion_tokens", "sec")}
            rows.append(row(pid, config, scores, gt, use, picked, right) | {"resource": right})
        sp = small[pid]
        scores, use = llm_full(columns(sp["source"]), columns(sp["target"]), True)
        rows.append(row(pid, "oracle+dict", scores, {tuple(x) for x in sp["gt"]}, use) | {"resource": right})
        print(f"done {pid}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/n40.csv", index=False)
    print(f"new LLM calls: {len(json.loads(CACHE.read_text())) - n_cached}")
    print(df.groupby("config", sort=False)[["R@GT", "F1", "hit", "hit@1", "prompt_tokens", "sec"]].mean().round(3))


if __name__ == "__main__":
    main()
