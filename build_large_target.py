"""Large-target variant of sub-set E: every FHIR pair is matched against the UNION of all 11 FHIR resources.

Writes data/subset_e/schemas/fhir__ALL.json (elements named "Resource.path") and data/subset_e/pairs_e_large.json
(E01-E14 + E20 with targets remapped). The matcher is not told which resource is the right one.
GT is unchanged except for the prefix, so a correct match into a *different* resource counts as wrong:
precision here is a lower bound.
"""
import json
import pathlib

SCHEMAS = pathlib.Path("data/subset_e/schemas")
PAIRS = pathlib.Path("data/subset_e/pairs_e.json")
OUT_PAIRS = pathlib.Path("data/subset_e/pairs_e_large.json")


def main():
    cols = []
    for f in sorted(SCHEMAS.glob("fhir__*.json")):
        d = json.loads(f.read_text())
        if d["table"] == "ALL":
            continue
        cols += [{**c, "name": f"{d['table']}.{c['name']}"} for c in d["columns"]]
    doc = {"system": "fhir", "table": "ALL", "source": "union of the 11 FHIR R4 resources in sub-set E",
           "license": "CC0-1.0", "lang": "en", "columns": cols}
    (SCHEMAS / "fhir__ALL.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

    large = []
    for p in json.loads(PAIRS.read_text()):
        if not p["target"].startswith("fhir__"):
            continue
        res = p["target"].removeprefix("fhir__")
        remap = lambda xs: [[s, f"{res}.{t}", *rest] for s, t, *rest in xs]
        large.append({**p, "id": p["id"] + "L", "group": p["group"] + "-large", "target": "fhir__ALL",
                      "gt": remap(p["gt"]), "gt_n1": remap(p["gt_n1"]), "ambiguous": remap(p["ambiguous"])})
    names = {c["name"] for c in cols}
    assert all(t in names for p in large for _, t in p["gt"]), "remapped GT target missing from union"
    OUT_PAIRS.write_text(json.dumps(large, ensure_ascii=False, indent=1))
    print(f"union target: {len(cols)} elements; {len(large)} pairs, {sum(len(p['gt']) for p in large)} gt")


if __name__ == "__main__":
    main()
