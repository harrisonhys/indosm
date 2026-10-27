"""Ablation: does giving the SOURCE TABLE NAME help on the large FHIR target (289 elements)?

All configs use the abbreviation dictionary (the table name is shown as e.g. "reg_periksa (registrasi periksa)").
  llm-full+dict            no table name            (= earlier run, cache hits)
  llm-full+dict+table      table name in the prompt
  two-stage+dict           no table name            (= earlier run, cache hits)
  two-stage+dict+t1        table name in stage 1 (resource selection) only
  two-stage+dict+t12       table name in stage 1 and stage 2
Writes results/ablation_table.csv. Usage: python ablation_table.py
"""
import json
import pathlib

import pandas as pd

from hybrid import CACHE, columns, llm_full
from pilot import f1_one_to_one, recall_at_gt
from two_stage import LARGE_PAIRS, two_stage


def table_name(schema: str) -> str:
    return schema.split("__", 1)[1]  # khanza__reg_periksa -> reg_periksa


def run_pair(p: dict) -> list[dict]:
    src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
    table, right = table_name(p["source"]), p["gt"][0][1].split(".")[0]
    rows = []

    def add(config, scores, use, picked=None):
        rows.append({"pair": p["id"].removesuffix("L"), "table": table, "config": config,
                     "R@GT": recall_at_gt(scores, gt), "F1": f1_one_to_one(scores, gt),
                     "picked": "|".join(picked) if picked is not None else "",
                     "hit": right in picked if picked is not None else None,
                     "hit@1": bool(picked) and picked[0] == right if picked is not None else None,
                     "prompt_tokens": use["prompt_tokens"], "completion_tokens": use["completion_tokens"],
                     "sec": use.get("sec", 0.0)})

    for config, tbl in (("llm-full+dict", None), ("llm-full+dict+table", table)):
        scores, use = llm_full(src, tgt, True, table=tbl)
        add(config, scores, use)
    for config, t1, t2 in (("two-stage+dict", None, None), ("two-stage+dict+t1", table, None),
                           ("two-stage+dict+t12", table, table)):
        scores, picked, r1, r2 = two_stage(src, tgt, True, table1=t1, table2=t2)
        use = {k: r1.get(k, 0) + r2.get(k, 0) for k in ("prompt_tokens", "completion_tokens", "sec")}
        add(config, scores, use, picked)
    return rows


def main():
    n_cached = len(json.loads(CACHE.read_text()))
    rows = []
    for p in json.loads(LARGE_PAIRS.read_text()):
        rows += run_pair(p)
        print(f"done {p['id']}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/ablation_table.csv", index=False)
    print(f"new LLM calls: {len(json.loads(CACHE.read_text())) - n_cached}")
    print(df.groupby("config", sort=False)[["R@GT", "F1", "hit", "hit@1", "prompt_tokens", "sec"]].mean().round(3))


if __name__ == "__main__":
    main()
