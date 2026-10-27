"""Held-out confirmation set (PREREG_CONFIRM.md): DRAFT non-Khanza Indonesian health schemas -> FHIR R4.

Extracts schemas (names/types only, never data rows) from data/subset_e/raw/{gh__*, opensid_umum}/ into
data/subset_e/schemas/, drafts GT with the SUBSET_E.md conventions, and writes data/subset_e/pairs_confirm.json plus
its large-target version pairs_confirm_large.json (target fhir__ALL). Kept apart from pairs_e.json so the n=41 runs
stay reproducible. Prints the SHA-256 to freeze in PREREG_CONFIRM.md. Usage: python draft_confirm.py
"""
import hashlib
import json
import pathlib
import re

from build_schemas import RAW, ddl, save
from draft_pairs_e import BASE_FHIR, validate

OUT = pathlib.Path("data/subset_e/pairs_confirm.json")
OUT_LARGE = pathlib.Path("data/subset_e/pairs_confirm_large.json")
GH = "https://github.com/"
# system: (raw dir, kind, source label, license, tables)
SYSTEMS = {
    "rmpuskesmas": ("gh__mfarim__laravel-rekam-medis-puskesmas", "laravel", "mfarim/laravel-rekam-medis-puskesmas",
                    "MIT", ["tb_pasien", "tb_rekam_medis", "tb_rujuk", "tb_resep", "tb_dokter"]),
    "sipuskesmas": ("gh__elingp__sistem-informasi-puskesmas", "laravel", "elingp/sistem-informasi-puskesmas", "MIT",
                    ["polis", "tenaga_kesehatans", "antrians"]),
    "cirekammedis": ("gh__arfandotid__ci_rekammedis", "mysql", "arfandotid/ci_rekammedis",
                     "unclear (license.txt is CodeIgniter's MIT, not the app author's)",
                     ["dokter", "obat", "pasien", "poliklinik", "rekam_medis", "rm_obat"]),
    "sipograf": ("gh__Kriss245__Sipograf-Sistem-Informasi-Posyandu-dengan-KMS", "mysql",
                 "Kriss245/Sipograf-Sistem-Informasi-Posyandu-dengan-KMS", "MIT", ["t_anak", "t_penimbangan"]),
    "epuskesmas": ("gh__Slyzyy__TUBES_WEBPRO_e-Puskesmas", "mysql", "Slyzyy/TUBES_WEBPRO_e-Puskesmas",
                   "unclear (license.txt is CodeIgniter's MIT, not the app author's)", ["obat"]),
    "opensid": ("opensid_umum", "laravel", "OpenSID/OpenSID (branch umum, struktur_tabel migrations)",
                "GPL-3.0 + OpenSID version clause", ["posyandu"]),
}
MACROS = {"id": ["id"], "timestamps": ["created_at", "updated_at"],
          "timesWithUserstamps": ["created_at", "created_by", "updated_at", "updated_by"]}
CONSTRAINTS = {"foreign", "primary", "unique", "index", "dropColumn"}


def laravel(php: str, table: str) -> list[dict]:
    body = re.search(rf"Schema::create\('{table}'.*?\{{(.*?)\n\s*\}}\);", php, re.S)
    assert body, f"table {table} not found"
    cols = []
    for method, arg in re.findall(r"\$table->(\w+)\(\s*(?:'(\w+)')?", body.group(1)):
        if method in MACROS and not arg:
            cols += [{"name": n, "type": method, "desc": ""} for n in MACROS[method]]
        elif arg and method not in CONSTRAINTS:
            cols.append({"name": arg, "type": method.lower(), "desc": ""})
    return cols


def build_schemas():
    for system, (d, kind, repo, lic, tables) in SYSTEMS.items():
        files = sorted((RAW / d).glob("*.php" if kind == "laravel" else "*.sql"))
        text = "\n".join(f.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n") for f in files)
        commit = (RAW / d / "COMMIT").read_text().split()[0]
        for t in tables:
            cols = laravel(text, t) if kind == "laravel" else ddl(text, t)
            save(system, t, f"{repo}@{commit[:10]}", lic, "id", cols)


P = []


def pair(id_, src, tgt, gt, gt_n1=(), ambiguous=(), notes=""):
    P.append({"id": id_, "group": "confirm-fhir", "lang": "id-en", "source": src, "target": f"fhir__{tgt}",
              "gt": [list(x) for x in gt], "gt_n1": [list(x) for x in gt_n1],
              "ambiguous": [list(x) for x in ambiguous], "notes": notes,
              "annotator": "draft-claude", "adjudicated": False})


# --- rmpuskesmas (mfarim): heavy ad-hoc abbreviations, different from Khanza's
pair("C01", "rmpuskesmas__tb_pasien", "Patient",
     [("kode_pasien", "identifier"), ("nama_pasien", "name"), ("alamat", "address"), ("tgl_lahir", "birthDate"),
      ("telp", "telecom"), ("ortu_suami", "contact.name")],
     gt_n1=[("no_jaminan", "identifier"), ("rt", "address"), ("rw", "address")],
     ambiguous=[("istri_anak", "contact.name", "second contact (wife/child) vs. ortu_suami")],
     notes=BASE_FHIR + " Jen_pmbyrn (payment type) belongs to Coverage; alergi_obat to AllergyIntolerance.")
pair("C02", "rmpuskesmas__tb_rekam_medis", "Encounter",
     [("no_redis", "identifier"), ("kode_pasien", "subject"), ("kode_dktr", "participant.individual"),
      ("keluhan", "reasonCode"), ("diagnosa", "diagnosis.condition")],
     ambiguous=[("rcn_tndk_lnjt", "hospitalization.dischargeDisposition", "follow-up plan vs. discharge disposition"),
                ("created_at", "period", "record timestamp vs. visit time")],
     notes="One row = one examination. Anamnesia/pmrk_fisik/therapy belong to Observation/ClinicalImpression/"
           "MedicationRequest; same split as Khanza kamar_inap (diagnosa_awal->reasonCode, akhir->diagnosis).")
pair("C03", "rmpuskesmas__tb_rujuk", "ServiceRequest",
     [("no_surat_rujukan", "identifier"), ("tgl_rujuk", "authoredOn"), ("no_redis", "encounter")],
     notes="no_redis = visit record id, the FK analogous to Khanza no_rawat.")
pair("C04", "rmpuskesmas__tb_resep", "MedicationRequest",
     [("no_resep", "identifier"), ("tgl_resep", "authoredOn"), ("no_redis", "encounter")],
     ambiguous=[("resep", "medication[x]", "free-text prescription: drug and/or dosage (dosageInstruction)")])
pair("C05", "rmpuskesmas__tb_dokter", "Practitioner",
     [("kode_dktr", "identifier"), ("nama_dktr", "name"), ("alamat_dktr", "address"),
      ("tgl_lahir_dktr", "birthDate"), ("telp_dktr", "telecom")],
     ambiguous=[("pend_trkhr_dktr", "qualification.code", "education level vs. professional qualification")],
     notes=BASE_FHIR)
# --- sipuskesmas (elingp): descriptive Laravel names
pair("C06", "sipuskesmas__polis", "Location", [("id", "identifier"), ("nama", "name")],
     notes="Poli = clinic department, -> Location as Khanza poliklinik (E04). nomor_sekarang = current queue number.")
pair("C07", "sipuskesmas__tenaga_kesehatans", "Practitioner",
     [("id", "identifier"), ("nama", "name"), ("no_telepon", "telecom")],
     notes="poli_id and jadwal (schedule) belong to PractitionerRole, not in the 11 resources.")
pair("C08", "sipuskesmas__antrians", "Encounter",
     [("id", "identifier"), ("pasien_id", "subject"), ("poli_id", "location.location")],
     ambiguous=[("created_at", "period", "queue-ticket time vs. visit time"),
                ("nomor_antrian", "identifier", "daily queue number vs. visit identifier")],
     notes="Queue ticket = registration of an outpatient visit (as Encounter with status arrived in SATUSEHAT).")
# --- cirekammedis (arfandotid): camelCase
pair("C09", "cirekammedis__dokter", "Practitioner",
     [("nip", "identifier"), ("namaDokter", "name"), ("spesialis", "qualification.code"), ("noTelp", "telecom"),
      ("alamat", "address")],
     gt_n1=[("email", "telecom")])
pair("C10", "cirekammedis__obat", "Medication", [("idObat", "identifier"), ("namaObat", "code")],
     notes="harga (price) and keterangan (indication text) have no Medication counterpart.")
pair("C11", "cirekammedis__pasien", "Patient",
     [("idPasien", "identifier"), ("namaPasien", "name"), ("jenisKelamin", "gender"), ("noTelp", "telecom"),
      ("alamat", "address")],
     gt_n1=[("email", "telecom")])
pair("C12", "cirekammedis__poliklinik", "Location", [("idPoliklinik", "identifier"), ("namaPoliklinik", "name")],
     ambiguous=[("gedung", "partOf", "building/floor text vs. parent location")])
pair("C13", "cirekammedis__rekam_medis", "Encounter",
     [("idRekamMedis", "identifier"), ("pasienId", "subject"), ("dokterNip", "participant.individual"),
      ("poliklinikId", "location.location"), ("keluhan", "reasonCode"), ("diagnosa", "diagnosis.condition"),
      ("tglPeriksa", "period")],
     notes="userId = app user who entered the record: no Encounter counterpart.")
pair("C14", "cirekammedis__rm_obat", "MedicationRequest",
     [("idRekamMedis", "encounter"), ("idObat", "medication[x]")],
     notes="Link table visit x drug.")
# --- sipograf (posyandu growth monitoring)
pair("C15", "sipograf__t_anak", "Patient",
     [("id_anak", "identifier"), ("nama_anak", "name"), ("tanggal_lahir", "birthDate"),
      ("jenis_kelamin", "gender"), ("alamat", "address")],
     ambiguous=[("nama_ibu", "contact.name", "mother of a child patient: guardian contact vs. mothersMaidenName ext.")],
     notes=BASE_FHIR)
pair("C16", "sipograf__t_penimbangan", "Observation",
     [("id_penimbangan", "identifier"), ("id_anak", "subject"), ("tgl_penimbangan", "effective[x]"),
      ("berat_badan", "value[x]"), ("petugas", "performer"), ("keterangan", "note")],
     gt_n1=[("tinggi_badan", "value[x]")],
     ambiguous=[("posyandu", "performer", "posyandu name: performing organization vs. location")],
     notes="Weighing record; weight is the primary value, height n:1 (same rule as the vital-sign tables). "
           "umur (age in months) has no Observation element.")
# --- epuskesmas
pair("C17", "epuskesmas__obat", "Medication", [("id_obat", "identifier"), ("nama", "code")],
     notes="kategori = therapeutic class ('Obat Demam'): Medication R4 has no such element.")
# --- OpenSID health module
pair("C18", "opensid__posyandu", "Organization", [("id", "identifier"), ("nama", "name"), ("alamat", "address")],
     notes="Posyandu = community-run health post. Organization chosen (a body with a name and address); "
           "Location is also defensible, so a Location answer scores 0 here (resource-level ambiguity).")


def large(pairs: list[dict]) -> list[dict]:
    names = {c["name"] for c in json.loads(pathlib.Path("data/subset_e/schemas/fhir__ALL.json").read_text())["columns"]}
    out = []
    for p in pairs:
        res = p["target"].removeprefix("fhir__")
        remap = lambda xs: [[s, f"{res}.{t}", *rest] for s, t, *rest in xs]
        out.append({**p, "id": p["id"] + "L", "group": "confirm-fhir-large", "target": "fhir__ALL",
                    "gt": remap(p["gt"]), "gt_n1": remap(p["gt_n1"]), "ambiguous": remap(p["ambiguous"])})
    assert all(t in names for p in out for _, t in p["gt"])
    return out


def main():
    build_schemas()
    for p in P:
        validate(p)
    OUT.write_text(json.dumps(P, ensure_ascii=False, indent=1))
    OUT_LARGE.write_text(json.dumps(large(P), ensure_ascii=False, indent=1))
    print(f"{len(P)} pairs, {sum(len(p['gt']) for p in P)} gt, {sum(len(p['gt_n1']) for p in P)} n:1, "
          f"{sum(len(p['ambiguous']) for p in P)} ambiguous")
    for f in (OUT, OUT_LARGE):
        print(f"sha256 {f.name}: {hashlib.sha256(f.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
