"""Automatic ID->EN glossary: Qwen3-8B translates every token of the large-target source tables (same token list
as the manual glossary), in batches, with no knowledge of FHIR or the pairs.

Writes data/glossary_id_en_qwen.json. Usage: python auto_glossary.py
"""
import json
import pathlib

from hybrid import cached_llm

TOKENS = pathlib.Path("data/domain_terms_tokens.json")
OUT = pathlib.Path("data/glossary_id_en_qwen.json")
BATCH = 50


def translate(batch: list[str]) -> dict[str, str]:
    prompt = (
        "These are words taken from column names of Indonesian information systems (hospital, village "
        "administration). Some are glued compounds or English words. Give each a short English gloss of 1-4 words "
        "as used in such systems. Keep English words unchanged.\n"
        f"Words: {json.dumps(batch, ensure_ascii=False)}\n"
        'Return JSON: {"glossary": {<word>: <english gloss>}}'
    )
    try:
        out = json.loads(cached_llm(prompt)["content"]).get("glossary", {})
    except (json.JSONDecodeError, AttributeError):
        out = {}
    return {w: str(out[w]).strip() for w in batch if isinstance(out.get(w), str) and out[w].strip()}


def main():
    toks = json.loads(TOKENS.read_text())["tokens"]
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    done = set(prev.get("_translated", [t for t in toks if t in prev]))  # tokens already sent to the model
    todo = [t for t in toks if t not in done and t not in prev]
    gloss = {k: v for k, v in prev.items() if not k.startswith("_")}
    for i in range(0, len(todo), BATCH):  # only new tokens, so earlier glosses (and results) stay fixed
        gloss |= translate(todo[i:i + BATCH])
    gloss = {w: g for w, g in gloss.items() if g.lower() != w.lower()}  # identity entries are no-ops
    OUT.write_text(json.dumps({"_note": "Qwen3-8B, temp 0, batches of 50; identity glosses dropped; extended "
                               "incrementally (new tokens only)", "_translated": sorted(done | set(todo)), **gloss},
                              ensure_ascii=False, indent=1))
    print(f"translated {len(todo)} new tokens; {len(gloss)} glosses total for {len(toks)} tokens")


if __name__ == "__main__":
    main()
