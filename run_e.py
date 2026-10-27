"""Schema-only baseline run on sub-set E (data/subset_e/pairs_e.json) -> results/subset_e_scores.csv.

Columns are given by name only (no types/descriptions) so every matcher sees the same input; only `gt` is scored.
"""
import json
import pathlib
import sys
import time

import pandas as pd

from ddl_pilot import empty
from pilot import MATCHERS, f1_one_to_one, recall_at_gt

SCHEMAS = pathlib.Path("data/subset_e/schemas")


def columns(name: str) -> list[str]:
    return [c["name"] for c in json.loads((SCHEMAS / f"{name}.json").read_text())["columns"]]


def main(pairs_file="data/subset_e/pairs_e.json"):
    rows = []
    for p in json.loads(pathlib.Path(pairs_file).read_text()):
        a, b, gt = empty(columns(p["source"])), empty(columns(p["target"])), {tuple(x) for x in p["gt"]}
        for m, fn in MATCHERS.items():
            t0 = time.time()
            try:
                sc = fn(a, b)
            except Exception as e:
                print(f"{p['id']} {m} FAILED: {e}", file=sys.stderr)
                continue
            rows.append({"pair": p["id"], "group": p["group"], "lang": p["lang"], "method": m,
                         "R@GT": recall_at_gt(sc, gt), "F1": f1_one_to_one(sc, gt), "sec": time.time() - t0})
        print(f"done {p['id']}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("results/subset_e_scores.csv", index=False)
    for metric in ("R@GT", "F1"):
        print(f"\n== mean {metric} by group ==")
        print(df.pivot_table(index="method", columns="group", values=metric, aggfunc="mean").round(3).to_string())
        print(df.pivot_table(index="method", columns="lang", values=metric, aggfunc="mean").round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:])
