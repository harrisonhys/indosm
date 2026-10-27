"""Richer stage-1 resource descriptions from the FHIR R4 spec (CC0), for the stage-1 catalog ablation.

Per resource: `short` (the current catalog), the root `definition` (+ `comment`) from the StructureDefinition,
the "Scope and Usage" and "Boundaries and Relationships" sections of the resource page
(hl7.org/fhir/R4/<name>.html, saved in data/subset_e/raw/fhir_pages/), and the top-level element names.
Writes data/fhir_catalog_rich.json. Usage: python fhir_catalog.py
"""
import html
import json
import pathlib
import re

from two_stage import RAW_FHIR

PAGES = pathlib.Path("data/subset_e/raw/fhir_pages")
OUT = pathlib.Path("data/fhir_catalog_rich.json")
H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)


def plain(fragment: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()


def section(page: str, title: str) -> str:
    heads = list(H2.finditer(page))
    for i, h in enumerate(heads):
        if title.lower() in plain(h.group(1)).lower():
            end = heads[i + 1].start() if i + 1 < len(heads) else len(page)
            return plain(page[h.end():end])
    return ""


def main():
    out = {}
    for f in sorted(RAW_FHIR.glob("*.json")):
        sd = json.loads(f.read_text())
        root, name = sd["snapshot"]["element"][0], sd["name"]
        page = (PAGES / f"{name.lower()}.html").read_text()
        top = [e["path"].split(".", 1)[1] for e in sd["snapshot"]["element"]
               if e["path"].count(".") == 1 and e["path"].split(".")[1] not in
               {"id", "meta", "implicitRules", "language", "text", "contained", "extension", "modifierExtension"}]
        out[name] = {"short": root["short"],
                     "definition": " ".join(filter(None, (root.get("definition"), root.get("comment")))),
                     "scope": section(page, "Scope and Usage"),
                     "boundaries": section(page, "Boundaries and Relationships"),
                     "elements": top}
        assert out[name]["scope"], f"no scope section for {name}"
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for name, d in out.items():
        print(f"{name:18} def {len(d['definition']):4}  scope {len(d['scope']):5}  bnr {len(d['boundaries']):5}  "
              f"elements {len(d['elements'])}")


if __name__ == "__main__":
    main()
