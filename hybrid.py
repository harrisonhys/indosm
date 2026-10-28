"""Hybrid schema matcher: bge-m3 top-k retrieval -> Qwen3-8B rerank, with optional abbreviation expansion.

2x2 ablation on sub-set E: {full-table LLM, hybrid} x {raw names, + Khanza abbreviation dictionary},
plus the embedding-only retrievers. Writes results/hybrid_scores<tag>_k<k>.csv and results/retrieval_recall<tag>.csv.
Usage: python hybrid.py [k] [pairs.json] [tag]
"""
import json
import os
import pathlib
import re
import sys
import time

import pandas as pd
import requests

from pilot import OLLAMA, f1_one_to_one, recall_at_gt

LOCAL_MODEL = "qwen3:8b"
# INDOSM_LLM=neuralwatt:<model id> switches every LLM call to that OpenAI-compatible API (key in NEURALWATT_API_KEY,
# never in the repo) with its own cache file; unset = local Ollama qwen3:8b, byte-identical to all earlier runs.
REMOTE = os.environ.get("INDOSM_LLM", "").removeprefix("neuralwatt:") or None
NEURALWATT = "https://api.neuralwatt.com/v1"
SCHEMAS = pathlib.Path("data/subset_e/schemas")
PAIRS = pathlib.Path("data/subset_e/pairs_e.json")
CACHE = pathlib.Path(f"data/hybrid_cache__{REMOTE}.json" if REMOTE else "data/hybrid_cache.json")
ABBREV = {k: v["expansion"] for k, v in json.loads(pathlib.Path("data/abbrev_khanza.json").read_text()).items()}
K_LIST = (1, 3, 5, 10)
MAX_OUTPUT_TOKENS = 3000  # ponytail: guards against repetition loops; normal answers are <1k tokens


# ---------- column text ----------

def words(name: str) -> list[str]:
    name = re.sub(r"\[x\]", "", name)
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)  # camelCase
    return [w for w in re.split(r"[^A-Za-z0-9]+", name.lower()) if w]


def text(name: str, use_dict: bool) -> str:
    return " ".join(ABBREV.get(w, w) if use_dict else w for w in words(name))


def label(name: str, use_dict) -> str:
    """Column as shown to the LLM: raw name, plus the abbreviation expansion when the dictionary changed it.

    use_dict may also be an ID->EN glossary (dict): then the English gloss of the expanded words is appended,
    e.g. "rujuk_ke (EN: refer to)" or "tgl_rujuk (tanggal rujuk = EN: date refer)".
    """
    raw, exp = " ".join(words(name)), text(name, True)
    shown = f"{name} ({exp})" if use_dict and exp != raw else name
    if not isinstance(use_dict, dict):
        return shown
    en = " ".join(use_dict.get(w, w) for w in exp.split())
    if en == exp:
        return shown
    return f"{name} ({exp} = EN: {en})" if exp != raw else f"{name} (EN: {en})"


# ---------- models ----------

def embed(texts: list[str]) -> list[list[float]]:
    for attempt in range(3):  # the Ollama bge-m3 runner occasionally dies (HTTP 400 "tokenize: EOF") and restarts
        r = requests.post(f"{OLLAMA}/embed", json={"model": "bge-m3", "input": texts}, timeout=300)
        if r.ok:
            return r.json()["embeddings"]
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()


def remote_llm(prompt: str) -> dict:
    body = {"model": REMOTE, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "seed": 0,
            "response_format": {"type": "json_object"}, "reasoning_effort": "low", "max_tokens": 16000}
    headers = {"Authorization": f"Bearer {os.environ['NEURALWATT_API_KEY']}"}
    t0 = time.time()
    for attempt in range(6):
        r = requests.post(f"{NEURALWATT}/chat/completions", json=body, headers=headers, timeout=600)
        if r.status_code not in (429, 500, 502, 503, 504):
            break
        time.sleep(min(60, 5 * 2 ** attempt))
    r.raise_for_status()
    j = r.json()
    content = (j["choices"][0]["message"].get("content") or "").strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)  # some models fence JSON despite json mode
    u = j.get("usage", {})
    return {"content": content, "prompt_tokens": u.get("prompt_tokens", 0),
            "completion_tokens": u.get("completion_tokens", 0),
            "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
            "finish_reason": j["choices"][0].get("finish_reason"), "sec": time.time() - t0}


def cached_llm(prompt: str) -> dict:
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    key = f"{REMOTE or LOCAL_MODEL}|{prompt}"
    if key not in cache and REMOTE:
        cache[key] = remote_llm(prompt)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    if key not in cache:
        body = {"model": LOCAL_MODEL, "messages": [{"role": "user", "content": prompt}], "format": "json",
                "think": False, "stream": False, "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": MAX_OUTPUT_TOKENS}}
        t0 = time.time()
        r = requests.post(f"{OLLAMA}/chat", json=body, timeout=900)
        r.raise_for_status()
        j = r.json()
        cache[key] = {"content": j["message"]["content"], "prompt_tokens": j.get("prompt_eval_count", 0),
                      "completion_tokens": j.get("eval_count", 0), "sec": time.time() - t0}
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    return cache[key]


def parse_matches(content: str, src: list[str], tgt: list[str], use_dict: bool) -> list[tuple[str, str, float]]:
    """LLM answers -> (source, target, confidence) with real column names.

    With the dictionary on, the model often echoes the shown label ("kd_dokter (kode dokter)") instead of the bare
    name, so labels are mapped back; anything that is neither a name nor a label is dropped.
    """
    try:
        out = json.loads(content)
    except json.JSONDecodeError:
        return []
    out = out.get("matches", []) if isinstance(out, dict) else out
    s_of = {label(c, use_dict): c for c in src} | {c: c for c in src}
    t_of = {label(c, use_dict): c for c in tgt} | {c: c for c in tgt}
    return [(s_of[m["source"]], t_of[m["target"]], float(m.get("confidence") or 1)) for m in out
            if isinstance(m, dict) and m.get("source") in s_of and m.get("target") in t_of]


# ---------- matchers: each returns (scores, usage) ----------

def similarity(src: list[str], tgt: list[str], use_dict: bool) -> dict:
    ea, eb = embed([text(c, use_dict) for c in src]), embed([text(c, use_dict) for c in tgt])
    return {(a, b): sum(x * y for x, y in zip(va, vb)) for a, va in zip(src, ea) for b, vb in zip(tgt, eb)}


def top_k(sim: dict, src: list[str], k: int) -> dict[str, list[str]]:
    return {s: [t for (_, t) in sorted(((v, t) for (a, t), v in sim.items() if a == s), reverse=True)[:k]] for s in src}


INSTRUCTION = ("You are a data-integration engineer doing schema matching. Find 1:1 correspondences between "
               "columns of the SOURCE and TARGET schemas (same real-world attribute, possibly different naming or "
               "language). Leave a source column unmatched if nothing fits.\n")
OUTPUT = 'Return JSON: {"matches": [{"source": <exact source name>, "target": <exact target name>, "confidence": <0..1>}]}'


def llm_full(src, tgt, use_dict, k=None, table=None):
    """table: optional source table name; when None the prompt is byte-identical to earlier runs (cache hits)."""
    lines = lambda cols: "\n".join(f"- {label(c, use_dict)}" for c in cols)
    head = f"SOURCE table: {label(table, use_dict)}\n" if table else ""
    prompt = f"{INSTRUCTION}{head}SOURCE:\n{lines(src)}\n\nTARGET:\n{lines(tgt)}\n\n{OUTPUT}"
    res = cached_llm(prompt)
    return {(s, t): c for s, t, c in parse_matches(res["content"], src, tgt, use_dict)}, res


def llm_rerank(src, tgt, use_dict, k):
    cands = top_k(similarity(src, tgt, use_dict), src, k)
    block = "\n".join(f"- {label(s, use_dict)}\n  candidates: " + "; ".join(label(t, use_dict) for t in cands[s])
                      for s in src)
    prompt = (f"{INSTRUCTION}For each SOURCE column you are given its {k} most similar TARGET candidates; pick the "
              f"single correct candidate or leave it unmatched.\n\n{block}\n\n{OUTPUT}")
    res = cached_llm(prompt)
    return {(s, t): c for s, t, c in parse_matches(res["content"], src, tgt, use_dict) if t in cands[s]}, res


def embedding_only(src, tgt, use_dict, k=None):
    return similarity(src, tgt, use_dict), {"prompt_tokens": 0, "completion_tokens": 0}


CONFIGS = {
    "emb": (embedding_only, False), "emb+dict": (embedding_only, True),
    "llm-full": (llm_full, False), "llm-full+dict": (llm_full, True),
    "hybrid": (llm_rerank, False), "hybrid+dict": (llm_rerank, True),
}


def columns(name: str) -> list[str]:
    return [c["name"] for c in json.loads((SCHEMAS / f"{name}.json").read_text())["columns"]]


def retrieval_recall(pairs) -> pd.DataFrame:
    rows = []
    for p in pairs:
        src, tgt, gt = columns(p["source"]), columns(p["target"]), [tuple(x) for x in p["gt"]]
        for use_dict in (False, True):
            ranked = top_k(similarity(src, tgt, use_dict), src, max(K_LIST))
            for k in K_LIST:
                rows.append({"pair": p["id"], "group": p["group"], "dict": use_dict, "k": k,
                             "recall@k": sum(t in ranked[s][:k] for s, t in gt) / len(gt)})
    return pd.DataFrame(rows)


def main(k: int = 5, pairs_file: str = str(PAIRS), tag: str = ""):
    pairs = json.loads(pathlib.Path(pairs_file).read_text())
    pathlib.Path("results").mkdir(exist_ok=True)
    rr = retrieval_recall(pairs)
    rr.to_csv(f"results/retrieval_recall{tag}.csv", index=False)
    print(rr.pivot_table(index=["group"], columns=["dict", "k"], values="recall@k").round(2).to_string(), flush=True)
    rows = []
    for p in pairs:
        src, tgt, gt = columns(p["source"]), columns(p["target"]), {tuple(x) for x in p["gt"]}
        for name, (fn, use_dict) in CONFIGS.items():
            scores, use = fn(src, tgt, use_dict, k)
            rows.append({"pair": p["id"], "group": p["group"], "lang": p["lang"], "config": name, "k": k,
                         "R@GT": recall_at_gt(scores, gt), "F1": f1_one_to_one(scores, gt),
                         "prompt_tokens": use["prompt_tokens"], "completion_tokens": use["completion_tokens"],
                         "sec": use.get("sec", 0.0)})
        print(f"done {p['id']}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"results/hybrid_scores{tag}_k{k}.csv", index=False)
    for metric in ("R@GT", "F1"):
        print(f"\n== {metric} (k={k}) ==")
        print(df.pivot_table(index="config", columns="group", values=metric).round(3).to_string())


if __name__ == "__main__":
    # ponytail: self-check of the text normaliser; scoring code is checked in pilot.py
    assert words("dispenseRequest.quantity") == ["dispense", "request", "quantity"]
    assert words("value[x]") == ["value"]
    assert text("nm_pasien", True) == "nama pasien" and text("nm_pasien", False) == "nm pasien"
    echoed = '{"matches": [{"source": "nm_pasien (nama pasien)", "target": "name", "confidence": 0.9}]}'
    assert parse_matches(echoed, ["nm_pasien"], ["name"], True) == [("nm_pasien", "name", 0.9)]
    args = sys.argv[1:]
    main(int(args[0]) if args else 5, *args[1:])
