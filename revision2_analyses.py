"""Second-round review analyses (run once per model, like revision_analyses.py):
  python revision2_analyses.py                                     # Qwen3-8B (local)
  INDOSM_LLM=neuralwatt:glm-5.3-flash python revision2_analyses.py # GLM (API; only cache misses are called)

Evaluation policies, fixed before computing any number (28 Oct 2026):
  annotation-neutral  predictions that the gold standard labels n:1 or ambiguous are removed before scoring
                      (the paper's earlier metric; measures the scorable subset, uses gold labels to filter).
  deployment-strict   no gold-based filtering. All parsed predictions with confidence > 0, greedy one-to-one
                      assignment by confidence; an assigned pair is a true positive iff it is a gold 1:1 pair, every
                      other assigned pair (including gold n:1 and ambiguous pairs) is a false positive; recall is
                      over gold 1:1 pairs. Lower bound on operational quality.
  deployment-lenient  same assignment; assigned pairs that are gold n:1 or ambiguous count as true positives
                      (acceptable to a reviewing engineer). Upper reference.
  P, R, F1 are computed per table and macro-averaged over tables (F1 is the mean of per-table F1, not the
  harmonic mean of mean P and mean R).

Experiments:
  oracle-A   gold resource, bare element names (`identifier`)                 = the paper's oracle
  oracle-B   gold resource, prefixed names (`MedicationRequest.identifier`)   = primary prompt when rank 1 is right
  emb-def / emb-defel  stage 1 by bge-m3 cosine between the table (expanded column names) and each resource's
             definition (+ element names); stage 2 = the same LLM primary prompt on the embedding's rank-1 resource.
Writes results/revision2__<model>.csv.
"""
import json

import pandas as pd

from ablation_gloss import SMALL_PAIRS
from draft_confirm import OUT as CONF_SMALL, OUT_LARGE as CONF_LARGE
from fhir_catalog import OUT as RICH
from hybrid import CACHE, LOCAL_MODEL, REMOTE, columns, embed, llm_full, text
from pilot import recall_at_gt
from revision_analyses import assign
from stage1_rich import catalogs
from two_stage import LARGE_PAIRS, select_resources, two_stage

RESOURCES = list(json.loads(RICH.read_text()))


def labels(p: dict) -> tuple[set, set]:
    one = {tuple(x) for x in p["gt"]}
    other = {(s, t) for s, t, *_ in p["gt_n1"] + p["ambiguous"]}
    return one, other


def scores_for(sc: dict, p: dict) -> dict:
    one, other = labels(p)
    pred = assign(sc)
    out = {}
    for name, tp_set, drop in (("neutral", one, other), ("strict", one, set()), ("lenient", one | other, set())):
        kept = {x for x in assign({k: v for k, v in sc.items() if k not in drop})} if drop else pred
        tp = len(kept & tp_set)
        prec = tp / len(kept) if kept else 0.0
        rec = len(kept & one) / len(one)  # recall is always over gold 1:1 pairs
        out[f"P_{name}"], out[f"R_{name}"] = prec, rec
        out[f"F1_{name}"] = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    out["R@GT_strict"] = recall_at_gt(sc, one)
    out["R@GT_neutral"] = recall_at_gt({k: v for k, v in sc.items() if k not in other}, one)
    return out


def embedding_ranker(variant: str):
    rich = json.loads(RICH.read_text())
    docs = {r: rich[r]["definition"] + ("" if variant == "def" else " Elements: " + ", ".join(rich[r]["elements"]))
            for r in RESOURCES}
    vecs = dict(zip(RESOURCES, embed([docs[r] for r in RESOURCES])))

    def rank(src: list[str]) -> list[str]:
        q = embed(["Database table with columns: " + ", ".join(text(c, True) for c in src)])[0]
        sim = {r: sum(a * b for a, b in zip(q, v)) for r, v in vecs.items()}
        return sorted(RESOURCES, key=sim.get, reverse=True)
    return rank


def main():
    model, cat, rows = REMOTE or LOCAL_MODEL, catalogs()["def"], []
    n0 = len(json.loads(CACHE.read_text()))
    rankers = {f"emb-{v}": embedding_ranker(v) for v in ("def", "defel")}
    for set_name, large_f, small_f in (("dev41", LARGE_PAIRS, SMALL_PAIRS), ("confirm18", CONF_LARGE, CONF_SMALL)):
        small = {p["id"]: p for p in json.loads(small_f.read_text())}
        for p in json.loads(large_f.read_text()):
            pid = p["id"].removesuffix("L")
            src, tgt = columns(p["source"]), columns(p["target"])
            right = p["gt"][0][1].split(".")[0]
            of = lambda r: [t for t in tgt if t.split(".")[0] == r]
            picked, _ = select_resources(src, True, catalog=cat)
            sp = small[pid]
            oa = {(s, f"{right}.{t}"): v for (s, t), v in llm_full(columns(sp["source"]), columns(sp["target"]), True)[0].items()}
            runs = {"llm-full": (llm_full(src, tgt, True)[0], None),
                    "union": (two_stage(src, tgt, True, catalog=cat)[0], picked[0] if picked else None),
                    "primary": (llm_full(src, of(picked[0]), True)[0] if picked else {}, picked[0] if picked else None),
                    "oracle-A": (oa, right), "oracle-B": (llm_full(src, of(right), True)[0], right)}
            for name, rank in rankers.items():
                r1 = rank(src)[0]
                runs[name] = (llm_full(src, of(r1), True)[0], r1)
            for name, (sc, r1) in runs.items():
                rows.append({"model": model, "set": set_name, "pair": pid, "config": name, "resource": right,
                             "rank1": r1, "hit@1": r1 == right if r1 else None} | scores_for(sc, p))
        print(f"done {set_name}, new LLM calls so far {len(json.loads(CACHE.read_text())) - n0}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"results/revision2__{model.replace(':', '_')}.csv", index=False)
    cols = ["R@GT_neutral", "R@GT_strict", "P_strict", "R_strict", "F1_strict", "F1_neutral", "F1_lenient", "hit@1"]
    print(df.astype({"hit@1": float}).groupby(["set", "config"], sort=False)[cols].mean().round(3).to_string())


if __name__ == "__main__":
    main()
