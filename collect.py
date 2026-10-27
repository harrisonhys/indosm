"""Pilot collector: pull CSV resources for a few shared indicators from CKAN-based Satu Data portals.

Writes data/raw/<host>/<resource_id>.csv and appends one JSON line per resource to data/raw/manifest.jsonl.
"""
import concurrent.futures as cf
import json
import pathlib
import requests

PORTALS = [
    "data.kalbarprov.go.id", "satudata.padang.go.id", "data.kaltimprov.go.id", "data.sumbarprov.go.id",
    "data.demakkab.go.id", "data.agamkab.go.id", "data.bantenprov.go.id", "data.acehprov.go.id",
    "data.bengkuluprov.go.id", "data.malangkota.go.id", "data.kutaitimurkab.go.id", "data.paserkab.go.id",
    "data.kendalkab.go.id", "data.kuduskab.go.id", "data.kamparkab.go.id", "data.tanahdatar.go.id",
    "data.pasamankab.go.id", "satudata.dharmasrayakab.go.id",
]
QUERIES = {"penduduk": "penduduk kecamatan jenis kelamin", "sekolah": "jumlah sekolah", "puskesmas": "puskesmas"}
ROWS_PER_QUERY = 8
MAX_BYTES = 2_000_000
OUT = pathlib.Path("data/raw")


def search(host, q):
    r = requests.get(f"https://{host}/api/3/action/package_search", params={"q": q, "rows": ROWS_PER_QUERY}, timeout=30)
    r.raise_for_status()
    return r.json()["result"]["results"]


def fetch(url):
    with requests.get(url, timeout=20, stream=True) as r:
        r.raise_for_status()
        buf = b""
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) > MAX_BYTES:  # ponytail: truncate big files, pilot only needs header + sample rows
                break
        return buf


def collect_portal(host):
    records = []
    for topic, q in QUERIES.items():
        try:
            pkgs = search(host, q)
        except Exception as e:
            print(f"[{host}] search '{q}' failed: {e}")
            continue
        for p in pkgs:
            for res in p.get("resources", []):
                if (res.get("format") or "").lower() != "csv" or not res.get("url"):
                    continue
                dest = OUT / host / f"{res['id']}.csv"
                if not dest.exists():
                    try:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(fetch(res["url"]))
                    except Exception as e:
                        print(f"[{host}] fetch {res['url']} failed: {e}")
                        continue
                records.append({
                    "host": host, "topic": topic, "package": p["name"], "title": p.get("title"),
                    "org": (p.get("organization") or {}).get("title"), "notes": p.get("notes"),
                    "license": p.get("license_title"), "resource_id": res["id"], "resource_name": res.get("name"),
                    "url": res["url"], "path": str(dest),
                })
                break  # one CSV per package is enough
    return records


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(18) as ex, open(OUT / "manifest.jsonl", "w") as f:
        futs = {ex.submit(collect_portal, h): h for h in PORTALS}
        for fut in cf.as_completed(futs):
            recs = fut.result()
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{futs[fut]}: {len(recs)} CSVs", flush=True)
