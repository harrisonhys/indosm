"""One-shot author of the DRAFT sub-set E ground truth -> data/subset_e/pairs_e.json.

After this, pairs_e.json is the source of truth: annotators edit the JSON, not this script.
Per pair:
  gt         1:1 correspondences (scored)
  gt_n1      extra source columns that map to an already-used target (n:1, e.g. tgl_x + jam_x -> period); not scored
  ambiguous  candidate pairs needing adjudication: [source, target, reason]
"""
import json
import pathlib

SCHEMAS = pathlib.Path("data/subset_e/schemas")
OUT = pathlib.Path("data/subset_e/pairs_e.json")


def same_names(src, tgt, exclude=()):
    a = {c["name"] for c in json.loads((SCHEMAS / f"{src}.json").read_text())["columns"]}
    b = {c["name"] for c in json.loads((SCHEMAS / f"{tgt}.json").read_text())["columns"]}
    return [[n, n] for n in sorted(a & b) if n not in exclude]


P = []


def pair(id_, group, lang, src, tgt, gt, gt_n1=(), ambiguous=(), notes=""):
    P.append({"id": id_, "group": group, "lang": lang, "source": src, "target": tgt,
              "gt": [list(x) for x in gt], "gt_n1": [list(x) for x in gt_n1],
              "ambiguous": [list(x) for x in ambiguous], "notes": notes,
              "annotator": "draft-claude", "adjudicated": False})


BASE_FHIR = "Base FHIR R4 only: SATUSEHAT extensions (birthPlace, religion, mothersMaidenName, citizenship) are not modelled, so those source columns are true negatives."

# ---- Group 1: SIMRS Khanza -> FHIR R4 (id-en) ----
pair("E01", "khanza-fhir", "id-en", "khanza__pasien", "fhir__Patient",
     [("no_ktp", "identifier"), ("nm_pasien", "name"), ("jk", "gender"), ("tgl_lahir", "birthDate"),
      ("alamat", "address"), ("stts_nikah", "maritalStatus"), ("no_tlp", "telecom"),
      ("bahasa_pasien", "communication"), ("namakeluarga", "contact.name"), ("keluarga", "contact.relationship"),
      ("alamatpj", "contact.address")],
     gt_n1=[("no_rkm_medis", "identifier"), ("no_peserta", "identifier"), ("email", "telecom"),
            ("kd_kel", "address"), ("kd_kec", "address"), ("kd_kab", "address"), ("kd_prop", "address")],
     notes=BASE_FHIR + " Primary identifier chosen = NIK (no_ktp), as in SATUSEHAT.")
pair("E02", "khanza-fhir", "id-en", "khanza__dokter", "fhir__Practitioner",
     [("kd_dokter", "identifier"), ("nm_dokter", "name"), ("jk", "gender"), ("tgl_lahir", "birthDate"),
      ("almt_tgl", "address"), ("no_telp", "telecom"), ("status", "active"),
      ("no_ijn_praktek", "qualification.identifier"), ("kd_sps", "qualification.code")],
     gt_n1=[("email", "telecom")],
     ambiguous=[("alumni", "qualification.issuer", "alma mater vs. issuing body of the qualification")],
     notes=BASE_FHIR)
pair("E03", "khanza-fhir", "id-en", "khanza__pegawai", "fhir__Practitioner",
     [("nik", "identifier"), ("nama", "name"), ("jk", "gender"), ("tgl_lahir", "birthDate"), ("alamat", "address"),
      ("stts_aktif", "active"), ("photo", "photo")],
     gt_n1=[("no_ktp", "identifier"), ("kota", "address")],
     ambiguous=[("pendidikan", "qualification.code", "education level vs. professional qualification")],
     notes="Trap: in Khanza `pegawai.nik` is the EMPLOYEE number (nomor induk karyawan); the national ID is `no_ktp`.")
pair("E04", "khanza-fhir", "id-en", "khanza__poliklinik", "fhir__Location",
     [("kd_poli", "identifier"), ("nm_poli", "name"), ("status", "status")],
     notes="registrasi / registrasilama are registration fees: no FHIR Location counterpart.")
pair("E05", "khanza-fhir", "id-en", "khanza__reg_periksa", "fhir__Encounter",
     [("no_rawat", "identifier"), ("tgl_registrasi", "period"), ("kd_dokter", "participant.individual"),
      ("no_rkm_medis", "subject"), ("kd_poli", "location.location"), ("stts", "status"), ("status_lanjut", "class")],
     gt_n1=[("jam_reg", "period")],
     ambiguous=[("kd_pj", "account", "payer code vs. billing account"),
                ("hubunganpj", "participant.type", "relation of responsible person; not a care participant")],
     notes="status_lanjut = Ralan/Ranap (outpatient/inpatient) -> Encounter.class.")
pair("E06", "khanza-fhir", "id-en", "khanza__diagnosa_pasien", "fhir__Condition",
     [("no_rawat", "encounter"), ("kd_penyakit", "code")],
     ambiguous=[("status_penyakit", "clinicalStatus", "Lama/Baru = new vs. existing case, not active/resolved"),
                ("prioritas", "stage", "diagnosis rank lives in Encounter.diagnosis.rank, not Condition")],
     notes="Small pair with 22 distractor targets.")
pair("E07", "khanza-fhir", "id-en", "khanza__resep_obat", "fhir__MedicationRequest",
     [("no_resep", "identifier"), ("no_rawat", "encounter"), ("kd_dokter", "requester"),
      ("tgl_peresepan", "authoredOn"), ("status", "category")],
     gt_n1=[("jam_peresepan", "authoredOn")],
     notes="status = ralan/ranap -> MedicationRequest.category (outpatient/inpatient). tgl_penyerahan belongs to MedicationDispense.")
pair("E08", "khanza-fhir", "id-en", "khanza__resep_dokter", "fhir__MedicationRequest",
     [("no_resep", "identifier"), ("kode_brng", "medication[x]"), ("jml", "dispenseRequest.quantity"),
      ("aturan_pakai", "dosageInstruction")])
pair("E09", "khanza-fhir", "id-en", "khanza__databarang", "fhir__Medication",
     [("kode_brng", "identifier"), ("nama_brng", "code"), ("kode_industri", "manufacturer"),
      ("expire", "batch.expirationDate"), ("status", "status")],
     ambiguous=[("kode_sat", "form", "dispensing unit (TAB/BTL) vs. dose form"),
                ("isi", "amount", "pack content vs. amount of drug per package")],
     notes="Most columns are prices per class (kelas1..vvip): true negatives.")
pair("E10", "khanza-fhir", "id-en", "khanza__kamar_inap", "fhir__Encounter",
     [("no_rawat", "identifier"), ("kd_kamar", "location.location"), ("tgl_masuk", "location.period"),
      ("stts_pulang", "hospitalization.dischargeDisposition"), ("diagnosa_awal", "reasonCode"),
      ("diagnosa_akhir", "diagnosis.condition")],
     gt_n1=[("jam_masuk", "location.period"), ("tgl_keluar", "location.period"), ("jam_keluar", "location.period")],
     ambiguous=[("lama", "length", "days in this room vs. whole encounter length")],
     notes="One row = one room stay, so dates map to location.period rather than Encounter.period.")
pair("E11", "khanza-fhir", "id-en", "khanza__penjab", "fhir__Organization",
     [("kd_pj", "identifier"), ("png_jawab", "name"), ("alamat_asuransi", "address"), ("no_telp", "telecom"),
      ("attn", "contact.name"), ("status", "active")],
     ambiguous=[("nama_perusahaan", "alias", "payer label (png_jawab) vs. legal company name")])
pair("E12", "khanza-fhir", "id-en", "khanza__rujuk", "fhir__ServiceRequest",
     [("no_rujuk", "identifier"), ("no_rawat", "encounter"), ("rujuk_ke", "performer"), ("tgl_rujuk", "authoredOn"),
      ("keterangan_diagnosa", "reasonCode"), ("kd_dokter", "requester"), ("keterangan", "note"),
      ("kat_rujuk", "category")],
     gt_n1=[("jam", "authoredOn")])
pair("E13", "khanza-fhir", "id-en", "khanza__periksa_lab", "fhir__DiagnosticReport",
     [("no_rawat", "encounter"), ("kd_jenis_prw", "code"), ("tgl_periksa", "effective[x]"), ("nip", "performer"),
      ("kd_dokter", "resultsInterpreter"), ("kategori", "category")],
     gt_n1=[("jam", "effective[x]")],
     ambiguous=[("dokter_perujuk", "basedOn", "referring doctor belongs to the ServiceRequest, only reachable via basedOn")],
     notes="Tariff columns (bagian_rs, bhp, tarif_*, kso, menejemen, biaya) are true negatives.")
pair("E14", "khanza-fhir", "id-en", "khanza__detail_periksa_lab", "fhir__Observation",
     [("no_rawat", "encounter"), ("id_template", "code"), ("nilai", "value[x]"), ("nilai_rujukan", "referenceRange"),
      ("tgl_periksa", "effective[x]")],
     gt_n1=[("jam", "effective[x]")],
     ambiguous=[("keterangan", "interpretation", "Khanza stores L/H flags here, but it is free text"),
                ("kd_jenis_prw", "basedOn", "lab package code vs. order")])

# ---- Group 2: civil-registry style (id-id) ----
pair("E15", "opensid-siak", "id-id", "opensid__tweb_penduduk", "siak__format_siak",
     [("nik", "NIK"), ("nama", "Nama Penduduk"), ("tempatlahir", "Tempat Lahir"), ("tanggallahir", "Tanggal Lahir"),
      ("sex", "Kelamin"), ("ayah_nik", "NIK Ayah"), ("nama_ayah", "Ayah"), ("ibu_nik", "NIK Ibu"), ("nama_ibu", "Ibu"),
      ("status_kawin", "Status Kawin"), ("kk_level", "SHDK"), ("agama_id", "Agama"), ("alamat_sekarang", "Alamat"),
      ("pendidikan_kk_id", "Pendidikan"), ("pekerjaan_id", "Pekerjaan"), ("golongan_darah_id", "Gol. Darah"),
      ("cacat_id", "Cacat"), ("dokumen_pasport", "Nomor Paspor"), ("akta_lahir", "Nomor Akta Lahir"),
      ("akta_perkawinan", "Nomor Akta Kawin"), ("tanggalperkawinan", "Tanggal Kwn"),
      ("akta_perceraian", "Nomor Akta Cerai"), ("tanggalperceraian", "Tgl Cerai"), ("status_dasar", "Status"),
      ("created_at", "Tgl Entri"), ("created_by", "Petugas Entri"), ("updated_at", "Tgl Ubah")],
     ambiguous=[("id_kk", "Nomor KK", "FK to tweb_keluarga, KK number only via join"),
                ("id_cluster", "RT", "FK to wilayah; RT/RW/Desa only via join"),
                ("ktp_el", "Cetak KTP", "e-KTP ownership flag vs. print date")],
     notes="SIAK export layout as shipped in OpenSID's import templates (header only).")
pair("E16", "opensid-siak", "id-id", "opensid__tweb_penduduk", "siak__bip_ektp",
     [("nama", "Nama Lengkap"), ("nik", "NIK"), ("tempatlahir", "Tempat Lahir"), ("tanggallahir", "Tgl/Bln/Th"),
      ("sex", "JK"), ("status_kawin", "Stat Kwn"), ("golongan_darah_id", "Gol. Drh"), ("kk_level", "SHDK"),
      ("agama_id", "Agama"), ("pendidikan_kk_id", "Pendidikan Terakhir"), ("akta_lahir", "No Akta Lahir"),
      ("pekerjaan_id", "Pekerjaan"), ("nama_ibu", "Nama Ibu"), ("nama_ayah", "Nama Ayah"), ("ktp_el", "KTP-eL"),
      ("status_rekam", "Stat Rkm")],
     ambiguous=[("status_dasar", "Status", "BIP 'Status' holds e-KTP issuance state (SDH DPT), not alive/dead")],
     notes="Buku Induk Penduduk e-KTP layout: abbreviated headers (JK, Stat Kwn, Gol. Drh, Stat Rkm, Wjb KTP).")
pair("E17", "khanza-siak", "id-id", "khanza__pasien", "siak__format_siak",
     [("no_ktp", "NIK"), ("nm_pasien", "Nama Penduduk"), ("tmp_lahir", "Tempat Lahir"), ("tgl_lahir", "Tanggal Lahir"),
      ("jk", "Kelamin"), ("nm_ibu", "Ibu"), ("stts_nikah", "Status Kawin"), ("agama", "Agama"), ("alamat", "Alamat"),
      ("pnd", "Pendidikan"), ("pekerjaan", "Pekerjaan"), ("gol_darah", "Gol. Darah"), ("cacat_fisik", "Cacat")],
     ambiguous=[("kd_kec", "Kecamatan", "code vs. name of the same attribute"),
                ("kd_kel", "Desa/Kel", "code vs. name of the same attribute")],
     notes="Hospital patient master vs. civil registry export (NIK verification scenario).")
pair("E18", "khanza-opensid", "id-id", "khanza__pasien", "opensid__tweb_penduduk",
     [("nm_pasien", "nama"), ("no_ktp", "nik"), ("jk", "sex"), ("tmp_lahir", "tempatlahir"), ("tgl_lahir", "tanggallahir"),
      ("nm_ibu", "nama_ibu"), ("alamat", "alamat_sekarang"), ("gol_darah", "golongan_darah_id"),
      ("pekerjaan", "pekerjaan_id"), ("stts_nikah", "status_kawin"), ("agama", "agama_id"), ("no_tlp", "telepon"),
      ("pnd", "pendidikan_kk_id"), ("cacat_fisik", "cacat_id"), ("email", "email"), ("no_peserta", "no_asuransi"),
      ("kd_pj", "id_asuransi"), ("bahasa_pasien", "bahasa_id")],
     notes="Same GT as pilot #1 (ddl_pilot.py).")
pair("E19", "khanza-siak", "id-id", "khanza__pasien", "siak__bip_ektp",
     [("nm_pasien", "Nama Lengkap"), ("no_ktp", "NIK"), ("tmp_lahir", "Tempat Lahir"), ("tgl_lahir", "Tgl/Bln/Th"),
      ("jk", "JK"), ("stts_nikah", "Stat Kwn"), ("gol_darah", "Gol. Drh"), ("agama", "Agama"),
      ("pnd", "Pendidikan Terakhir"), ("pekerjaan", "Pekerjaan"), ("nm_ibu", "Nama Ibu")],
     notes="Abbreviated on BOTH sides (jk/JK, stts_nikah/Stat Kwn, gol_darah/Gol. Drh).")
pair("E20", "opensid-fhir", "id-en", "opensid__tweb_penduduk", "fhir__Patient",
     [("nik", "identifier"), ("nama", "name"), ("sex", "gender"), ("tanggallahir", "birthDate"),
      ("alamat_sekarang", "address"), ("status_kawin", "maritalStatus"), ("telepon", "telecom"),
      ("bahasa_id", "communication"), ("status_dasar", "deceased[x]"), ("foto", "photo")],
     gt_n1=[("email", "telecom")],
     notes=BASE_FHIR + " status_dasar (HIDUP/MATI/PINDAH) -> deceased[x] is lossy.")

# ---- Group 3: SIAKAD -> PDDikti Feeder (id-id, mostly near-identical names) ----
pair("E21", "siakad-feeder", "id-id", "siakad__siakad_mahasiswa", "feeder__InsertBiodataMahasiswa",
     same_names("siakad__siakad_mahasiswa", "feeder__InsertBiodataMahasiswa"),
     ambiguous=[("no_kps", "nomor_kps", "duplicate KPS column in source")],
     notes="Easy control: SIAKAD built around Feeder naming.")
pair("E22", "siakad-feeder", "id-id", "siakad__siakad_matakuliah", "feeder__InsertMataKuliah",
     [("id_prodi_ws", "id_prodi"), ("kode_matakuliah", "kode_mata_kuliah"), ("nama_matakuliah", "nama_mata_kuliah"),
      ("id_jenis_matakuliah", "id_jenis_mata_kuliah"), ("id_kelompok_matakuliah", "id_kelompok_mata_kuliah"),
      ("sks_matakuliah", "sks_mata_kuliah"), ("sks_tatapmuka", "sks_tatap_muka")]
     + same_names("siakad__siakad_matakuliah", "feeder__InsertMataKuliah", exclude={"id_prodi"}),
     ambiguous=[("id_prodi", "id_prodi", "local key; the Feeder UUID is in id_prodi_ws")],
     notes="Trap: identical name id_prodi is the LOCAL key; the correct push mapping is id_prodi_ws -> id_prodi.")
pair("E23", "siakad-feeder", "id-id", "siakad__siakad_kelas", "feeder__InsertKelasKuliah",
     [("id_prodi_ws", "id_prodi"), ("id_matkul_ws", "id_matkul")]
     + same_names("siakad__siakad_kelas", "feeder__InsertKelasKuliah", exclude={"id_prodi"}),
     ambiguous=[("id_prodi", "id_prodi", "local key; the Feeder UUID is in id_prodi_ws")])
pair("E24", "siakad-feeder", "id-id", "siakad__siakad_akm", "feeder__InsertPerkuliahanMahasiswa",
     [("id_registrasi_mahasiswa_ws", "id_registrasi_mahasiswa"), ("id_status_mahasiswa_ws", "id_status_mahasiswa"),
      ("sks_total", "total_sks")]
     + same_names("siakad__siakad_akm", "feeder__InsertPerkuliahanMahasiswa", exclude={"id_status_mahasiswa"}),
     ambiguous=[("id_status_mahasiswa", "id_status_mahasiswa", "local copy vs. *_ws Feeder value")],
     notes="AKM = aktivitas kuliah mahasiswa.")
pair("E25", "siakad-feeder", "id-id", "siakad__siakad_riwayatpendidikan", "feeder__InsertRiwayatPendidikanMahasiswa",
     [("id_mahasiswa_ws", "id_mahasiswa"), ("id_prodi_ws", "id_prodi")]
     + same_names("siakad__siakad_riwayatpendidikan", "feeder__InsertRiwayatPendidikanMahasiswa",
                  exclude={"id_mahasiswa", "id_prodi"}),
     ambiguous=[("id_mahasiswa", "id_mahasiswa", "local key"), ("id_prodi", "id_prodi", "local key")])
pair("E26", "siakad-feeder", "id-id", "siakad__siakad_kurikulum", "feeder__InsertKurikulum",
     [("id_prodi_ws", "id_prodi")]
     + same_names("siakad__siakad_kurikulum", "feeder__InsertKurikulum", exclude={"id_prodi"}),
     ambiguous=[("id_prodi", "id_prodi", "local key")])

# ---- Group 4: other systems -> Feeder ----
pair("E27", "slims-feeder", "en-id", "slims__member", "feeder__InsertBiodataMahasiswa",
     [("member_name", "nama_mahasiswa"), ("gender", "jenis_kelamin"), ("birth_date", "tanggal_lahir"),
      ("member_address", "jalan"), ("member_email", "email"), ("postal_code", "kode_pos")],
     ambiguous=[("member_phone", "handphone", "generic phone vs. mobile/landline split (telepon)")],
     notes="Natural EN->ID pair: campus library (SLiMS, English schema) vs. PDDikti student biodata.")
pair("E28", "khanza-feeder", "id-id", "khanza__pasien", "feeder__InsertBiodataMahasiswa",
     [("nm_pasien", "nama_mahasiswa"), ("jk", "jenis_kelamin"), ("tmp_lahir", "tempat_lahir"),
      ("tgl_lahir", "tanggal_lahir"), ("agama", "id_agama"), ("no_ktp", "nik"), ("alamat", "jalan"),
      ("email", "email"), ("nm_ibu", "nama_ibu_kandung"), ("cacat_fisik", "id_kebutuhan_khusus_mahasiswa")],
     ambiguous=[("no_tlp", "handphone", "single phone column vs. telepon/handphone split"),
                ("kd_kel", "kelurahan", "code vs. name")],
     notes="Campus clinic scenario: abbreviated (Khanza) vs. descriptive (Feeder) Indonesian.")


def validate(p):
    cols = {k: {c["name"] for c in json.loads((SCHEMAS / f"{p[k]}.json").read_text())["columns"]} for k in ("source", "target")}
    for field in ("gt", "gt_n1", "ambiguous"):
        for s, t, *_ in p[field]:
            assert s in cols["source"], f"{p['id']} {field}: {s!r} not in {p['source']}"
            assert t in cols["target"], f"{p['id']} {field}: {t!r} not in {p['target']}"
    srcs, tgts = [s for s, _ in p["gt"]], [t for _, t in p["gt"]]
    assert len(srcs) == len(set(srcs)) and len(tgts) == len(set(tgts)), f"{p['id']}: gt is not 1:1"
    used_t = set(tgts)
    assert all(t in used_t for _, t in p["gt_n1"]), f"{p['id']}: gt_n1 target not used in gt"


if __name__ == "__main__":
    for p in P:
        validate(p)
    OUT.write_text(json.dumps(P, ensure_ascii=False, indent=1))
    print(f"{len(P)} pairs, {sum(len(p['gt']) for p in P)} gt, {sum(len(p['gt_n1']) for p in P)} n:1, "
          f"{sum(len(p['ambiguous']) for p in P)} ambiguous")
    for p in P:
        print(f"{p['id']} {p['group']:15} {p['lang']} {p['source']:34} -> {p['target']:42} gt={len(p['gt'])}")
