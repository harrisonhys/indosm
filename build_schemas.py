"""Extract sub-set E schemas (column name/type/description) from raw sources into data/subset_e/schemas/*.json.

Raw sources live in data/subset_e/raw/ (not for redistribution; see SUBSET_E.md for provenance and licenses).
Only schema metadata is extracted, never data rows.
"""
import json
import pathlib
import re

import pandas as pd

RAW = pathlib.Path("data/subset_e/raw")
OUT = pathlib.Path("data/subset_e/schemas")

SOURCES = {
    "khanza": ("sik.sql", "SIMRS Khanza (mas-elkhanza/SIMRS-Khanza@master, sik.sql)", "Khanza custom license (free use, no commercial gain without permission)", "id"),
    "opensid": ("opensid.sql", "OpenSID (OpenSID/OpenSID@master, contoh_data_awal_20210901.sql)", "GPL-3.0 + OpenSID version clause", "id"),
    "slims": ("senayan.sql", "SLiMS 9 Bulian (slims/slims9_bulian@master, install/senayan.sql)", "GPL-3.0", "en"),
    "siakad": ("idik_siakad.sql", "SIAKAD Feeder (idiknursidik/siakad@master, siakad.sql)", "MIT", "id"),
}
KHANZA_TABLES = ["pasien", "dokter", "pegawai", "poliklinik", "reg_periksa", "diagnosa_pasien", "resep_obat",
                 "resep_dokter", "databarang", "kamar_inap", "penjab", "rujuk", "periksa_lab", "detail_periksa_lab",
                 # added for the n>=40 Khanza->FHIR set (E29-E54)
                 "pasien_mati", "pasien_corona", "petugas", "perusahaan_pasien", "industrifarmasi", "datasuplier",
                 "bangsal", "kamar", "ruang_ok", "dpjp_ranap", "resume_pasien", "pemeriksaan_ralan",
                 "pemeriksaan_ranap", "catatan_observasi_igd", "catatan_observasi_ranap", "data_triase_igd",
                 "skrining_gizi", "skrining_hipertensi", "resep_dokter_racikan", "resep_pulang", "periksa_radiologi",
                 "hasil_radiologi", "permintaan_lab", "permintaan_radiologi", "rujukan_internal_poli", "rujuk_masuk"]
TABLES = {"khanza": KHANZA_TABLES, "opensid": ["tweb_penduduk"], "slims": ["member"],
          "siakad": ["siakad_mahasiswa", "siakad_matakuliah", "siakad_kelas", "siakad_akm",
                     "siakad_riwayatpendidikan", "siakad_kurikulum"]}
FHIR_RESOURCES = ["patient", "practitioner", "organization", "location", "encounter", "condition", "observation",
                  "medicationrequest", "medication", "diagnosticreport", "servicerequest"]
FHIR_SKIP = {"id", "meta", "implicitRules", "language", "text", "contained", "extension", "modifierExtension"}
PDF_FRAGMENTS = {"wa"}  # line-wrap debris from the PDF table in InsertPerubahanRiwayatPendidikan
FEEDER_ENDPOINTS = ["InsertBiodataMahasiswa", "InsertRiwayatPendidikanMahasiswa", "InsertMataKuliah",
                    "InsertKelasKuliah", "InsertPerkuliahanMahasiswa", "InsertKurikulum"]
# ponytail: 2-row merged header of OpenSID's format-bip-ektp.xls typed by hand; the file's sample rows look like
# real personal data, so the file itself is not kept.
BIP_EKTP = ["NO", "Nama Lengkap", "NIK", "Tempat Lahir", "Tgl/Bln/Th", "JK", "Stat Kwn", "Gol. Drh", "SHDK", "Agama",
            "Pendidikan Terakhir", "No Akta Lahir", "Pekerjaan", "Nama Ibu", "Nama Ayah", "Wjb KTP", "KTP-eL", "Status",
            "Stat Rkm"]


def save(system, table, source, license_, lang, columns):
    OUT.mkdir(parents=True, exist_ok=True)
    names = [c["name"] for c in columns]
    assert len(names) == len(set(names)), f"duplicate columns in {system}.{table}"
    doc = {"system": system, "table": table, "source": source, "license": license_, "lang": lang, "columns": columns}
    (OUT / f"{system}__{table}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    return f"{system}__{table}"


def ddl(sql: str, table: str) -> list[dict]:
    m = re.search(rf"CREATE TABLE (?:IF NOT EXISTS )?`{table}`\s*\((.*?)\n\)\s*(?:ENGINE|;)", sql, re.S)
    assert m, f"table {table} not found"
    cols = re.findall(r"^\s+`(\w+)`\s+([A-Za-z]+(?:\([^)]*\))?)", m.group(1), re.M)
    return [{"name": n, "type": t.lower(), "desc": ""} for n, t in cols]


def fhir(resource: str) -> tuple[str, list[dict]]:
    sd = json.loads((RAW / "fhir" / f"{resource}.json").read_text())
    cols = []
    for el in sd["snapshot"]["element"]:
        parts = el["path"].split(".")[1:]
        if not parts or parts[0] in FHIR_SKIP or parts[-1] in FHIR_SKIP:
            continue
        cols.append({"name": ".".join(parts), "type": "|".join(t["code"] for t in el.get("type", [])),
                     "desc": el.get("short", "")})
    return sd["name"], cols


def feeder(endpoint: str) -> list[dict]:
    txt = re.sub(r"<<PAGE \d+>>\nUser Guide Web Service Versi2.2 Page \d+ ?\n", "", (RAW / "feeder.txt").read_text())
    body = re.split(rf"\n3\.\d+ {endpoint} ?\n", txt)[1]
    body = re.split(r"\n3\.\d+ \w+", body)[0]
    found = re.findall(r"^\s*([a-z][a-z0-9_]+)\s+(character varying|character|date|smallint|numeric|integer|uuid|text|double|decimal)",
                       body, re.M)
    seen, cols = set(), []
    for n, t in found:
        if n not in seen and n not in PDF_FRAGMENTS:
            seen.add(n); cols.append({"name": n, "type": t, "desc": ""})
    return cols


def main():
    made = []
    for system, (fname, src, lic, lang) in SOURCES.items():
        sql = (RAW / fname).read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        made += [save(system, t, src, lic, lang, ddl(sql, t)) for t in TABLES[system]]
    for r in FHIR_RESOURCES:
        name, cols = fhir(r)
        made.append(save("fhir", name, "HL7 FHIR R4 4.0.1 StructureDefinition snapshot", "CC0-1.0", "en", cols))
    for ep in FEEDER_ENDPOINTS:
        made.append(save("feeder", ep, "PDDikti Feeder Web Service User Guide v2.2 (07-12-2020)", "public documentation", "id", feeder(ep)))
    siak = pd.read_excel(RAW / "format-siak.xls", header=None, nrows=1, dtype=str).iloc[0].dropna().tolist()
    made.append(save("siak", "format_siak", "OpenSID storage/app/template/impor/format-siak.xls (header only)", "GPL-3.0 (OpenSID)", "id",
                     [{"name": c.strip(), "type": "", "desc": ""} for c in siak]))
    made.append(save("siak", "bip_ektp", "OpenSID storage/app/template/impor/format-bip-ektp.xls (header only)", "GPL-3.0 (OpenSID)", "id",
                     [{"name": c, "type": "", "desc": ""} for c in BIP_EKTP]))
    for m in made:
        n = len(json.loads((OUT / f"{m}.json").read_text())["columns"])
        print(f"{m:45} {n:3} cols")


if __name__ == "__main__":
    main()
