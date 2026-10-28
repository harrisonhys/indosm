# Rencana paper ramping (28 Okt 2026)

Tujuan: menyelesaikan satu paper dengan bukti yang sudah ada dan **membekukan eksperimen**. Tidak ada ablasi baru kecuali tiga butir "wajib" di bawah.

## Klaim (sesuai bukti)

1. **Data:** skema operasional open-source Indonesia (SIMRS/puskesmas) → FHIR R4 adalah tolok ukur yang sulit: kolom bersingkatan, kode lokal, dan FK. Header portal Satu Data justru mudah (pilot #1: 6% bersingkatan, COMA ≈ LLM).
   *Bukti:* PILOT_REPORT.md, SUBSET_E.md (baseline klasik vs LLM).
2. **Metode:** untuk target besar (289 elemen FHIR), *two-stage* dengan **satu resource utama** (pilih resource dari deskripsi `definition` FHIR, lalu matching hanya ke resource peringkat 1) menyamai atau melampaui LLM penuh dengan ±50% token.
   *Bukti:* Qwen dev41 +13,7 poin; set konfirmasi pra-registrasi +12,2 (p_Holm 0,14, arah konsisten); **GLM-5.3 Flash tanpa penyetelan ulang: dev41 +12,7 (p = 0,016), gabungan +11,2 (p = 0,010)**.
3. **Analisis kegagalan:** hambatan utama bukan bahasa atau singkatan, tetapi **pemodelan FHIR**.
   - Resource yang dirujuk lewat FK (`no_rawat` → Encounter) "menyerap" prediksi.
   - Rujukan dan order tidak dikenali sebagai ServiceRequest.
   - Deskripsi panjang, glosarium ID→EN, dan instruksi negatif tidak membantu. Instruksi negatif bahkan berefek *priming*.
   - Kamus singkatan hasil tambang membantu retrieval, tetapi tidak membantu LLM penuh.

## RQ yang dipertahankan / ditunda

| RQ PRD | Status di paper |
| --- | --- |
| RQ1 klasik vs LLM pada skema bersingkatan | **dipertahankan** (pilot + baseline sub-set E) |
| RQ2 pipeline hybrid / bertahap untuk target besar | **inti paper** |
| RQ4 kamus singkatan | **dipertahankan** sebagai hasil sekunder (membantu retrieval saja) |
| RQ3 lintas bahasa penuh (3 varian bahasa) | **ditunda** → keterbatasan / *future work*; data pilot cukup untuk satu paragraf |
| RQ5 model terbuka | **dipertahankan**: Qwen3-8B lokal vs GLM-5.3 Flash (open-weight, via API). Efek metode tereplikasi di kedua model; GLM +16..+24 poin |
| Baseline Columbo | **ditunda**: disebut di related work, bukan dieksperimenkan |

## Butir wajib sebelum submit

| # | Butir | Siapa | Waktu | Status |
| --- | --- | --- | --- | --- |
| 1 | Anotator kedua mengisi `annotation/anotasi_kedua.xlsx` (59 pasangan, 713 kolom), lalu `python annotation_kit.py score <file>`, lalu adjudikasi `ketidaksepakatan.csv` dan rescore semua tabel hasil (dari cache) | **Anda** mencari anotator; skrip siap | ±4 jam kerja anotator + 1 hari adjudikasi | kit siap |
| 2 | Lengan model kedua untuk 4 konfigurasi utama × 59 pasangan | Claude | — | **selesai** (GLM-5.3 Flash, 28 Okt) |
| 3 | Kirim permintaan izin rilis (`annotation/izin_rilis.md`) | **Anda** | 30 menit; jawaban tidak ditunggu untuk submit | draf siap |

Tanpa izin, paper tetap bisa terbit dengan angka agregat. Dataset dirilis hanya untuk sumber berlisensi jelas (OpenSID, SLiMS, FHIR, mfarim, elingp, Sipograf), dan sisanya "tersedia atas permintaan setelah izin".

## Garis besar naskah (±8 halaman)

1. Pendahuluan: integrasi data SIMRS → SATUSEHAT/FHIR, kenapa schema matching.
2. Related work: Valentine, LLM matchers (Magneto, dll.), Columbo, benchmark berbahasa non-Inggris.
3. Data: pilot Satu Data → sub-set E → set konfirmasi held-out; konvensi GT; lisensi.
4. Metode: llm-full, hybrid, two-stage (union / primary), katalog tahap 1, kamus.
5. Hasil: baseline (RQ1); target besar + two-stage (RQ2); kamus (RQ4); konfirmasi pra-registrasi.
6. Analisis kegagalan: penyerapan Encounter, ServiceRequest, ablasi yang gagal.
7. Keterbatasan: satu/dua anotator, satu run per konfigurasi, model 8B, power.
8. Kesimpulan.

## Kandidat venue (SINTA 2, dicek 28 Okt 2026; konfirmasi peringkat di sinta.kemdiktisaintek.go.id sebelum submit)

1. **IJCCS (UGM)**: SINTA 2, SK 177/E/KPT/2024, periode 2023–2028. Berbahasa Inggris, terbit Jan/Apr/Jul/Okt. Pilihan utama: akreditasinya paling jelas masa berlakunya.
2. **Jurnal RESTI (IAII)**: SINTA 2 (SK terbaru belum terverifikasi). Menerima artikel bahasa Inggris, submisi dan review gratis, frekuensi terbit tinggi. Pilihan cepat.
3. *Opsi naik kelas:* **JISEBI (Unair)**: kini SINTA 1 (SK 79/E/KPT/2023, 2023–2027) menurut situsnya. Ruang lingkup sistem informasi/integrasi data paling cocok, tetapi terbit hanya 2×/tahun (Apr/Okt).

Tidak disarankan: JTIIK (SK di daftar publik tampak berakhir 2024) dan Khazanah Informatika (SK berlaku sampai vol. 11 no. 2, 2025), sampai status akreditasi barunya jelas. Jurnal rekam medis/informatika kesehatan yang ditemukan rata-rata SINTA 3–5.

**Dipilih: IJCCS (28 Okt).** Naskah: `paper/ijccs/manuscript.md`, dibangun dengan `python paper/ijccs/build_ijccs.py` menjadi `paper/ijccs/IJCCS_manuscript.docx`, memakai template resmi bahasa Inggris (A4, margin 3 cm, TNR 11). Hasilnya 11 halaman (render LibreOffice), abstrak ID 176 kata / EN 187 kata, judul 10 kata, 29 referensi IEEE berurutan kemunculan, 8 tabel + 1 gambar. Sisa isian: nama/afiliasi/email penulis, `[TBD: κ]`, acknowledgements; lalu cek ulang jumlah halaman di Microsoft Word.

**Revisi setelah review (28 Okt):**
- Judul baru: *Single-Resource LLM Schema Matching of Indonesian Health Systems to FHIR*.
- Tabel baru: P/R/F1 threshold-free; stage-1 dengan stage-2 kondisional; absorpsi Encounter dihitung ulang dengan katalog `def` untuk dua model.
- Prosedur metrik ditulis lengkap dengan contoh, keluarga uji konfirmatori dinyatakan eksplisit, dan pernyataan pra-registrasi ditulis jujur.
- Hasil: 11 halaman, abstrak 181/196 kata. Tanggapan poin per poin ada di `paper/ijccs/tanggapan_reviewer.md`, dan analisisnya di `revision_analyses.py`.
- Belum: κ (annotator kedua), data penulis, URL repo bersih.

**Revisi putaran 2 (28 Okt):**
- Tiga kebijakan evaluasi (neutral, deployment-strict, lenient); hasil tetap sama tanpa penyaringan berbasis gold.
- Ablasi oracle-B: prefiks membantu Qwen (+5,0), efeknya kecil pada GLM (+2,1, tidak signifikan); primary identik dengan oracle-B bila rank-1 benar.
- Baseline embedding stage-1: top-1 27%, di bawah llm-full.
- Klaim dibatasi ke zero-training/schema-only/single-resource.
- 12 halaman (sisa margin ±¾ halaman). Analisis ada di `revision2_analyses.py`.

## Jadwal realistis

- **Minggu 1:** draf bagian 3–6 **selesai 28 Okt** (`paper/draft_sections_3-6.md`, bahasa Inggris; statistik data dari `paper_stats.py`). Sisanya dikerjakan paralel dengan anotator kedua.
- Bagian 1–2 dan 7–8 juga **selesai 28 Okt** (`paper/draft_sections_1-2_7-8.md`). 29 referensi terverifikasi ada di `paper/references.md`.
- **Minggu 2:** adjudikasi, rescore, finalisasi angka `[TBD-κ]`, gabung jadi satu naskah + abstrak, format ke template venue, revisi.
- Submit di akhir minggu 2–3.
