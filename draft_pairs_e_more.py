"""One-shot author of 26 more DRAFT Khanza->FHIR pairs (E29-E54), appended to data/subset_e/pairs_e.json.

Same conventions as draft_pairs_e.py (gt = scored 1:1, gt_n1 = extra source columns onto an already-used target,
ambiguous = needs adjudication), plus one new rule for vital-sign tables:
  one row holds several vitals; FHIR models blood pressure with components, so the BP column -> component.value[x]
  is the scored gt and the other vitals -> component.value[x] go to gt_n1.
"""
import json
import pathlib

from draft_pairs_e import BASE_FHIR, OUT, validate

NEW = []
VITALS = "Vital-sign row: BP column -> component.value[x] is scored, other vitals are gt_n1 (same target)."


def pair(id_, src, tgt, gt, gt_n1=(), ambiguous=(), notes=""):
    NEW.append({"id": id_, "group": "khanza-fhir", "lang": "id-en", "source": f"khanza__{src}", "target": f"fhir__{tgt}",
                "gt": [list(x) for x in gt], "gt_n1": [list(x) for x in gt_n1],
                "ambiguous": [list(x) for x in ambiguous], "notes": notes,
                "annotator": "draft-claude", "adjudicated": False})


# Patient
pair("E29", "pasien_mati", "Patient", [("no_rkm_medis", "identifier"), ("tanggal", "deceased[x]")],
     gt_n1=[("jam", "deceased[x]")],
     notes="icd1-4 = cause of death (Condition), kd_dokter = certifying doctor: no Patient counterpart.")
pair("E30", "pasien_corona", "Patient",
     [("no_rkm_medis", "identifier"), ("nama_lengkap", "name"), ("kode_jk", "gender"), ("tgl_lahir", "birthDate"),
      ("kd_kelurahan", "address"), ("notelp", "telecom")],
     gt_n1=[("no_pengenal", "identifier"), ("inisial", "name"), ("nama_jk", "gender"), ("nm_kelurahan", "address"),
            ("kd_kecamatan", "address"), ("nm_kecamatan", "address"), ("kd_kabupaten", "address"),
            ("nm_kabupaten", "address"), ("kd_propinsi", "address"), ("nm_propinsi", "address"), ("email", "telecom")],
     ambiguous=[("sebab_kematian", "deceased[x]", "cause of death text vs. deceased flag/date")],
     notes=BASE_FHIR + " COVID-19 reporting table (kewarganegaraan, status rawat/isolasi have no base-R4 target).")
# Practitioner
pair("E31", "petugas", "Practitioner",
     [("nip", "identifier"), ("nama", "name"), ("jk", "gender"), ("tgl_lahir", "birthDate"), ("alamat", "address"),
      ("no_telp", "telecom"), ("status", "active")],
     gt_n1=[("email", "telecom")],
     ambiguous=[("kd_jbtn", "qualification.code", "job position vs. qualification")], notes=BASE_FHIR)
# Organization
for id_, t, code, name in (("E32", "perusahaan_pasien", "kode_perusahaan", "nama_perusahaan"),
                           ("E33", "industrifarmasi", "kode_industri", "nama_industri"),
                           ("E34", "datasuplier", "kode_suplier", "nama_suplier")):
    pair(id_, t, "Organization", [(code, "identifier"), (name, "name"), ("alamat", "address"), ("no_telp", "telecom")],
         gt_n1=[("kota", "address")])
# Location
pair("E35", "bangsal", "Location", [("kd_bangsal", "identifier"), ("nm_bangsal", "name"), ("status", "status")])
pair("E36", "kamar", "Location",
     [("kd_kamar", "identifier"), ("kd_bangsal", "partOf"), ("status", "operationalStatus"), ("statusdata", "status")],
     ambiguous=[("kelas", "type", "room class (Kelas 1/VIP) vs. location type")],
     notes="status = ISI/KOSONG/DIBERSIHKAN is bed occupancy -> operationalStatus; statusdata = active flag -> status.")
pair("E37", "ruang_ok", "Location", [("kd_ruang_ok", "identifier"), ("nm_ruang_ok", "name")])
# Encounter
pair("E38", "dpjp_ranap", "Encounter", [("no_rawat", "identifier"), ("kd_dokter", "participant.individual")],
     notes="DPJP = attending doctor of an inpatient stay.")
# Condition
pair("E39", "resume_pasien", "Condition",
     [("no_rawat", "encounter"), ("kd_diagnosa_utama", "code"), ("kd_dokter", "asserter")],
     gt_n1=[("diagnosa_utama", "code"), ("kd_diagnosa_sekunder", "code"), ("kd_diagnosa_sekunder2", "code"),
            ("kd_diagnosa_sekunder3", "code"), ("kd_diagnosa_sekunder4", "code")],
     ambiguous=[("kd_dokter", "recorder", "DPJP as asserter vs. recorder")],
     notes="Discharge summary; procedures, complaints and discharge meds belong to other resources.")
# Observation
for id_, t, bp, others, date, time, nip in (
        ("E40", "pemeriksaan_ralan", "tensi", ["suhu_tubuh", "nadi", "respirasi", "tinggi", "berat", "spo2", "gcs"],
         "tgl_perawatan", "jam_rawat", "nip"),
        ("E41", "pemeriksaan_ranap", "tensi", ["suhu_tubuh", "nadi", "respirasi", "tinggi", "berat", "spo2", "gcs"],
         "tgl_perawatan", "jam_rawat", "nip"),
        ("E42", "catatan_observasi_igd", "td", ["hr", "rr", "suhu", "spo2", "gcs"], "tgl_perawatan", "jam_rawat", "nip"),
        ("E43", "catatan_observasi_ranap", "td", ["hr", "rr", "suhu", "spo2", "gcs"], "tgl_perawatan", "jam_rawat", "nip")):
    amb = [("kesadaran", "value[x]", "consciousness level as its own observation"),
           ("pemeriksaan", "note", "SOAP 'O' free text")] if t.startswith("pemeriksaan") else []
    pair(id_, t, "Observation",
         [("no_rawat", "encounter"), (date, "effective[x]"), (nip, "performer"), (bp, "component.value[x]")],
         gt_n1=[(time, "effective[x]")] + [(o, "component.value[x]") for o in others], ambiguous=amb, notes=VITALS)
pair("E44", "data_triase_igd", "Observation",
     [("no_rawat", "encounter"), ("tgl_kunjungan", "effective[x]"), ("tekanan_darah", "component.value[x]")],
     gt_n1=[(o, "component.value[x]") for o in ("nadi", "pernapasan", "suhu", "saturasi_o2", "nyeri")],
     ambiguous=[("id_observation_tekanan_darah", "identifier", "SATUSEHAT resource id vs. business identifier"),
                ("kode_kasus", "category", "case type vs. observation category")],
     notes=VITALS + " The id_observation_* columns are Khanza's own SATUSEHAT bridging ids.")
pair("E45", "skrining_gizi", "Observation",
     [("no_rawat", "encounter"), ("tanggal", "effective[x]"), ("skor_total", "value[x]"), ("nip", "performer"),
      ("skor_imt", "component.value[x]")],
     gt_n1=[("skor_bb", "component.value[x]"), ("skor_penyakit", "component.value[x]")],
     ambiguous=[("parameter_total", "interpretation", "free-text summary of the score")],
     notes="Nutrition screening score: total -> value[x], sub-scores -> component.value[x].")
pair("E46", "skrining_hipertensi", "Observation",
     [("no_rawat", "encounter"), ("tanggal", "effective[x]"), ("nip", "performer"), ("sistole", "component.value[x]"),
      ("klasifikasi_hipertensi", "interpretation"), ("hasil_skrining", "value[x]"), ("keterangan", "note")],
     gt_n1=[("diastole", "component.value[x]")])
# MedicationRequest
pair("E47", "resep_dokter_racikan", "MedicationRequest",
     [("no_resep", "identifier"), ("nama_racik", "medication[x]"), ("jml_dr", "dispenseRequest.quantity"),
      ("aturan_pakai", "dosageInstruction"), ("keterangan", "note")],
     ambiguous=[("kd_racik", "dosageInstruction", "compounding form (puyer/kapsul) vs. dosage")],
     notes="Compounded prescription (racikan).")
pair("E48", "resep_pulang", "MedicationRequest",
     [("no_rawat", "encounter"), ("kode_brng", "medication[x]"), ("jml_barang", "dispenseRequest.quantity"),
      ("dosis", "dosageInstruction"), ("tanggal", "authoredOn")],
     gt_n1=[("jam", "authoredOn")],
     ambiguous=[("no_batch", "dispenseRequest.initialFill", "batch belongs to Medication.batch / dispense")],
     notes="Discharge medication; prices (harga, total) are true negatives.")
# DiagnosticReport
pair("E49", "periksa_radiologi", "DiagnosticReport",
     [("no_rawat", "encounter"), ("kd_jenis_prw", "code"), ("tgl_periksa", "effective[x]"), ("nip", "performer"),
      ("kd_dokter", "resultsInterpreter")],
     gt_n1=[("jam", "effective[x]")],
     ambiguous=[("dokter_perujuk", "basedOn", "referring doctor only reachable via the ServiceRequest")],
     notes="Exposure parameters (kV, mAS, FFD, dosis) and tariffs are true negatives.")
pair("E50", "hasil_radiologi", "DiagnosticReport",
     [("no_rawat", "encounter"), ("tgl_periksa", "effective[x]"), ("hasil", "conclusion")],
     gt_n1=[("jam", "effective[x]")])
# ServiceRequest
for id_, t in (("E51", "permintaan_lab"), ("E52", "permintaan_radiologi")):
    pair(id_, t, "ServiceRequest",
         [("noorder", "identifier"), ("no_rawat", "encounter"), ("tgl_permintaan", "authoredOn"),
          ("dokter_perujuk", "requester"), ("informasi_tambahan", "note"), ("diagnosa_klinis", "reasonCode")],
         gt_n1=[("jam_permintaan", "authoredOn")],
         ambiguous=[("tgl_sampel", "specimen", "sampling time belongs to Specimen")],
         notes="status = ralan/ranap is the care setting, not ServiceRequest.status.")
pair("E53", "rujukan_internal_poli", "ServiceRequest",
     [("no_rawat", "encounter"), ("kd_dokter", "performer"), ("kd_poli", "locationReference")],
     notes="Internal referral to another clinic.")
pair("E54", "rujuk_masuk", "ServiceRequest",
     [("no_rujuk", "identifier"), ("no_rawat", "encounter"), ("perujuk", "requester"), ("kd_penyakit", "reasonCode"),
      ("kategori_rujuk", "category"), ("keterangan", "note")],
     gt_n1=[("dokter_perujuk", "requester")],
     ambiguous=[("no_rawat", "encounter", "the referral precedes the local encounter it created")],
     notes="Incoming referral = a ServiceRequest from an outside organisation.")


if __name__ == "__main__":
    existing = json.loads(OUT.read_text())
    assert not {p["id"] for p in existing} & {p["id"] for p in NEW}, "ids already present; refusing to append twice"
    for p in NEW:
        validate(p)
    OUT.write_text(json.dumps(existing + NEW, ensure_ascii=False, indent=1))
    n = sum(p["group"] == "khanza-fhir" for p in existing + NEW)
    print(f"appended {len(NEW)} pairs ({sum(len(p['gt']) for p in NEW)} gt); khanza-fhir pairs now {n}; total {len(existing) + len(NEW)}")
