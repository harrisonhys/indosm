"""Pilot experiment: classic (Valentine) vs embedding (bge-m3) vs LLM on Indonesian schema pairs.

Each pair in pairs.json is run in three language variants of the column names:
  id-id  original headers,  en-en  both sides translated,  id-en  target side translated.
Translations are hand-written in data/translations_en.json so they don't come from the model being evaluated.
LLM outputs are cached in data/llm_cache.json; set USE_GEMINI=1 to add the Gemini arm (free tier: 20 req/day).
"""
import json
import os
import pathlib
import sys
import time

import pandas as pd
import requests
from valentine import valentine_match
from valentine.algorithms import Coma, Cupid, JaccardDistanceMatcher, SimilarityFlooding

from tables import load

GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
LOCAL_MODEL = "qwen3:8b"
OLLAMA = "http://localhost:11434/api"
N_SAMPLES = 3
TRANSLATIONS = json.loads(pathlib.Path("data/translations_en.json").read_text())
LLM_CACHE = pathlib.Path("data/llm_cache.json")
RESULTS = pathlib.Path("results")


def gemini(prompt: str) -> str:
    key = os.environ["GEMINI_API_KEY"]
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    for attempt in range(5):
        r = requests.post(GEMINI_URL, headers={"x-goog-api-key": key}, json=body, timeout=120)
        if r.status_code in (500, 503):
            time.sleep(2 ** attempt * 5)
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError(f"Gemini kept failing: {r.status_code} {r.text[:200]}")


def local_llm(prompt: str) -> str:
    body = {"model": LOCAL_MODEL, "messages": [{"role": "user", "content": prompt}], "format": "json",
            "think": False, "stream": False, "options": {"temperature": 0, "seed": 0, "num_ctx": 8192}}
    r = requests.post(f"{OLLAMA}/chat", json=body, timeout=600)
    r.raise_for_status()
    return r.json()["message"]["content"]


def cached(path: pathlib.Path, key: str, fn):
    cache = json.loads(path.read_text()) if path.exists() else {}
    if key not in cache:
        cache[key] = fn()
        path.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    return cache[key]


def translate(cols: list[str]) -> dict[str, str]:
    return {c: TRANSLATIONS[c] for c in cols}  # KeyError = column missing from the hand-written file


# ---------- matchers: each returns {(src_col, tgt_col): score} ----------

def classic(matcher):
    def run(a: pd.DataFrame, b: pd.DataFrame):
        res = valentine_match([a, b], matcher, df_names=["s", "t"])
        return {(p.source_column, p.target_column): s for p, s in res.items()}
    return run


def embed(texts: list[str]) -> list[list[float]]:
    r = requests.post(f"{OLLAMA}/embed", json={"model": "bge-m3", "input": texts}, timeout=120)
    r.raise_for_status()
    return r.json()["embeddings"]  # already L2-normalised


def col_text(df: pd.DataFrame, c: str) -> str:
    vals = df[c].dropna().astype(str).head(N_SAMPLES).tolist()
    return f"{c}: {', '.join(vals)}"


def embedding(a, b):
    ea, eb = embed([col_text(a, c) for c in a.columns]), embed([col_text(b, c) for c in b.columns])
    return {(ca, cb): sum(x * y for x, y in zip(va, vb)) for ca, va in zip(a.columns, ea) for cb, vb in zip(b.columns, eb)}


def llm(model: str, call):
    def run(a, b):
        desc = lambda df: "\n".join(f"- {col_text(df, c)}" for c in df.columns)
        prompt = (
            "You are a data-integration engineer doing schema matching. Find 1:1 correspondences between columns of "
            "the SOURCE and TARGET tables (same real-world attribute, possibly different naming or language). "
            "Each column is listed as 'name: sample values'. Leave columns unmatched if nothing fits.\n"
            f"SOURCE:\n{desc(a)}\n\nTARGET:\n{desc(b)}\n\n"
            'Return JSON: {"matches": [{"source": <exact source name>, "target": <exact target name>, "confidence": <0..1>}]}'
        )
        out = cached(LLM_CACHE, f"{model}|{prompt}", lambda: json.loads(call(prompt)))
        out = out.get("matches", []) if isinstance(out, dict) else out
        return {(m["source"], m["target"]): float(m.get("confidence", 1)) for m in out
                if m.get("source") in a.columns and m.get("target") in b.columns}
    return run


MATCHERS = {
    "COMA": classic(Coma(use_instances=True)),
    "Cupid": classic(Cupid()),
    "SimFlood": classic(SimilarityFlooding()),
    "Jaccard": classic(JaccardDistanceMatcher()),
    "bge-m3": embedding,
    LOCAL_MODEL: llm(LOCAL_MODEL, local_llm),
    **({GEMINI_MODEL: llm(GEMINI_MODEL, gemini)} if os.environ.get("USE_GEMINI") else {}),
}


# ---------- metrics ----------

def recall_at_gt(scores: dict, gt: set) -> float:
    top = sorted(scores, key=scores.get, reverse=True)[: len(gt)]
    return len(set(top) & gt) / len(gt)


def f1_one_to_one(scores: dict, gt: set) -> float:
    used_s, used_t, pred = set(), set(), set()
    for s, t in sorted((k for k, v in scores.items() if v > 0), key=scores.get, reverse=True):
        if s not in used_s and t not in used_t:
            pred.add((s, t)); used_s.add(s); used_t.add(t)
    tp = len(pred & gt)
    return 0.0 if tp == 0 else 2 * tp / (len(pred) + len(gt))


def variant(a, b, gt, kind):
    if kind == "id-id":
        return a, b, gt
    tb = translate(list(b.columns))
    b2, gt2 = b.rename(columns=tb), {(s, tb[t]) for s, t in gt}
    if kind == "id-en":
        return a, b2, gt2
    ta = translate(list(a.columns))
    return a.rename(columns=ta), b2, {(ta[s], t) for s, t in gt2}


def main(pairs_file="pairs.json"):
    pairs = json.loads(pathlib.Path(pairs_file).read_text())
    rows = []
    for p in pairs:
        a, b = load(p["source"]), load(p["target"])
        gt = {tuple(x) for x in p["gt"]}
        missing = {s for s, _ in gt} - set(a.columns) | {t for _, t in gt} - set(b.columns)
        assert not missing, f"{p['id']}: GT columns not in tables: {missing}"
        for kind in ("id-id", "id-en", "en-en"):
            va, vb, vgt = variant(a, b, gt, kind)
            for name, fn in MATCHERS.items():
                t0 = time.time()
                try:
                    sc = fn(va, vb)
                except Exception as e:
                    print(f"{p['id']} {kind} {name} FAILED: {e}", file=sys.stderr)
                    continue
                rows.append({"pair": p["id"], "kind": p["kind"], "lang": kind, "method": name,
                             "R@GT": recall_at_gt(sc, vgt), "F1": f1_one_to_one(sc, vgt), "sec": time.time() - t0})
        print(f"done {p['id']}", flush=True)
    RESULTS.mkdir(exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "pilot_scores.csv", index=False)
    for metric in ("R@GT", "F1"):
        print(f"\n== mean {metric} over {df.pair.nunique()} pairs ==")
        print(df.pivot_table(index="method", columns="lang", values=metric, aggfunc="mean")[["id-id", "id-en", "en-en"]].round(3))


if __name__ == "__main__":
    # ponytail: self-check of the metric code; full pytest suite once the benchmark grows
    g = {("a", "x"), ("b", "y")}
    assert recall_at_gt({("a", "x"): .9, ("b", "x"): .8, ("b", "y"): .1}, g) == 0.5
    assert f1_one_to_one({("a", "x"): .9, ("b", "x"): .8, ("b", "y"): .1}, g) == 1.0
    assert f1_one_to_one({("a", "y"): .9}, g) == 0.0
    main(*sys.argv[1:])
