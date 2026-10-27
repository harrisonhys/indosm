"""Robust loader for messy Satu Data CSVs (mixed delimiters, BOM, xlsx-as-csv, junk files)."""
import csv
import io
import pathlib

import pandas as pd


def load(path: str | pathlib.Path, nrows: int = 500) -> pd.DataFrame | None:
    raw = pathlib.Path(path).read_bytes()
    if raw[:2] == b"PK":  # xlsx served with format=CSV
        return None
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        delim = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    try:
        df = pd.read_csv(io.StringIO(text), sep=delim, nrows=nrows, dtype=str, on_bad_lines="skip")
    except Exception:
        return None
    df.columns = [" ".join(str(c).split()) for c in df.columns]  # collapse stray whitespace/newlines in headers
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed")]].dropna(how="all")
    return df if df.shape[1] >= 2 and len(df) >= 2 else None


if __name__ == "__main__":
    import json
    import sys

    for line in open(sys.argv[1] if len(sys.argv) > 1 else "data/raw/manifest.jsonl"):
        m = json.loads(line)
        df = load(m["path"])
        cols = "SKIP" if df is None else " | ".join(df.columns)[:260]
        print(f"{m['topic']:9} {m['host'][:24]:24} {m['resource_id'][:8]} {m['title'][:50]:50} :: {cols}")
