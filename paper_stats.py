"""Dataset statistics for the paper (Data section): per set and source system, tables, source columns, gt / n:1 /
ambiguous counts, and the share of columns with at least one vowel-poor token (the abbreviation proxy used by
mine_abbrev.vowel_poor; 2-letter tokens count as acronyms). Usage: python paper_stats.py"""
import json

import pandas as pd

from draft_confirm import OUT as CONFIRM
from hybrid import PAIRS, columns, words
from mine_abbrev import vowel_poor


NOT_ABBR = {"id", "at", "by", "of", "to"}  # universal/English 2-letter tokens (id, created_at, updated_by)


def abbreviated(col: str) -> bool:
    return any((len(w) == 2 and w.isalpha() and w not in NOT_ABBR) or (len(w) >= 3 and w.isalpha() and vowel_poor(w)) for w in words(col))


def main():
    rows = []
    for set_name, f in (("dev", PAIRS), ("confirm", CONFIRM)):
        for p in json.loads(f.read_text()):
            if not p["target"].startswith("fhir__"):
                continue
            cols = columns(p["source"])
            rows.append({"set": set_name, "system": p["source"].split("__")[0], "resource": p["target"][6:],
                         "cols": len(cols), "abbr_cols": sum(map(abbreviated, cols)), "gt": len(p["gt"]),
                         "n1": len(p["gt_n1"]), "amb": len(p["ambiguous"]),
                         "tgt": len(columns(p["target"]))})
    df = pd.DataFrame(rows)
    agg = lambda g: pd.Series({"tables": len(g), "cols": g.cols.sum(), "cols/table": round(g.cols.mean(), 1),
                               "abbr%": round(100 * g.abbr_cols.sum() / g.cols.sum(), 1), "gt": g["gt"].sum(),
                               "n1": g.n1.sum(), "amb": g.amb.sum()})
    print(df.groupby(["set", "system"]).apply(agg).to_string())
    print(df.groupby("set").apply(agg).to_string())
    print("\nresource distribution:\n", df.pivot_table(index="resource", columns="set", values="gt", aggfunc="size",
                                                    fill_value=0).to_string())
    print("\ntarget elements per resource:", df.groupby("resource").tgt.first().to_dict(), "union =",
          len(columns("fhir__ALL")))
    assert abbreviated("kd_dokter") and abbreviated("jk") and not abbreviated("nama_pasien")
    assert not abbreviated("created_at") and not abbreviated("id") and abbreviated("no_rawat")


if __name__ == "__main__":
    main()
