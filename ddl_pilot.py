"""Schema-only pilot on real operational schemas (no instances): SIMRS Khanza `pasien` vs
OpenSID `tweb_penduduk` (ID-ID, abbreviation-heavy) and vs a flattened FHIR R4 / SATUSEHAT Patient (ID-EN, natural).

Usage: python ddl_pilot.py <sik.sql> <opensid.sql>
"""
import re
import sys

import pandas as pd

from pilot import MATCHERS, f1_one_to_one, recall_at_gt

# ponytail: hand-flattened FHIR Patient incl. SATUSEHAT extensions (birthPlace, religion, administrativeCode)
FHIR_PATIENT = [
    "identifier_nik", "identifier_mrn", "identifier_bpjs", "active", "name_text", "gender", "birthDate", "birthPlace",
    "deceasedBoolean", "address_line", "address_province_code", "address_city_code", "address_district_code",
    "address_village_code", "address_postalCode", "telecom_phone", "telecom_email", "maritalStatus", "religion",
    "mothersMaidenName", "citizenshipStatus", "communication_language", "multipleBirthInteger",
    "contact_name", "contact_relationship", "managingOrganization",
]
GT_OPENSID = [("nm_pasien", "nama"), ("no_ktp", "nik"), ("jk", "sex"), ("tmp_lahir", "tempatlahir"),
              ("tgl_lahir", "tanggallahir"), ("nm_ibu", "nama_ibu"), ("alamat", "alamat_sekarang"),
              ("gol_darah", "golongan_darah_id"), ("pekerjaan", "pekerjaan_id"), ("stts_nikah", "status_kawin"),
              ("agama", "agama_id"), ("no_tlp", "telepon"), ("pnd", "pendidikan_kk_id"), ("cacat_fisik", "cacat_id"),
              ("email", "email"), ("no_peserta", "no_asuransi"), ("kd_pj", "id_asuransi"), ("bahasa_pasien", "bahasa_id")]
GT_FHIR = [("no_ktp", "identifier_nik"), ("no_rkm_medis", "identifier_mrn"), ("no_peserta", "identifier_bpjs"),
           ("nm_pasien", "name_text"), ("jk", "gender"), ("tmp_lahir", "birthPlace"), ("tgl_lahir", "birthDate"),
           ("nm_ibu", "mothersMaidenName"), ("alamat", "address_line"), ("stts_nikah", "maritalStatus"),
           ("agama", "religion"), ("no_tlp", "telecom_phone"), ("email", "telecom_email"),
           ("bahasa_pasien", "communication_language"), ("kd_prop", "address_province_code"),
           ("kd_kab", "address_city_code"), ("kd_kec", "address_district_code"), ("kd_kel", "address_village_code"),
           ("namakeluarga", "contact_name"), ("keluarga", "contact_relationship")]


def ddl_columns(sql_path: str, table: str) -> list[str]:
    sql = open(sql_path, encoding="utf-8", errors="replace").read()
    body = re.search(rf"CREATE TABLE `{table}` \((.*?)\) ENGINE", sql, re.S).group(1)
    return re.findall(r"^\s+`(\w+)`", body, re.M)


def empty(cols):  # schema-only: 2 blank rows so instance-based code paths don't crash
    return pd.DataFrame({c: ["", ""] for c in cols})


if __name__ == "__main__":
    khanza, opensid = ddl_columns(sys.argv[1], "pasien"), ddl_columns(sys.argv[2], "tweb_penduduk")
    rows = []
    for name, tgt, gt in [("khanza-opensid (id-id)", opensid, GT_OPENSID), ("khanza-fhir (id-en)", FHIR_PATIENT, GT_FHIR)]:
        gts = set(gt)
        assert {s for s, _ in gts} <= set(khanza) and {t for _, t in gts} <= set(tgt), name
        for m, fn in MATCHERS.items():
            sc = fn(empty(khanza), empty(tgt))
            rows.append({"pair": name, "method": m, "R@GT": recall_at_gt(sc, gts), "F1": f1_one_to_one(sc, gts)})
    df = pd.DataFrame(rows)
    df.to_csv("results/ddl_pilot_scores.csv", index=False)
    print(f"source {len(khanza)} cols | opensid {len(opensid)} | fhir {len(FHIR_PATIENT)}")
    print(df.pivot_table(index="method", columns="pair", values=["R@GT", "F1"]).round(3).to_string())
