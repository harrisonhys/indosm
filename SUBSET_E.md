# IndoSM sub-set E — skema sistem operasional ↔ standar (DRAFT)

Status: **draf satu anotator (Claude), belum diadjudikasi.** 54 pasangan pengembangan (+ 18 pasangan konfirmasi held-out, lihat bawah), 401 korespondensi 1:1, ditambah 82 n:1 dan 46 kasus ambigu. Awalnya 28 pasangan (E01–E28); pada 27 Okt ditambah 26 pasangan Khanza→FHIR (E29–E54, `draft_pairs_e_more.py`), sehingga grup khanza-fhir menjadi 40 pasangan. Aturan tanda vital ada di docstring skrip tersebut.

## Isi

| Grup | Bahasa | Pasangan | Sumber → target | Karakter |
| --- | --- | --- | --- | --- |
| khanza-fhir | ID→EN | E01–E14 (14) | SIMRS Khanza → FHIR R4 (Patient, Practitioner, Location, Encounter, Condition, MedicationRequest, Medication, Organization, ServiceRequest, DiagnosticReport, Observation) | singkatan berat (`nm_`, `kd_`, `stts_`, `tgl_`), target berstruktur (path FHIR) |
| opensid-siak | ID→ID | E15–E16 (2) | OpenSID `tweb_penduduk` → format ekspor SIAK, format BIP e-KTP | snake_case vs label manusia; BIP bersingkatan (`JK`, `Stat Kwn`, `Gol. Drh`) |
| khanza-siak / khanza-opensid | ID→ID | E17–E19 (3) | Khanza `pasien` → SIAK, OpenSID, BIP e-KTP | singkatan vs deskriptif, atau singkatan di kedua sisi |
| opensid-fhir | ID→EN | E20 (1) | OpenSID → FHIR Patient | lintas bahasa natural |
| siakad-feeder | ID→ID | E21–E26 (6) | SIAKAD → PDDikti Feeder WS (Insert*) | **kontrol mudah** (nama hampir identik) + jebakan `id_prodi` lokal vs `id_prodi_ws` |
| slims-feeder | EN→ID | E27 (1) | SLiMS `member` → Feeder biodata mahasiswa | lintas bahasa arah sebaliknya |
| khanza-feeder | ID→ID | E28 (1) | Khanza `pasien` → Feeder biodata mahasiswa | skenario klinik kampus |

File:
- `data/subset_e/schemas/*.json` — 41 skema (nama, tipe, deskripsi bila sumber menyediakan), dibangkitkan oleh `build_schemas.py`
- `data/subset_e/pairs_e.json` — GT; **sumber kebenaran mulai sekarang** (dibuat sekali oleh `draft_pairs_e.py`)
- `data/subset_e/raw/` — file sumber asli; **jangan dirilis** (lihat lisensi)
- `run_e.py` — baseline schema-only → `results/subset_e_scores.csv`

## Provenance & lisensi

| Sumber | Versi yang dipakai | Lisensi | Implikasi untuk rilis benchmark |
| --- | --- | --- | --- |
| SIMRS Khanza (`mas-elkhanza/SIMRS-Khanza`, `sik.sql`) | master @ `8a6431dcb3` (diunduh 26 Okt 2026) | **Lisensi khusus** (`lisensi.txt`): gratis, open source, boleh dipakai siapa saja; **dilarang memperjualbelikan/mengambil keuntungan tanpa izin Khanza.Soft Media**. Tidak berlisensi OSI dan tidak mengatur redistribusi/turunan secara eksplisit | Riset non-komersial aman. **Minta izin tertulis sebelum merilis** nama kolom + GT. Jangan redistribusi `sik.sql` |
| OpenSID (`OpenSID/OpenSID`, `contoh_data_awal_20210901.sql`) | master @ `4c68b749f2` (1 Sep 2021). Branch `umum` sekarang memakai migrasi PHP | GPL-3.0 + klausul versi Umum/Premium | Turunan skema boleh dirilis dengan GPL-3.0 + atribusi |
| Template impor OpenSID: `format-siak.xls`, `format-bip-ektp.xls` | branch `umum` | GPL-3.0 (bagian dari OpenSID) | **Hanya header yang dipakai.** Baris contoh `format-bip-ektp.xls` tampak berisi data pribadi asli (NIK + nama), jadi file itu tidak disimpan; headernya diketik ulang di `build_schemas.py` |
| SLiMS 9 Bulian (`slims/slims9_bulian`, `install/senayan.sql`) | master @ `1d892599c1` | GPL-3.0 | Sama seperti OpenSID |
| SIAKAD Feeder (`idiknursidik/siakad`, `siakad.sql`) | master @ `05f0b8fe19` (Apr 2022) | **Tidak jelas.** GitHub mendeteksi "MIT", tetapi `license.txt` adalah lisensi MIT milik framework CodeIgniter, bukan lisensi aplikasi dari penulisnya | Hubungi penulis, atau ganti dengan SIAKAD berlisensi jelas sebelum rilis |
| HL7 FHIR R4 4.0.1 StructureDefinition | `hl7.org/fhir/R4/*.profile.json` | CC0 (spesifikasi); "FHIR" merek dagang HL7 | Bebas |
| PDDikti Feeder Web Service User Guide v2.2 (07-12-2020) | PDF yang dihosting stk.uss.ac.id | Dokumentasi publik tanpa lisensi eksplisit | Rilis nama field saja (spesifikasi antarmuka), dengan sitasi. Idealnya ambil versi terbaru dari PDDikti/GetDictionary |
| SIAK (Dukcapil) | — | — | **Tidak ada skema resmi yang publik.** Nama field yang beredar (`NAMA_LGKP`, `TMPT_LHR`, …) berasal dari laporan kebocoran data 2023, jadi **sengaja tidak dipakai**. Pengganti: header format ekspor SIAK dari template OpenSID |
| **Set konfirmasi held-out** (`pairs_confirm.json`, `draft_confirm.py`) | | | |
| `mfarim/laravel-rekam-medis-puskesmas` (migrasi Laravel) | `1767a3ff14` (Apr 2019) | MIT (penulis aplikasi) | Boleh dirilis dengan atribusi |
| `elingp/sistem-informasi-puskesmas` (migrasi Laravel) | `be12a98aaf` (Des 2020) | MIT (penulis aplikasi) | Boleh dirilis dengan atribusi |
| `Kriss245/Sipograf-Sistem-Informasi-Posyandu-dengan-KMS` (`dbsipograf.sql`) | `3ddc160c19` (Mei 2025) | MIT (penulis aplikasi) | Boleh dirilis dengan atribusi |
| `arfandotid/ci_rekammedis` (`rekam_medis.sql`) | `606cd16795` (Des 2019) | **Tidak jelas**: `license.txt` adalah MIT milik CodeIgniter (BCIT), sama seperti kasus SIAKAD | Riset saja; tahan sampai ada izin |
| `Slyzyy/TUBES_WEBPRO_e-Puskesmas` (`db_puskesmas.sql`) | `82f97d411f` (Okt 2023) | **Tidak jelas** (lisensi CodeIgniter Foundation) | Riset saja; tahan sampai ada izin |
| OpenSID modul kesehatan (`struktur_tabel/*_create_posyandu_table.php`) | branch `umum` @ `661a8884a8` | GPL-3.0 | Sama seperti OpenSID |
| Halaman resource FHIR R4 (`raw/fhir_pages/*.html`, untuk katalog tahap 1) | hl7.org/fhir/R4 | CC0 | Bebas |
| *Ditolak:* `fikihafizalfarisi/royal_master` (`dbo.sql`, 195 tabel SQL Server "ROYAL_EMR") | — | Lisensi CodeIgniter; tampak skema EMR produksi rumah sakit yang diekspor dari server internal | **Tidak dipakai**: otorisasi unggahan tidak jelas (prinsip sama dengan SIAK). File mentah sudah dihapus (27 Okt 2026) |
| *Ditolak:* `basoro/mlite` | — | GPL-3.0 | Memakai basis data Khanza, jadi bukan sistem independen |
| *Ditolak:* `aisahana/eclinic_api` | — | MIT | Identifier berbahasa Inggris; kandidat kondisi EN→FHIR terpisah |

Rekomendasi rilis: anotasi GT (karya sendiri) dengan CC-BY-4.0; file skema dengan lisensi sumber masing-masing; sub-set Khanza dan SIAKAD ditahan sampai ada izin.

## Set konfirmasi held-out (27 Okt 2026)

18 pasangan non-Khanza → FHIR (C01–C18, grup `confirm-fhir`), 69 gt, 6 n:1, 10 ambigu, dari 6 sistem. Set ini disimpan **terpisah** dari `pairs_e.json` (`pairs_confirm.json`, `pairs_confirm_large.json`) dan di-hash di `PREREG_CONFIRM.md` sebelum run pertama. Konvensinya sama, dengan dua catatan baru:
- **Ambiguitas di tingkat resource:** `posyandu` → Organization (Location juga dapat dibela); skor untuk jawaban Location adalah 0.
- **Kolom yang generik** (`id`, `nama`) tetap di-gt walaupun tanpa nama tabel hampir tidak mungkin ditebak.

Setelah dipakai untuk konfirmasi, set ini tidak lagi "bersih" untuk pengembangan berikutnya.

## Konvensi anotasi (draf, perlu disepakati anotator)

1. **Unit** = kolom (DDL) ↔ elemen (FHIR element path tanpa prefix resource, mis. `contact.name`, `value[x]`; field Feeder; header kolom SIAK/BIP).
2. **FHIR tidak di-*expand* ke komponen datatype** (`name` bukan `name.family`). Akibatnya beberapa kolom sumber jatuh ke satu elemen; yang paling representatif masuk `gt`, sisanya `gt_n1` (tidak dinilai). Contoh: `tgl_registrasi` → `period` (gt), `jam_reg` → `period` (n:1).
3. **Hanya FHIR R4 dasar.** Ekstensi SATUSEHAT tidak dimodelkan. Kolom seperti `tmp_lahir`, `agama`, `nm_ibu` vs Patient menjadi negatif sungguhan. Varian "R4 + ekstensi SATUSEHAT" bisa jadi ablasi.
4. **Kode vs nama atribut yang sama** (`kd_kec` vs `Kecamatan`) → `ambiguous`, bukan gt.
5. **FK yang hanya terhubung lewat join** (`id_kk` → `Nomor KK`) → `ambiguous`.
6. **Kunci lokal vs kunci sistem target** (`id_prodi` lokal vs `id_prodi_ws` = UUID Feeder): gt adalah kolom yang benar untuk *push* ke target.
7. Kolom audit (`created_at` ↔ `Tgl Entri`) dihitung match.

## Baseline (schema-only, nama kolom saja, R@|GT| rata-rata per grup)

Tujuannya *sanity check* GT, bukan hasil: kontrol mudah harus mudah, pasangan bersingkatan/lintas bahasa harus sulit.

| Metode | siakad-feeder (kontrol) | opensid-siak | khanza-siak | khanza-opensid | khanza-feeder | khanza-fhir | opensid-fhir | slims-feeder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COMA | 0,861 | 0,690 | 0,580 | 0,444 | 0,500 | **0,153** | 0,300 | 0,333 |
| Similarity Flooding | 0,861 | 0,391 | 0,535 | 0,278 | 0,400 | 0,090 | 0,400 | 0,333 |
| Cupid | 0,335 | 0,186 | 0,000 | 0,000 | 0,000 | 0,048 | 0,000 | 0,000 |
| bge-m3 | 0,861 | 0,491 | 0,374 | 0,389 | 0,200 | 0,178 | 0,500 | 0,333 |
| Qwen3-8B | 0,817 | 0,758 | 0,864 | 0,778 | 0,800 | **0,528** | 0,800 | 0,833 |

Per bahasa (R@|GT|): COMA ID–ID 0,72 / ID–EN 0,16 / EN–ID 0,33; Qwen3-8B 0,81 / 0,55 / 0,83. Jaccard = 0 di semua pasangan (berbasis instance, tidak ada data). Median waktu Qwen 17 detik per pasangan.

Bacaan cepat:
- Kontrol berjalan sesuai harapan: semua metode ±0,86 di SIAKAD↔Feeder. Qwen sedikit di bawah COMA di E22–E24, kemungkinan karena terjebak `id_prodi` lokal vs `id_prodi_ws`.
- **Khanza↔FHIR adalah sub-grup tersulit** (COMA 0,15, LLM 0,53), terutama Encounter/MedicationRequest/ServiceRequest (E05, E07, E10, E12 ≤ 0,43 untuk LLM). Ini kandidat terbaik untuk menguji hybrid + kamus singkatan (RQ2/RQ4).
- Gap klasik vs LLM di pasangan bersingkatan ID–ID (khanza-*) 30–40 poin, konsisten dengan pilot #1.

Keterbatasan: GT satu anotator; FHIR R4 tanpa ekspansi datatype; skema publik di GitHub kemungkinan ada di data latih LLM.

## Langkah berikutnya

1. Anotator kedua (idealnya satu orang rekam medis/SIMRS dan satu orang PDDikti) mengisi ulang `gt` secara independen dan menyelesaikan `ambiguous`; hitung kappa.
2. Kirim permintaan izin ke Khanza.Soft Media dan penulis `idiknursidik/siakad`, atau ganti SIAKAD dengan sumber berlisensi jelas.
3. Ablasi: tambahkan tipe kolom + deskripsi FHIR ke representasi kolom; varian FHIR + ekstensi SATUSEHAT.
4. Pasangan Khanza dari versi lama (mis. 2019) dibanding versi sekarang sebagai sub-set "belum terlihat" yang lebih sulit dikontaminasi.
