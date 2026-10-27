"""Two-stage matcher for the large FHIR target: (1) LLM picks 1-3 FHIR resources from name + one-line
description, (2) full-table column matching against only the elements of the picked resources, either in one
prompt over their union or one prompt per resource (merged by confidence).

Compared with llm-full on all 289 elements and with the oracle (the right resource given = small target).
Neither stage sees the source table name, same as llm-full, so the only extra input is the resource descriptions.
Writes results/two_stage.csv. Usage: python two_stage.py
"""
import json
import pathlib

import pandas as pd

from hybrid import cached_llm, columns, label, llm_full
from pilot import f1_one_to_one, recall_at_gt

LARGE_PAIRS = pathlib.Path("data/subset_e/pairs_e_large.json")
RAW_FHIR = pathlib.Path("data/subset_e/raw/fhir")
MAX_RESOURCES = 3


def resource_catalog() -> dict[str, str]:
    out = {}
    for f in sorted(RAW_FHIR.glob("*.json")):
        sd = json.loads(f.read_text())
        out[sd["name"]] = sd["snapshot"]["element"][0]["short"]
    return out


CATALOG = resource_catalog()


def select_resources(src: list[str], use_dict: bool, table: str | None = None,
                     catalog: dict[str, str] | None = None, hint: str = "") -> tuple[list[str], dict]:
    """hint: extra instruction appended after the task line; empty keeps the prompt byte-identical."""
    catalog = catalog or CATALOG
    cols = "\n".join(f"- {label(c, use_dict)}" for c in src)
    head = f"SOURCE table: {label(table, use_dict)}\n" if table else ""
    res = "\n".join(f"- {name}: {desc}" for name, desc in catalog.items())
    prompt = (
        "You are a data-integration engineer mapping a hospital database table to HL7 FHIR R4. Given the columns of "
        f"one SOURCE table, choose the 1 to {MAX_RESOURCES} FHIR resources its columns would be mapped into, most "
        "likely first. Choose fewer when one resource clearly fits." + (f" {hint}" if hint else "") + "\n"
        f"{head}SOURCE columns:\n{cols}\n\nFHIR resources:\n{res}\n\n"
        'Return JSON: {"resources": [<resource name>, ...]}'
    )
    r = cached_llm(prompt)
    try:
        picked = json.loads(r["content"]).get("resources", [])
    except (json.JSONDecodeError, AttributeError):
        picked = []
    picked = [p for p in dict.fromkeys(picked) if p in CATALOG][:MAX_RESOURCES]
    return picked, r


NO_CALL = {"prompt_tokens": 0, "completion_tokens": 0, "sec": 0.0}


def two_stage(src: list[str], all_tgt: list[str], use_dict: bool, per_resource: bool = False,
              table1: str | None = None, table2: str | None = None, use_dict2=None, catalog=None):
    """Stage 2 either matches against the union of picked resources in one prompt, or (per_resource) runs one
    prompt per picked resource and merges, keeping the highest confidence per (source, target)."""
    picked, r1 = select_resources(src, use_dict, table1, catalog)
    groups = [[t for t in all_tgt if t.split(".")[0] == r] for r in picked] if per_resource \
        else [[t for t in all_tgt if t.split(".")[0] in picked]]
    scores, use = {}, dict(NO_CALL)
    for tgt in filter(None, groups):
        sc, r2 = llm_full(src, tgt, use_dict if use_dict2 is None else use_dict2, table=table2)
        for key, v in sc.items():
            scores[key] = max(v, scores.get(key, 0.0))
        use = {k: use[k] + r2.get(k, 0) for k in use}
    return scores, picked, r1, use


def main():
    rows = []
    for p in json.loads(LARGE_PAIRS.read_text()):
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        right = p["gt"][0][1].split(".")[0]
        for use_dict, per_resource in ((False, False), (True, False), (False, True), (True, True)):
            scores, picked, r1, r2 = two_stage(src, tgt, use_dict, per_resource)
            name = "two-stage" + ("-per-res" if per_resource else "") + ("+dict" if use_dict else "")
            rows.append({"pair": p["id"].removesuffix("L"), "config": name,
                         "R@GT": recall_at_gt(scores, gt), "F1": f1_one_to_one(scores, gt),
                         "picked": "|".join(picked), "right_resource": right,
                         "hit": right in picked, "hit@1": bool(picked) and picked[0] == right,
                         "n_targets": sum(t.split(".")[0] in picked for t in tgt), "stage2_calls": len(picked) if per_resource else 1,
                         "prompt_tokens": r1["prompt_tokens"] + r2["prompt_tokens"],
                         "completion_tokens": r1["completion_tokens"] + r2["completion_tokens"],
                         "stage1_tokens": r1["prompt_tokens"] + r1["completion_tokens"],
                         "sec": r1.get("sec", 0.0) + r2.get("sec", 0.0)})
        print(f"done {p['id']}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/two_stage.csv", index=False)
    print(df.groupby("config")[["R@GT", "F1", "hit", "hit@1", "n_targets", "prompt_tokens", "sec"]].mean().round(3))


if __name__ == "__main__":
    main()
