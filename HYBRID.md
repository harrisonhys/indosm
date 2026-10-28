# IndoSM — Pipeline hybrid + kamus singkatan Khanza (RQ2, RQ4)

26 Okt 2026 · evaluasi di sub-set E (28 pasangan, fokus grup khanza-fhir, n = 14) · Qwen3-8B lokal + bge-m3 (Ollama, temp 0, seed 0)

## Ringkasan

1. **Kamus singkatan menolong retrieval, tidak menolong LLM penuh.** Hybrid naik +14 poin R@|GT| di khanza-fhir (k=5, p=0,008; 9 menang / 0 kalah) dan embedding naik +8 poin. Pada LLM penuh efeknya nol (−0,9 poin, p=0,59; 11 dari 14 pasangan identik). Qwen3-8B tampaknya sudah bisa membaca singkatan Khanza sendiri. **H4 didukung** untuk metode berbasis retrieval.
2. **H2 (hybrid lebih akurat dan lebih murah) ditolak pada ukuran skema ini.**
   - Hybrid tanpa kamus kalah telak dari LLM penuh (−28 poin pada k=5, p=0,002).
   - Konfigurasi hybrid terbaik (k=10 + kamus) hanya menyamai LLM penuh: F1 −0,6 poin (p=0,81), R@|GT| −6,5 poin (p=0,18).
   - Hybrid butuh **3,5–4× token prompt** (1.494 vs 375 per pasangan) dan ±37% lebih lama.
   - Penyebabnya: skema target kecil (5–46 kolom) sehingga muat utuh di prompt, sedangkan hybrid mengulang daftar kandidat per kolom sumber.
3. **Batas atas retrieval adalah hambatan utama.** Pada khanza-fhir, recall@5 bge-m3 hanya 0,49 (0,54 dengan kamus) dan recall@10 0,58 (0,69). LLM penuh mencapai 0,55, yaitu sudah di atas batas atas hybrid k=5.
4. Pasangan yang tetap sulit untuk semua konfigurasi (R@|GT| ≤ 0,43): E05 `reg_periksa`→Encounter, E09 `databarang`→Medication, E10 `kamar_inap`→Encounter, E14 `detail_periksa_lab`→Observation. E07 dan E12 juga ≤ 0,25 untuk hybrid.

**Implikasi untuk paper:** hybrid hanya layak diusulkan bila targetnya besar, misalnya seluruh spesifikasi FHIR (ratusan elemen) atau katalog standar Satu Data, di mana prompt penuh tidak muat atau mahal. Eksperimen itulah yang perlu dijalankan berikutnya untuk menguji H2 dengan adil.

**Status terbaru (27 Okt, n = 41, target besar 289 elemen):** konfigurasi terbaik non-oracle adalah **two-stage dengan satu resource utama** (katalog `def`, resource peringkat 1 dari tahap 1). R@|GT| 0,407 vs llm-full+dict 0,270 (+13,7 poin, CI +3,8..+23,7) dengan 55% token. Sisa gap ke oracle (0,552) hampir seluruhnya akibat salah pilih resource di tahap 1. Upaya memperbaikinya lewat prompt tahap 1 (katalog `elements`, instruksi anti-FK) tidak menaikkan recall. **Konfirmasi pra-registrasi pada 18 pasangan non-Khanza:** arah dan besar efek tereplikasi (+12,2 poin atas llm-full), tetapi belum signifikan (p_Holm = 0,14). **Model kedua (GLM-5.3 Flash, konfigurasi tidak disetel ulang):** keunggulan rank1 tereplikasi (+12,7 poin dev41, p = 0,016; +11,2 gabungan, p = 0,010). Lihat bagian-bagian terakhir.

## Kamus singkatan (`mine_abbrev.py` → `data/abbrev_khanza.json`)

Ditambang otomatis dari DDL 1.189 tabel Khanza, tanpa GT dan tanpa kamus eksternal. Metodenya:

| Metode | Ide | Entri |
| --- | --- | --- |
| context | dua identifier yang berbeda satu token (`nm_pasien` ~ `nama_pasien` → nm = nama) | 15 |
| acronym | satu token vs 2–3 token berinisial sama (`jk` ~ `jenis_kelamin`) | 2 |
| subseq | token miskin vokal → kata kosakata Khanza yang memuatnya sebagai subsekuens, diurutkan menurut kesamaan token tetangga (`rkm` dan `rekam` sama-sama bertetangga dengan `medis`) | 184 |

Presisi (dinilai oleh saya, satu penilai, `data/abbrev_judgments.json`):
- **27/36 (75%)** pada token yang muncul di tabel evaluasi. Angka ini kemungkinan optimistis, karena aturan penambang saya setel dengan melihat token-token ini.
- **10/40 (25%)**, plus 5 ragu, pada sampel acak di luar tabel evaluasi. Ekor panjangnya adalah akronim medis/administrasi (`ekg`, `ctg`, `apd`, `rtl`, `ktp`, `rs`) yang tidak bisa dipecahkan dengan subsekuens.
- Contoh benar: `nm`→nama, `kd`→kode, `tgl`→tanggal, `jk`→jenis kelamin, `brng`→barang, `stts`→status, `almt`→alamat, `sps`→spesialis, `trf`→tarif.
- Contoh salah: `ijn`→ipsrsjenisbarang (izin), `rkm`→rekomendasi (rekam), `pnd`→pengadaan (pendidikan), dan `almt_tgl`, di mana `tgl` di sini berarti *tinggal*, bukan tanggal.

## Desain eksperimen (`hybrid.py`, `analyze_hybrid.py`)

| Konfigurasi | Retrieval | LLM | Kamus |
| --- | --- | --- | --- |
| emb / emb+dict | bge-m3 atas nama ternormalisasi (snake/camelCase dipecah) | — | −/+ |
| llm-full / llm-full+dict | — | satu prompt berisi seluruh kolom sumber & target | −/+ |
| hybrid / hybrid+dict | bge-m3 top-k per kolom sumber | satu prompt: tiap kolom sumber + k kandidatnya | −/+ |

Dengan kamus, kolom ditampilkan sebagai `nm_pasien (nama pasien)`, dan teks embedding memakai bentuk ekspansinya. k=5 ditetapkan sebelum melihat hasil; k=10 adalah uji sensitivitas. Uji statistik: Wilcoxon signed-rank berpasangan per pasangan tabel, bootstrap 95% CI atas selisih rata-rata.

## Hasil

### Batas atas retrieval (recall@k bge-m3, khanza-fhir)

| k | 1 | 3 | 5 | 10 |
| --- | --- | --- | --- | --- |
| tanpa kamus | 0,31 | 0,42 | 0,49 | 0,58 |
| dengan kamus | 0,42 | 0,49 | 0,54 | 0,69 |

### R@|GT| per grup

| Konfigurasi | khanza-fhir | khanza-siak | khanza-opensid | opensid-siak | siakad-feeder (kontrol) |
| --- | --- | --- | --- | --- | --- |
| emb | 0,202 | 0,451 | 0,333 | 0,447 | 0,837 |
| emb+dict | 0,285 | 0,619 | 0,444 | 0,478 | 0,833 |
| hybrid k=5 | 0,271 | 0,626 | 0,611 | 0,646 | 0,814 |
| hybrid+dict k=5 | 0,412 | 0,710 | 0,611 | 0,727 | 0,810 |
| hybrid k=10 | 0,326 | 0,671 | 0,667 | 0,677 | 0,823 |
| hybrid+dict k=10 | 0,489 | 0,748 | 0,667 | 0,727 | 0,819 |
| **llm-full** | **0,554** | **0,832** | **0,778** | **0,814** | 0,831 |
| llm-full+dict | 0,545 | 0,832 | 0,722 | 0,795 | 0,831 |

### Uji berpasangan, khanza-fhir (n = 14)

| Perbandingan | Δ R@|GT| [95% CI] | p | Δ F1 | p |
| --- | --- | --- | --- | --- |
| hybrid − llm-full (k=5) | −0,284 [−0,38, −0,19] | 0,002 | −0,249 | 0,002 |
| llm-full+dict − llm-full | −0,009 [−0,04, 0,02] | 0,593 | −0,009 | 0,444 |
| hybrid+dict − hybrid (k=5) | **+0,141** [0,07, 0,22] | 0,008 | +0,099 | 0,041 |
| hybrid+dict − hybrid (k=10) | **+0,163** [0,06, 0,27] | 0,022 | +0,179 | 0,003 |
| hybrid+dict − llm-full (k=10) | −0,065 [−0,18, 0,03] | 0,176 | −0,006 | 0,814 |
| emb+dict − emb | +0,083 [0,02, 0,14] | 0,058 | +0,102 | 0,018 |

Di seluruh sub-set E (n = 28) polanya sama: kamus menaikkan hybrid +9 poin (p=0,001) dan embedding +7 poin (p=0,007), dan tidak berpengaruh pada LLM penuh.

### Biaya per pasangan tabel (rata-rata 28 pasangan, M3 Pro)

| Konfigurasi | Token prompt | Token output | Detik |
| --- | --- | --- | --- |
| llm-full | 375 | 559 | 27 |
| llm-full+dict | 423 | 589 | 27 |
| hybrid k=5 | 837 | 675 | 34 |
| hybrid+dict k=5 | 943 | 701 | 35 |
| hybrid k=10 | 1.323 | 677 | 36 |
| hybrid+dict k=10 | 1.494 | 701 | 37 |

## Catatan metodologis & bug yang sudah diperbaiki

- **Bug parser (sudah diperbaiki sebelum angka di atas):** dengan kamus aktif, Qwen sering mengembalikan label (`"kd_dokter (kode dokter)"`), bukan nama kolom persis, dan versi pertama parser membuangnya. Akibatnya hasil awal sempat menunjukkan "kamus merugikan LLM" (E02: 0,67 → 0,11). Ini artefak. Sekarang label dipetakan kembali ke nama kolom (ada self-check di `hybrid.py`). Skor ulang memakai output LLM yang sama dari cache; tidak ada panggilan baru. Angka sebelum perbaikan disimpan di `results/hybrid_scores_k*_buggy_parser.csv`.
- Satu panggilan sempat macet karena output mengulang. Output kini dibatasi 3.000 token; jawaban normal di bawah 1.000 token.
- Satu run per konfigurasi (temp 0, seed 0). Variansi antar-run belum diukur.
- Prompt LLM penuh di sini (nama saja, tanpa "sample values") sedikit berbeda dari `run_e.py`. Angkanya dekat (0,554 vs 0,528 di khanza-fhir) tetapi tidak identik.
- GT, kamus, dan penilaian presisi semuanya masih dari satu anotator (Claude). Skema publik kemungkinan sudah ada di data latih LLM.

## Uji target besar (gabungan 11 resource FHIR, 289 elemen)

`build_large_target.py` → `data/subset_e/pairs_e_large.json`. Ada 15 pasangan (E01–E14 + E20) dengan 94 korespondensi. Target setiap tabel sumber adalah gabungan seluruh resource (`Patient.birthDate`, `Encounter.period`, …), tanpa petunjuk resource mana yang benar. GT sama, hanya diberi prefiks.

### Hasil (rata-rata 15 pasangan, R@|GT|)

| Konfigurasi | Target kecil (1 resource) | Target besar (289 elemen) | Token prompt kecil → besar |
| --- | --- | --- | --- |
| emb / emb+dict | 0,229 / 0,306 | 0,106 / 0,112 | — |
| hybrid k=5 / +dict | 0,286 / 0,424 | 0,096 / 0,181 | 493 → 658 / 533 → 683 |
| hybrid k=10 / +dict | 0,344 / 0,496 | 0,078 / 0,177 | 726 → 1.042 / 773 → 1.071 |
| **llm-full** / **+dict** | 0,558 / 0,549 | 0,284 / **0,353** | 307 → 1.919 / 340 → 1.964 |

F1 menunjukkan pola yang sama (llm-full+dict 0,270; hybrid+dict 0,135–0,139). Batas atas retrieval runtuh: recall@5 bge-m3 0,22 (0,35 dengan kamus) dan recall@10 0,25 (0,40), dibanding 0,49/0,58 di target kecil.

### Uji berpasangan, target besar (n = 15)

| Perbandingan | Δ R@|GT| [95% CI] | p | Δ F1 | p |
| --- | --- | --- | --- | --- |
| hybrid − llm-full (k=5) | −0,188 [−0,33, −0,04] | 0,028 | −0,135 | 0,041 |
| hybrid+dict − llm-full+dict (k=5)¹ | −0,172 | — | −0,135 | — |
| hybrid+dict − hybrid (k=10) | +0,100 [0,03, 0,18] | 0,028 | +0,082 | 0,018 |
| llm-full+dict − llm-full | +0,068 [−0,02, 0,18] | 0,345 | +0,039 | 0,575 |

¹ selisih rata-rata saja.

### Kebingungan resource

54% prediksi llm-full (59% untuk +dict) dan 70–74% prediksi hybrid jatuh ke resource lain, bukan resource GT. Dari 30 sampel acak prediksi lintas-resource llm-full+dict yang saya nilai (`data/large_target_cross_resource_judgments.json`):
- **6/30 (20%) masih bisa dibenarkan**, kebanyakan FK yang menunjuk resource rujukannya (`no_rawat`→`Encounter.identifier`, `kode_brng`→`Medication.code`, `p_jawab`→`Patient.contact.name`).
- **24/30 adalah kesalahan nyata**: atribut dokter/pegawai masuk ke `Patient.*`, `status` poliklinik masuk ke `MedicationRequest.status`, biaya lab masuk ke `DiagnosticReport.media.comment`.

Jadi penurunan akurasi sebagian besar nyata. Hanya sebagian kecil yang merupakan artefak definisi GT, yaitu presisi sebagai batas bawah.

### Kesimpulan untuk H2

- **H2 tetap ditolak, sekarang dengan alasan berbeda.** Di target besar, hybrid memang jauh lebih hemat token prompt (−66% pada k=5, −46% pada k=10), tetapi akurasinya kira-kira separuh LLM penuh (0,18 vs 0,35). Selisih waktu hampir hilang (25–33 vs 30 detik), karena waktu didominasi token output, bukan prefill.
- Penyebab utamanya batas atas retrieval: bge-m3 tidak bisa memilih resource yang benar dari nama kolom bersingkatan. Rerank yang sebaik apa pun dibatasi recall@10 = 0,40.
- **Kamus singkatan makin berguna saat tugas makin sulit:** +10 poin untuk hybrid (p=0,028), dan +6,8 poin untuk LLM penuh di target besar (tidak signifikan, tetapi arahnya berbalik dari target kecil yang −0,9).
- Untuk paper: pipeline dua tahap yang adil butuh tahap **pemilihan resource/tabel** dulu (table-candidate selection ala LLMatch), baru matching kolom. Itu desain yang lebih realistis untuk skenario ESB.

### Catatan teknis
- Run k=10 sempat gagal dua kali: runner bge-m3 di Ollama crash (`tokenize: EOF`), lalu disk penuh. Embedding kini mencoba ulang hingga 3 kali; semua output LLM yang sudah ada diambil dari cache.
- Mesin uji kehabisan memori: swap mencapai 29 GB pada RAM 18 GB, dengan Qwen 6,3 GB + bge-m3 dimuat bersamaan. Ini memengaruhi angka detik, tetapi tidak memengaruhi akurasi maupun token.

## Pipeline dua tahap: pilih resource → matching kolom (`two_stage.py`, `compare_two_stage.py`)

- **Tahap 1:** LLM melihat daftar kolom sumber (tanpa nama tabel, sama seperti llm-full) dan daftar 11 resource FHIR beserta deskripsi satu barisnya dari StructureDefinition resmi (`short`). Ia memilih 1–3 resource, urut dari yang paling mungkin.
- **Tahap 2**, dua varian:
  - **union**: satu prompt, kolom sumber vs gabungan elemen resource terpilih (rata-rata 67 dari 289 elemen);
  - **per-res**: satu prompt per resource terpilih (rata-rata 2,6 panggilan), lalu prediksinya digabung dengan mengambil confidence tertinggi per pasangan kolom.
- **Oracle** = resource yang benar diberikan (hasil target kecil). Ini batas atas tahap 2.

### Hasil (15 pasangan, target besar 289 elemen)

| Konfigurasi | R@|GT| | F1 | Token prompt | Token output | Detik |
| --- | --- | --- | --- | --- | --- |
| llm-full | 0,284 | 0,231 | 1.919 | 493 | 30 |
| llm-full+dict | 0,353 | 0,270 | 1.964 | 524 | 31 |
| two-stage (union) | 0,319 | 0,245 | 922 | 503 | 25 |
| **two-stage+dict (union)** | **0,400** | **0,330** | **985** | 485 | **24** |
| two-stage per-res | 0,261 | 0,251 | 1.237 | 1.230 | 55 |
| two-stage per-res+dict | 0,283 | 0,274 | 1.364 | 1.257 | 56 |
| *oracle (resource diberikan)* | *0,558* | *0,492* | *307* | *354* | *18* |
| *oracle+dict* | *0,549* | *0,476* | *340* | *428* | *20* |

Token dan detik dua tahap = tahap 1 (±360–390 token) + tahap 2.

### Uji berpasangan (n = 15)

| Perbandingan | Δ R@|GT| [95% CI] | p | Δ F1 | p |
| --- | --- | --- | --- | --- | --- |
| two-stage+dict − llm-full+dict | +0,048 [−0,06, 0,15] | 0,314 | +0,060 | 0,424 |
| two-stage − llm-full | +0,034 [−0,03, 0,10] | 0,207 | +0,014 | 0,790 |
| per-res+dict − two-stage+dict | −0,117 [−0,21, −0,02] | 0,066 | −0,055 | 0,139 |
| oracle+dict − two-stage+dict | +0,148 [0,03, 0,28] | 0,029 | +0,147 | 0,013 |

### Tahap 1: pemilihan resource

| | Resource benar ada di pilihan | Benar di peringkat 1 |
| --- | --- | --- |
| tanpa kamus | 12/15 (80%) | 7/15 (47%) |
| dengan kamus | 13/15 (87%) | 10/15 (67%) |

Kegagalan tahap 1 yang konsisten:
- E12 `rujuk` → ServiceRequest (dipilih Encounter/Condition/Practitioner);
- E13 `periksa_lab` → DiagnosticReport (dipilih Encounter/Practitioner/Organization);
- E04 `poliklinik` → Location, hanya pada varian tanpa kamus.

Ada juga kasus tahap 1 benar tetapi tahap 2 gagal: E03 `pegawai` (Patient + Practitioner terpilih), di mana LLM memetakan seluruh kolom pegawai ke `Patient.*` sehingga R@|GT| = 0.

### Kesimpulan

1. **Two-stage (union) + kamus adalah konfigurasi terbaik non-oracle di target besar.** Akurasinya sedikit di atas llm-full+dict (+4,8 poin R@|GT|, +6,0 poin F1; belum signifikan dengan n=15), dengan **separuh token prompt (−50%) dan 22% lebih cepat**. Ini konfigurasi pertama yang memenuhi sisi biaya H2 tanpa kehilangan akurasi. Sisi akurasi H2 (≥ 5 poin lebih baik) belum terbukti.
2. **Matching per resource terpisah justru lebih buruk dan lebih mahal** (−11,7 poin vs union, 2,6× token output, 2,3× waktu). Bila tiap resource diproses sendiri, LLM "memaksakan" match ke setiap resource yang diberikan, tanpa persaingan antar-resource. Confidence dari panggilan terpisah juga tidak terkalibrasi untuk digabung. Jadi tahap 2 sebaiknya melihat semua resource terpilih sekaligus.
3. **Sisa gap ke oracle 15 poin (p=0,029)** berasal dari dua sumber: tahap 1 yang meleset (2–3 dari 15 pasangan) dan kebingungan antar-resource di tahap 2 saat lebih dari satu resource diberikan (mis. E03).
4. Kamus singkatan konsisten membantu di kedua tahap: hit@1 tahap 1 naik dari 47% ke 67%, dan R@|GT| naik +8 poin (belum signifikan).

### Catatan
- Satu run per konfigurasi (temp 0). Hasil union identik saat dijalankan ulang (dari cache).
- n = 15 pasangan; CI lebar. Butuh lebih banyak pasangan Khanza→FHIR sebelum klaim di paper.
- Nama tabel sumber sengaja tidak diberikan ke kedua tahap. Memberikannya (`reg_periksa`, `resep_obat`) kemungkinan besar menaikkan akurasi tahap 1, dan itu ablasi yang realistis.

## Ablasi nama tabel sumber (`ablation_table.py`, `analyze_ablation_table.py`)

Semua konfigurasi memakai kamus. Nama tabel ditampilkan seperti kolom, misalnya `SOURCE table: reg_periksa (registrasi periksa)`. Konfigurasi tanpa nama tabel memakai prompt yang identik byte-per-byte dengan run sebelumnya (diverifikasi: 0 panggilan baru, hasil sama). Total ada 47 panggilan LLM baru.

### Hasil (15 pasangan, target besar)

| Konfigurasi | R@|GT| | F1 | Tahap 1: resource benar terpilih | Tahap 1: benar di peringkat 1 | Token prompt |
| --- | --- | --- | --- | --- | --- |
| llm-full+dict | 0,353 | 0,270 | — | — | 1.964 |
| llm-full+dict + nama tabel | 0,327 | 0,280 | — | — | 1.973 |
| two-stage+dict | **0,400** | **0,330** | 13/15 | 10/15 | 985 |
| two-stage+dict + nama tabel di tahap 1 | 0,389 | 0,328 | **14/15** | 9/15 | 998 |
| two-stage+dict + nama tabel di tahap 1 & 2 | 0,373 | 0,290 | 14/15 | 9/15 | 1.007 |
| *oracle+dict* | *0,549* | *0,476* | — | — | *340* |

Uji berpasangan: semua efek nama tabel kecil dan tidak signifikan.

| Perbandingan | Δ R@|GT| | p | Δ F1 | p |
| --- | --- | --- | --- | --- | --- |
| llm-full+dict: +nama tabel | −0,026 | 0,600 | +0,011 | 0,779 |
| two-stage: +nama tabel di tahap 1 | −0,011 | 0,655 | −0,002 | 0,655 |
| two-stage: +nama tabel di tahap 2 juga | −0,016 | 0,866 | −0,038 | 0,214 |
| oracle − two-stage (nama tabel di kedua tahap) | +0,175 | 0,017 | +0,187 | 0,001 |

### Bacaan

1. **Nama tabel tidak menambah akurasi.** Nama kolom bersama kamus sudah memuat hampir semua informasi yang ada di nama tabel. Efek bersihnya sekitar nol, cenderung sedikit negatif.
2. **Nama tabel memperbaiki satu kegagalan tahap 1 dan merusak yang lain.**
   - `periksa_lab` kini memilih DiagnosticReport (E13: 0,00 → 0,33).
   - `resep_dokter` kini memilih Medication di samping MedicationRequest, dan R@|GT| justru turun (E08: 0,75 → 0,25), karena `kode_brng` tertarik ke `Medication.code`.
   - Peringkat 1 turun dari 10/15 ke 9/15 (E03 `pegawai` dan E04 `poliklinik` kini menaruh Organization di depan).
3. **`rujuk` → ServiceRequest tetap gagal di semua varian.** Qwen3-8B tidak mengaitkan *rujuk/rujukan* (referral) dengan ServiceRequest, dan kamus tidak membantu karena `rujuk` bukan singkatan. Ini contoh bagus untuk paper: **kegagalan karena istilah domain berbahasa Indonesia, bukan karena singkatan.** Kandidat perbaikannya kamus istilah domain ID→EN (rujuk→referral, ralan→outpatient, ranap→inpatient, penjab→payer), bukan kamus singkatan.
4. **Sisa gap ke oracle (±17–19 poin) adalah masalah tahap 2**: kebingungan antar-resource ketika 2–3 resource diberikan (E03 `pegawai` → Patient, E12, E14). Tahap 1 sendiri sudah mencapai 93% (dengan nama tabel).

Kesimpulan untuk desain: pertahankan **two-stage+dict tanpa nama tabel** sebagai konfigurasi utama. Nama tabel dilaporkan sebagai ablasi negatif.

## Kamus istilah domain ID→EN (`ablation_gloss.py`, `analyze_ablation_gloss.py`)

Dua glosarium kata-per-kata, tanpa konteks, untuk **seluruh** 200 token tabel sumber (setelah ekspansi singkatan). Ditambah entri contoh dari Anda (ranap, penjab, bangsal) meskipun token itu tidak muncul di kolom.

- **Manual** (`data/glossary_id_en_manual.json`): 182 entri, ditulis oleh saya. Arti kata umum/domain saja, tanpa nama elemen FHIR. Risiko bias: saya sudah melihat GT. Mitigasinya: semua token diterjemahkan, bukan hanya yang gagal.
- **Otomatis** (`data/glossary_id_en_qwen.json`, `auto_glossary.py`): 178 entri dari Qwen3-8B, batch 50 token, tanpa info FHIR atau pasangan. Istilah inti benar (`rujuk`→refer, `ralan`→outpatient, `poli`→clinic). Istilah RS lebih lemah (`rawat`→inpatient, `keluar`→exit, `masuk`→enter, `bhp`→health insurance, `wp`→workplace).

Kolom ditampilkan sebagai `tgl_rujuk (tanggal rujuk = EN: date refer)` atau `rujuk_ke (EN: refer to)`. Nama FHIR tidak berubah. Total 107 panggilan LLM baru.

### Hasil (15 pasangan, R@|GT|)

| Konfigurasi | Target besar | Tahap 1: resource benar terpilih / di peringkat 1 | Token prompt |
| --- | --- | --- | --- |
| llm-full+dict | 0,353 | — | 1.964 |
| llm-full + glosarium manual | 0,255 | — | 2.049 |
| llm-full + glosarium Qwen | 0,240 | — | 2.049 |
| two-stage+dict | 0,400 | 13/15 / 10/15 | 985 |
| two-stage + glosarium manual di tahap 1 | 0,356 | 13/15 / 10/15 | 1.113 |
| two-stage + glosarium manual di tahap 1 & 2 | 0,387 | 13/15 / 10/15 | 1.198 |
| **two-stage + glosarium Qwen di tahap 1 & 2** | **0,433** | 13/15 / 10/15 | 1.189 |
| *oracle+dict (resource benar diberikan)* | *0,549* | — | *340* |
| *oracle + glosarium manual* | *0,605* | — | *425* |

Uji berpasangan (R@|GT|):

| Perbandingan | Δ | p |
| --- | --- | --- |
| two-stage: glosarium Qwen vs kamus saja | +0,033 | 0,401 |
| two-stage: glosarium manual vs kamus saja | −0,013 | 0,917 |
| llm-full: glosarium Qwen vs kamus saja | **−0,113** | **0,028** |
| llm-full: glosarium manual vs kamus saja | −0,098 | 0,116 |
| oracle: glosarium manual vs kamus saja | +0,057 | 0,225 |
| two-stage vs llm-full (keduanya glosarium manual) | +0,132 | 0,021 |

F1 menunjukkan arah yang sama.

### Bacaan

1. **Glosarium tidak memperbaiki tahap 1 sama sekali.** Hit rate identik (13/15, 10/15). E12 `rujuk` tetap tidak pernah memilih ServiceRequest, padahal kolomnya sudah berlabel `rujuk_ke (EN: refer to)`. Jadi hipotesis saya sebelumnya ("Qwen tidak paham *rujuk*") **salah**. Qwen paham artinya. Yang tidak ia tahu adalah bahwa *referral* dimodelkan sebagai **ServiceRequest** di FHIR, dan deskripsi satu baris ServiceRequest ("A request for a service to be performed") tidak menyebut rujukan. Masalahnya ada di **pengetahuan pemodelan FHIR**, bukan bahasa.
2. **Di prompt penuh 289 elemen, glosarium merugikan** (−10 sampai −11 poin; versi Qwen signifikan, p=0,028). Glosa kata-per-kata ("code clinic", "number care") menambah teks tanpa menambah petunjuk resource, dan di target besar itu menjadi noise.
3. **Di tahap 2 dengan resource yang sudah benar (oracle), glosarium cenderung membantu**: +5,7 poin, belum signifikan. Contohnya E06 0,50→1,00 dan E13 0,17→0,50, meskipun E12 turun 0,62→0,38. Jadi glosarium berguna untuk memilih **elemen**, bukan **resource**.
4. **Glosarium otomatis (Qwen) tidak kalah dari yang manual** (0,433 vs 0,387 untuk two-stage, selisih tidak signifikan). Untuk paper, ini argumen bahwa glosarium bisa dibangkitkan otomatis tanpa kurasi manusia, dengan catatan bahwa ia masih salah pada istilah RS.
5. **Semua selisih ±3–5 poin di antara konfigurasi two-stage berada di dalam noise** (n=15). Konfigurasi terbaik secara angka adalah two-stage + glosarium Qwen (0,433), tetapi belum ada yang terbukti lebih baik dari two-stage+dict.

### Implikasi
- Gap ke oracle sekarang **±17–22 poin** dan terdiri dari: (a) tahap 1 tidak tahu konvensi pemodelan FHIR (rujukan → ServiceRequest, pemeriksaan lab → DiagnosticReport); (b) kebingungan antar-resource di tahap 2.
- Perbaikan yang lebih tepat sasaran untuk (a): beri tahap 1 **definisi resource yang lebih kaya** (field `definition`/`purpose` FHIR, yang menyebut referral, lab report, dsb.) alih-alih satu baris `short`. Glosarium kolom tidak menyentuh masalah ini.

## Set diperbesar: 40 pasangan Khanza→FHIR (n = 41 dengan E20) (`draft_pairs_e_more.py`, `run_n40.py`, `rescore_n40.py`, `analyze_n40.py`)

**Pasangan baru E29–E54 (26):** 111 korespondensi, 63 n:1, 17 ambigu. Konvensinya sama dengan E01–E14, ditambah satu aturan untuk tabel tanda vital: satu baris berisi beberapa vital, dan karena FHIR memodelkan tekanan darah dengan *component*, kolom tekanan darah → `component.value[x]` dinilai, sedangkan vital lain → `component.value[x]` masuk n:1. Sebaran resource utama untuk 40 tabel Khanza:

| Resource | Jumlah tabel |
| --- | --- |
| Observation | 8 |
| ServiceRequest | 5 |
| Organization, Location, MedicationRequest, Patient | masing-masing 4 |
| Practitioner, Encounter, DiagnosticReport | masing-masing 3 |
| Condition | 2 |
| Medication | 1 |

Target tetap gabungan 11 resource (289 elemen), jadi angka E01–E14 identik dengan run sebelumnya (diverifikasi dari cache). Glosarium Qwen diperluas hanya untuk 111 token baru, sehingga glosa lama tidak berubah. Run ini memerlukan 144 panggilan LLM baru.

### Hasil (41 pasangan, 205 korespondensi)

| Konfigurasi | R@|GT| | F1 | Token prompt | Token output | Detik |
| --- | --- | --- | --- | --- | --- |
| llm-full+dict | 0,270 | 0,250 | 1.936 | 408 | 26 |
| two-stage+dict | 0,323 | 0,292 | 958 | 403 | 21 |
| **two-stage+qgloss** | **0,340** | **0,301** | 1.110 | 401 | 22 |
| *oracle+dict* | *0,524* | *0,488* | *312* | *338* | *16* |

Pasangan baru lebih sulit daripada yang lama: llm-full+dict 0,222 (26 baru) vs 0,353 (15 lama); two-stage+dict 0,279 vs 0,400.

### Uji berpasangan (Wilcoxon + bootstrap 95% CI, n = 41)

| Perbandingan | Δ R@|GT| [95% CI] | p | Δ F1 | p |
| --- | --- | --- | --- | --- | --- |
| two-stage+dict − llm-full+dict | +0,053 [−0,03, 0,14] | 0,19 | +0,041 | 0,40 |
| two-stage+qgloss − llm-full+dict | +0,070 [−0,02, 0,16] | **0,037** | +0,051 | 0,16 |
| two-stage+qgloss − two-stage+dict | +0,016 [−0,03, 0,07] | 0,43 | +0,010 | 0,28 |
| oracle+dict − two-stage+dict | **+0,201** [0,13, 0,28] | **< 0,001** | +0,197 | < 0,001 |

Hasil Khanza saja (n = 40) praktis sama.

**Catatan jujur soal signifikansi:** p=0,037 untuk two-stage+qgloss hanya pada R@|GT|, tidak pada F1. Bootstrap CI-nya masih memuat 0, dan dengan 4 perbandingan (koreksi Bonferroni, α=0,0125) hasil ini **tidak signifikan**. Yang kokoh hanyalah: (a) arahnya konsisten, two-stage ≥ llm-full pada kedua metrik; (b) biaya two-stage turun **−50% token prompt dan −17% waktu**; (c) gap ke oracle besar (±20 poin, p < 0,001).

### Metrik n:1-netral

Konvensi menyebut prediksi `gt_n1`/`ambiguous` "tidak dinilai", tetapi metrik ketat tetap menghitungnya sebagai salah bila masuk top-|GT| atau mengambil slot 1:1. Contohnya, model memetakan semua vital ke `component.value[x]` (benar menurut konvensi) dan tetap dihukum. `rescore_n40.py` menghapus prediksi seperti itu sebelum menilai (dari cache, 0 panggilan baru).

| | Ketat | n:1-netral |
| --- | --- | --- |
| llm-full+dict | 0,270 | 0,270 |
| two-stage+dict | 0,323 | 0,323 |
| two-stage+qgloss | 0,340 | 0,346 (p=0,024 vs llm-full) |
| oracle+dict | 0,524 | 0,552 (Observation 0,24 → 0,32) |

Kesimpulan tidak berubah. Ke depan, **metrik n:1-netral sebaiknya menjadi metrik utama**, karena itulah yang sesuai konvensi. Angka di bagian-bagian sebelumnya dokumen ini memakai metrik ketat.

### Tahap 1 dan per resource

- Resource benar terpilih **34/41** (83%), di peringkat 1 26/41 (two-stage+dict). Dengan glosarium Qwen, peringkat 1 turun ke 22/41.
- **ServiceRequest tidak pernah terpilih: 0/5 pasangan** (`rujuk`, `rujuk_masuk`, `rujukan_internal_poli`, `permintaan_lab`, `permintaan_radiologi`). Ini kegagalan sistematis tahap 1, konsisten dengan temuan sebelumnya bahwa deskripsi satu baris "A request for a service to be performed" tidak menyebut order lab/radiologi maupun rujukan. Miss lainnya: E13 `periksa_lab` (DiagnosticReport) dan E29 `pasien_mati` (Patient; terpilih Encounter/Condition/Practitioner).

R@|GT| per resource utama:

| Resource (n) | llm-full+dict | two-stage+dict | two-stage+qgloss | oracle |
| --- | --- | --- | --- | --- |
| Organization (4) | 0,25 | **0,88** | 0,81 | 0,92 |
| Location (4) | 0,73 | 0,81 | 0,81 | 0,81 |
| MedicationRequest (4) | 0,18 | **0,49** | 0,44 | 0,64 |
| Patient (4) | **0,61** | 0,46 | 0,45 | 0,54 |
| Encounter (3) | **0,59** | 0,42 | 0,15 | 0,37 |
| Practitioner (3) | 0,22 | 0,19 | 0,41 | 0,70 |
| DiagnosticReport (3) | 0,06 | 0,00 | 0,24 | 0,30 |
| ServiceRequest (5) | 0,07 | 0,00 | 0,00 | 0,52 |
| Observation (8) | 0,00 | 0,02 | 0,04 | 0,24 |

- Two-stage paling membantu di resource yang namanya jelas (Organization, MedicationRequest), dan merugikan di Patient/Encounter, di mana tahap 1 menambah resource pesaing.
- **Observation hampir 0 di semua konfigurasi target besar**, dan hanya 0,24–0,32 di oracle. Kesalahan dominan di oracle: `no_rawat` (nomor kunjungan, FK) → `Observation.identifier` alih-alih `encounter`, tanggal → `encounter`, dan vital → `referenceRange`.

### Power

Simpangan baku selisih per pasangan besar (±0,27–0,30). Untuk mendeteksi efek sebesar yang teramati (+5 sampai +8 poin) dengan power 80%, dibutuhkan **±120–200 pasangan**, bukan 40. Implikasinya untuk paper:
1. laporkan efek dengan CI, bukan hanya p;
2. pertimbangkan unit analisis **korespondensi** (205 GT) dengan model campuran atau cluster bootstrap per tabel;
3. atau tambah pasangan dari sistem lain (SIMRS lain, OpenSID→FHIR) daripada terus menambah tabel Khanza.

## Ablasi katalog tahap 1: definisi resource FHIR yang lebih kaya (`fhir_catalog.py`, `stage1_rich.py`, `analyze_stage1_rich.py`)

27 Okt 2026 · 41 pasangan, target besar 289 elemen, two-stage+dict, metrik n:1-netral · 211 panggilan LLM baru

Pertanyaannya: apakah kegagalan tahap 1 (ServiceRequest 0/5, E13, E29) hilang bila deskripsi satu baris (`short`) diganti dengan teks spesifikasi yang lebih lengkap? Sumbernya FHIR R4 (CC0): root `definition` (+ `comment`) dari StructureDefinition, bagian "Scope and Usage" dan "Boundaries and Relationships" dari halaman resource (`data/subset_e/raw/fhir_pages/`), serta daftar elemen tingkat atas. Patient dan Medication tidak punya bagian Boundaries. Tahap 2 tidak diubah (gabungan resource terpilih) dan hanya memanggil LLM baru bila himpunan resource terpilih berubah. Varian `short` 100% dari cache, sehingga identik dengan run n=41.

### Hasil

| Katalog tahap 1 | Token tahap 1 | Hit (41) | Hit@1 | Hit di 7 yang meleset | R@\|GT\| | F1 | Token prompt total | Detik |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `short` (baseline) | 349 | 34 | 26 | 0/7 | 0,323 | 0,296 | 958 | 21 |
| `def` (definition + comment) | 685 | **36** | 26 | **3/7** | **0,338** | **0,299** | 1.342 | 24 |
| `elements` (short + nama elemen) | 890 | 35 | **29** | 2/7 | 0,335 | 0,288 | 1.545 | 26 |
| `scope` (def + Scope and Usage) | 4.638 | 33 | 26 | 0/7 | 0,322 | 0,297 | 5.295 | 42 |
| `scope+bnr` (+ Boundaries) | 8.014 | 34 | 27 | 2/7 | 0,302 | 0,278 | 8.665 | 61 |

Uji berpasangan R@|GT| terhadap `short` (n = 41): `def` +1,5 poin (CI −2,4..+5,6; p=0,48), `elements` +1,2 (CI −3,7..+5,8; p=0,53), `scope` −0,1 (p=0,68), `scope+bnr` −2,1 (CI −6,1..+0,7; p=0,28). Tidak ada yang signifikan. Semua varian kehilangan E31 (Practitioner), dan `scope+bnr` juga kehilangan E07.

Pilihan tahap 1 untuk 7 pasangan yang meleset:

| Pasangan | Resource benar | `short` | `def` | `elements` | `scope+bnr` | Oracle R@\|GT\| |
| --- | --- | --- | --- | --- | --- | --- |
| E12 `rujuk` | ServiceRequest | – | ✓ | – | ✓ | 0,62 |
| E13 `periksa_lab` | DiagnosticReport | – | ✓ | – | – | 0,17 |
| E29 `pasien_mati` | Patient | – | – | ✓ | – | 0,50 |
| E51 `permintaan_lab` | ServiceRequest | – | – | – | – | 0,67 |
| E52 `permintaan_radiologi` | ServiceRequest | – | – | – | – | 0,67 |
| E53 `rujukan_internal_poli` | ServiceRequest | – | – | – | – | 0,33 |
| E54 `rujuk_masuk` | ServiceRequest | – | ✓ | ✓ | ✓ | 0,33 |

### Bacaan

1. **Definisi yang lebih kaya hanya memperbaiki sebagian tahap 1, dan teks panjang tidak membantu.** `def` (+336 token) menaikkan hit dari 0/7 ke 3/7 di pasangan yang meleset. `scope` (13× lebih panjang) kembali ke 0/7, dan `scope+bnr` kembali ke 2/7 dengan biaya 2,8× waktu. Dugaan: teks Scope/Boundaries menyebut banyak resource lain (ServiceRequest "akan menghasilkan DiagnosticReport/Observation"), dan model 8B mengambil nama-nama itu. `permintaan_lab`/`permintaan_radiologi` tetap ke DiagnosticReport di semua varian. Model memetakan "permintaan pemeriksaan lab" ke laporannya, bukan ke order-nya.
2. **Hit tahap 1 tidak berubah menjadi skor.** Di 7 pasangan itu R@|GT| tetap ≈0 di semua varian (maks. 0,07, yaitu E29 di `elements`), padahal oracle-nya rata-rata 0,47. Ketika ServiceRequest sudah terpilih (E12/E54 di `def`), tahap 2 tetap memetakan hampir semua kolom ke **Encounter**: `no_rujuk`→`Encounter.identifier`, `kd_dokter`→`Encounter.participant.individual`, `tgl_rujuk`→`Encounter.hospitalization.origin`.
3. **Hambatan sebenarnya ada di tahap 2: Encounter "menyerap" prediksi.** Encounter terpilih di 24/41 pasangan, karena hampir setiap tabel klinis Khanza punya `no_rawat`. Di 31 pasangan non-Encounter yang resource benarnya sudah terpilih (varian `short`):

   | Encounter ikut terpilih? | n | Porsi top-\|GT\| ke Encounter.* | Porsi ke resource benar | R@\|GT\| | Oracle | Gap |
   | --- | --- | --- | --- | --- | --- | --- |
   | Tidak | 17 | 0% | 76% | 0,60 | 0,73 | 0,13 |
   | Ya | 14 | 63% | 30% | 0,13 | 0,41 | **0,28** |

   Ada konfon: tabel yang memicu Encounter adalah tabel kejadian klinis (8 di antaranya Observation), yang memang lebih sulit (oracle 0,41 vs 0,73). Meski begitu, gap ke oracle dua kali lipat. Ini juga menjelaskan Observation ≈0 di target besar.

**Kesimpulan:** untuk two-stage, pakai `def` sebagai katalog default (biayanya kecil, arahnya positif). Perbaikan berikutnya tidak lagi di tahap 1, tetapi di tahap 2. Konvensi GT menempatkan semua korespondensi satu tabel di **satu resource utama** (FK seperti `no_rawat` → `X.encounter`, bukan ke elemen Encounter), sehingga pipeline perlu memilih satu resource utama, bukan menggabungkan.

## Tahap 2 dengan satu resource utama (`stage2_primary.py`, `analyze_stage2_primary.py`)

27 Okt 2026 · 41 pasangan, target besar, katalog tahap 1 `def`, kamus di kedua tahap, metrik n:1-netral · 67 panggilan LLM baru

Setiap resource hasil tahap 1 dicocokkan **terpisah**. Hasil yang dipakai hanya milik **satu** resource, bukan gabungan semuanya. Aturan pemilihan (tanpa panggilan LLM tambahan):
- `rank1`: urutan tahap 1, pilihan pertama.
- `sum_conf`: total confidence terbesar.
- `coverage`: kolom sumber terbanyak yang ter-match.
- `best`: R@|GT| tertinggi. Ini **plafon pemilihan** dengan GT, bukan metode.

Aturan memakai skor mentah, karena filter n:1-netral memakai informasi GT.

### Hasil

| Konfigurasi | Resource yang dipilih benar | R@\|GT\| | F1 | Token prompt | Median detik |
| --- | --- | --- | --- | --- | --- |
| llm-full+dict (289 elemen) | – | 0,270 | 0,258 | 1.936 | 22 |
| two-stage union [`def`] | – | 0,338 | 0,299 | 1.342 | 21 |
| **primary [`rank1`]** | 26/41 | **0,407** | **0,389** | **1.062**¹ | **19**¹ |
| primary [`sum_conf`] | 21/41 | 0,305 | 0,307 | 1.688 | 43 |
| primary [`coverage`] | 19/41 | 0,278 | 0,286 | 1.688 | 43 |
| *primary [`best`] (plafon pemilihan)* | *34/41* | *0,508* | *0,476* | – | – |
| *oracle+dict* | *41/41* | *0,552* | *0,514* | *312* | *12* |

¹ `rank1` cukup memanggil tahap 2 sekali (resource pertama). Biaya di tabel ini adalah biaya varian satu panggilan tersebut. Varian lain menjalankan semua resource terpilih. Satu panggilan tercatat 16.127 detik dengan output normal (<1.000 token), kemungkinan mesin tidur/swap, jadi waktu dilaporkan sebagai median.

Uji berpasangan (n = 41, Wilcoxon + bootstrap 95% CI):

| Perbandingan | Δ R@\|GT\| (CI) | p | Δ F1 (CI) | p |
| --- | --- | --- | --- | --- | --- |
| rank1 − union[`def`] | +6,9 (−0,6..+14,2) | 0,096 | **+9,0 (+1,7..+16,3)** | 0,024 |
| rank1 − llm-full+dict | **+13,7 (+3,8..+23,7)** | 0,011 | **+13,1 (+3,5..+22,5)** | 0,011 |
| oracle − rank1 | +14,6 (+5,1..+24,1) | 0,013 | +12,5 (+3,3..+22,4) | 0,035 |
| best − rank1 | +10,1 (+4,1..+17,0) | 0,012 | +8,7 (+3,4..+14,9) | 0,012 |
| oracle − best | +4,4 (−3,3..+12,6) | 0,44 | +3,8 (−4,1..+12,6) | 0,78 |

### Bacaan

1. **Satu resource utama mengalahkan gabungan resource, dan untuk pertama kalinya mengalahkan llm-full dengan CI yang tidak memuat 0.** `rank1` unggul +13,7 poin R@|GT| atas llm-full+dict dengan 55% token prompt dan waktu sedikit lebih cepat. Atas union, F1 naik +9 poin. Hipotesis "Encounter menyerap prediksi" terkonfirmasi: begitu matching dibatasi ke satu resource, prediksi tidak lagi bocor ke Encounter.
2. **Confidence LLM tidak bisa dipakai memilih resource.** `sum_conf`/`coverage` memilih resource yang benar hanya di 19–21/41 pasangan, lebih buruk daripada urutan tahap 1 (26/41). Model memberi confidence tinggi untuk resource apa pun. Location/Organization "menang" karena kolom alamat, dan Observation menang di tabel apa pun yang punya kolom nilai.
3. **Sisa gap ke oracle (14,6 poin) hampir seluruhnya soal pemilihan.** Plafon pemilihan (`best`) hanya 4,4 poin di bawah oracle (ns). Jadi bila resource utama dipilih dengan benar di antara pilihan tahap 1, pipeline hampir setara oracle. Kesalahan `rank1`: Encounter di peringkat 1 (6 pasangan), Patient di peringkat 1 untuk tabel dokter/petugas (3), DiagnosticReport (1).
4. Per resource (`rank1`): Organization 0,92, Location 0,88, Condition 0,67, Patient 0,58, MedicationRequest 0,54. Tetap lemah: **ServiceRequest 0,00** (tidak pernah di peringkat 1), Practitioner 0,00 (kalah oleh Patient), Observation 0,11.

### Catatan validitas

- Tiga aturan pemilihan dicoba dan yang terbaik dilaporkan, jadi ada bias pemilihan *post hoc*. Dengan Bonferroni untuk 3 aturan × 2 pembanding, ambang p ≈ 0,008. Di sini `rank1` vs llm-full (p = 0,011) belum lolos, meskipun bootstrap CI-nya tidak memuat 0. Untungnya `rank1` adalah aturan paling sederhana dan tanpa parameter, sehingga konfirmasi pada data baru seharusnya mudah.
- Satu run per konfigurasi, GT satu anotator.

## Memperbaiki peringkat 1 tahap 1 untuk primary[rank1] (`stage1_primary_hint.py`, `analyze_stage1_primary_hint.py`)

27 Okt 2026 · 41 pasangan, desain 2×2: katalog {`def`, `elements`} × instruksi {tanpa, `described`} · primary[rank1], metrik n:1-netral · 80 panggilan LLM baru

Instruksi `described` ditambahkan setelah kalimat tugas tahap 1, dalam istilah FHIR umum (tanpa nama kolom Khanza). Isinya: "taruh di depan resource yang *dideskripsikan* tabel (satu baris = satu instance). Jangan taruh di depan resource yang hanya dirujuk lewat FK: kolom ID/kode kunjungan, pasien, atau praktisi adalah referensi ke Encounter, Patient, atau Practitioner, bukan bukti bahwa tabelnya resource itu." Sel `def`/tanpa identik dengan primary[rank1] sebelumnya (0 panggilan baru).

### Hasil

| Katalog | Instruksi | Hit@1 | Salah: Encounter di peringkat 1 | R@\|GT\| | F1 | Token prompt |
| --- | --- | --- | --- | --- | --- | --- |
| `def` | tanpa (baseline) | 26/41 | 7 | **0,407** | 0,389 | 1.062 |
| `def` | `described` | 23/41 | **14** | 0,403 | 0,375 | 1.162 |
| `elements` | tanpa | **29/41** | 6 | 0,405 | **0,414** | 1.270 |
| `elements` | `described` | 23/41 | **14** | 0,367 | 0,359 | 1.369 |

Uji berpasangan terhadap baseline (n = 41): semua |Δ R@\|GT\|| ≤ 4 poin, ns (p ≥ 0,46). `elements`/tanpa: F1 +2,5 (CI −2,3..+7,5; p = 0,35).

### Bacaan

1. **Instruksi `described` justru memperburuk keadaan, dengan efek "jangan pikirkan gajah".** Encounter sebagai peringkat 1 yang salah naik dua kali lipat (7 → 14), terutama di tabel Observation: E40–E44 yang sebelumnya benar sekarang dimulai dengan Encounter. Menyebut nama "Encounter" di instruksi negatif tampaknya malah mem-*priming* model 8B. Hit@1 turun ke 23/41 di kedua katalog. Kalau mau dicoba lagi, instruksinya jangan menyebut nama resource. Tetapi menyetel prompt berulang kali di 41 pasangan yang sama berisiko *overfitting*.
2. **Katalog `elements` memperbaiki urutan (hit@1 26 → 29), tetapi recall tidak naik.** Pasangan yang membaik adalah E05 (Encounter), E29 (Patient), E41, dan E44 (Observation); E06 (Condition) memburuk. Pasangan Observation yang sekarang benar tetap ber-recall rendah, karena matching Observation sulit bahkan di oracle (0,24–0,32). Jadi keuntungan hit@1 belum berubah menjadi skor.
3. **ServiceRequest tetap 0/5 di peringkat 1** di keempat sel, dan Practitioner 0–1/3 (kalah oleh Patient).

**Kesimpulan:** tidak ada varian yang lebih baik secara bermakna dari baseline. Konfigurasi rekomendasi tetap **primary[rank1] dengan katalog `def` tanpa instruksi**. `elements` boleh dipakai bila F1 yang diutamakan, karena F1 +2,5 (ns) dan atas llm-full +15,6 F1 (CI +6,4..+24,9). Tetapi ini pilihan *post hoc* lagi. Memperbaiki peringkat 1 lewat teks prompt tampaknya sudah mentok untuk Qwen3-8B. Sisa gap ke plafon pemilihan (0,407 → 0,508) perlu sinyal lain, bukan deskripsi tambahan.

## Konfirmasi pra-registrasi pada pasangan non-Khanza (`PREREG_CONFIRM.md`, `draft_confirm.py`, `run_confirm.py`, `analyze_confirm.py`)

27 Okt 2026 · set *held-out*: 18 pasangan → FHIR dari 6 sistem Indonesia non-Khanza, 69 gt, target besar 289 elemen, metrik n:1-netral · konfigurasi dibekukan dan GT di-hash sebelum run · 90 panggilan LLM baru

Sumber: `mfarim/laravel-rekam-medis-puskesmas` (MIT, singkatan ad hoc `pmrk_fisik`, `rcn_tndk_lnjt`), `elingp/sistem-informasi-puskesmas` (MIT), `arfandotid/ci_rekammedis` (camelCase, lisensi tidak jelas), `Kriss245/Sipograf` (posyandu, MIT), `Slyzyy/e-Puskesmas` (lisensi tidak jelas), dan modul kesehatan OpenSID (GPL-3.0). Kamus singkatan tetap kamus Khanza, jadi ini juga uji transfer. Detail sumber ada di SUBSET_E.md.

### Hasil konfirmatori

| Konfigurasi | R@\|GT\| | F1 | Token prompt | Median detik |
| --- | --- | --- | --- | --- |
| llm-full+dict | 0,488 | 0,435 | 1.876 | 16 |
| union[`def`] | 0,545 | 0,453 | 1.161 | 14 |
| **primary[rank1]** | **0,611** | **0,520** | **907** | **12** |
| *oracle+dict* | *0,791* | *0,732* | *253* | *8* |

| Hipotesis (satu sisi, Holm) | Δ R@\|GT\| (95% CI) | w/t/l | p Holm | n=41 (pengembangan) |
| --- | --- | --- | --- | --- |
| H1 rank1 > llm-full+dict | +12,2 (−0,2..+27,2) | 4/13/1 | 0,138 | +13,7 (+3,8..+23,7) |
| H2 rank1 > union[`def`] | +6,5 (−6,7..+20,2) | 4/12/2 | 0,173 | +6,9 (−0,6..+14,2) |

**Status menurut kriteria pra-registrasi: H1 tidak terkonfirmasi secara statistik, tetapi arahnya konsisten.** Besar efeknya hampir sama dengan set pengembangan (+12,2 vs +13,7). Urutan keempat konfigurasi identik, dan primary[rank1] tetap yang termurah. Gagalnya uji terutama soal power: n = 18, dan 13/18 pasangan seri, karena banyak skema baru mudah sehingga semua metode mencapai skor sama.

### Eksploratif (tidak dikoreksi, tidak dipra-registrasi)

- **Set gabungan pengembangan + konfirmasi (n = 59):** rank1 − llm-full +13,2 (CI +5,3..+21,5; p = 0,002); rank1 − union +6,8 (CI +0,4..+13,3; p = 0,053). Set ini memuat data pengembangan, jadi bukan konfirmasi.
- **Skema baru lebih mudah daripada Khanza** (llm-full 0,49 vs 0,27; oracle 0,79 vs 0,55): nama lebih deskriptif dan kolom lebih sedikit. Kamus Khanza tetap dipakai dan tidak tampak merugikan.
- **Tahap 1:** hit 17/18, hit@1 12/18. Pola "penyerapan" Khanza muncul lagi dalam bentuk lain:
  - C03 `tb_rujuk` → Encounter di peringkat 1. ServiceRequest kini terpilih, tetapi hanya di peringkat 2.
  - C14 `rm_obat` → Medication di peringkat 1, bukan MedicationRequest.
  - C02 → Condition di peringkat 1.
- **Sistem `sipuskesmas` = 0 di semua konfigurasi non-oracle** (oracle 0,89). Tabel `polis` (`id, nama, nomor_sekarang`), `tenaga_kesehatans` (`id, poli_id, nama, jadwal, no_telepon`), dan `antrians` tanpa nama tabel memang tidak bisa dibedakan: kolom generik `id`/`nama` membuat tahap 1 memilih Patient. Di sini **nama tabel kemungkinan besar menentukan**. Ini berbeda dari ablasi nama tabel di Khanza (no gain), karena kolom Khanza sudah bermuatan domain (`kd_poli`, `nm_dokter`). Ini hipotesis untuk diuji, bukan temuan.

### Kesimpulan

primary[rank1] (two-stage, katalog `def`, satu resource peringkat 1) dapat dilaporkan sebagai konfigurasi terbaik dengan efek yang **direplikasi arahnya dan besarnya** pada data baru (+12 sampai +14 poin atas llm-full, ±50% token). Signifikansi konfirmatorinya belum tercapai (p_Holm = 0,14, n = 18). Untuk paper, laporkan kedua set terpisah ditambah status pra-registrasi apa adanya. Menambah set konfirmasi (sistem lain, atau EN→FHIR seperti `eclinic_api` sebagai kondisi terpisah) adalah cara langsung menaikkan power.

## Analisis tingkat korespondensi (`analyze_correspondence.py`, eksploratif)

28 Okt 2026 · dari cache (0 panggilan baru) · unit = satu korespondensi gt, *hit* = masuk top-|GT| (n:1-netral) · recall mikro · CI = bootstrap klaster per pasangan, p = uji permutasi *sign-flip* per pasangan (dua sisi), agar korespondensi dalam satu tabel tidak dianggap independen

| Set (pasangan / korespondensi) | llm-full+dict | union[`def`] | primary[rank1] | oracle | rank1 − llm-full (CI; p) | rank1 − union (CI; p) |
| --- | --- | --- | --- | --- | --- | --- |
| dev41 (41 / 205) | 0,263 | 0,327 | 0,356 | 0,561 | +9,3 (−1,4..+20,8; 0,12) | +2,9 (−5,2..+10,9; 0,57) |
| confirm18 (18 / 69) | 0,536 | 0,609 | 0,667 | 0,812 | +13,0 (0,0..+28,0; 0,19) | +5,8 (−9,6..+20,6; 0,60) |
| gabungan (59 / 274) | 0,332 | 0,398 | 0,434 | 0,624 | **+10,2 (+1,4..+19,3; 0,029)** | +3,6 (−3,4..+10,7; 0,37) |

Bacaan:
- Analisis korespondensi **tidak menambah power**. Begitu korelasi dalam tabel dikoreksi, unit efektifnya tetap pasangan.
- Efek mikro sedikit lebih kecil daripada makro (+9,3 vs +13,7 di dev41), karena tabel besar (mis. `pasien`, 11 gt) mendapat bobot lebih, dan di tabel besar semua metode relatif sama.
- Urutan konfigurasi konsisten di ketiga set.
- Klaim yang kokoh untuk paper: **primary[rank1] tidak lebih buruk dan cenderung lebih baik (+9 sampai +14 poin) daripada llm-full dengan ±50% token prompt.** Efisiensi biaya bersifat deterministik; keunggulan akurasi tereplikasi arahnya tetapi signifikansinya bergantung pada set gabungan.

## Model kedua: GLM-5.3 Flash via API Neuralwatt (`run_model2.py`, `analyze_model2.py`)

28 Okt 2026 · `glm-5.3-flash` (zai-org/GLM-5.3-Flash; GLM 5.2 Flash tidak tersedia di endpoint) · temperature 0, seed 0, `json_object`, `reasoning_effort=low` (reasoning tidak bisa dimatikan) · 4 konfigurasi utama × 59 pasangan, prompt dan konfigurasi **identik** dengan Qwen (dibekukan pada Qwen, tidak disetel untuk GLM) · 258 panggilan, semua `finish=stop`, 0 JSON rusak · 203k token input + 60k output (±US$0,06)

| Model / set | llm-full+dict | union[`def`] | primary[rank1] | oracle | hit@1 tahap 1 |
| --- | --- | --- | --- | --- | --- |
| Qwen3-8B / dev41 | 0,270 | 0,338 | **0,407** | 0,552 | 26/41 |
| Qwen3-8B / confirm18 | 0,488 | 0,545 | **0,611** | 0,791 | 12/18 |
| GLM-5.3 Flash / dev41 | 0,556 | 0,581 | **0,682** | 0,764 | 34/41 |
| GLM-5.3 Flash / confirm18 | 0,635 | 0,619 | **0,714** | 0,824 | 15/18 |

(R@|GT| n:1-netral; F1 menunjukkan pola yang sama.)

primary[rank1] − llm-full+dict (Wilcoxon dua sisi, bootstrap 95% CI):

| Model | dev41 | confirm18 | gabungan 59 |
| --- | --- | --- | --- |
| Qwen3-8B | +13,7 (+3,8..+23,7; p=0,011) | +12,2 (−0,2..+27,2; p=0,14) | +13,2 (+5,3..+21,5; p=0,002) |
| GLM-5.3 Flash | **+12,7 (+3,7..+21,7; p=0,016)** | +7,9 (−5,6..+22,2; p=0,36) | **+11,2 (+3,8..+18,7; p=0,010)** |

primary[rank1] − union[`def`] untuk GLM: +9,9 gabungan (CI +3,3..+17,2; p = 0,009). Untuk Qwen: +6,8 (p = 0,053).

### Bacaan

1. **Keunggulan satu resource utama tereplikasi lintas keluarga model.** Untuk GLM, dev41 adalah replikasi yang jujur: semua pilihan desain dibuat di Qwen, dan GLM tidak pernah dipakai untuk menyetel apa pun. Efeknya hampir sama besar (+12,7 vs +13,7) dan signifikan. Di confirm18 arahnya sama tetapi ns. Banyak pasangan seri (14/18), karena GLM sudah tinggi di semua konfigurasi.
2. **Pada model yang lebih kuat, union tidak lagi membantu, tetapi rank1 tetap membantu.** GLM union ≈ llm-full (+2,5 dev, −1,6 confirm), sedangkan rank1 tetap +8 sampai +13. Penyerapan oleh resource yang dirujuk lewat FK (Encounter) tetap terjadi pada model yang lebih besar, dan pembatasan ke satu resource adalah perbaikannya.
3. **GLM jauh lebih akurat** (+16 sampai +24 poin per konfigurasi, semua p < 0,001) dan **sangat cepat** (median 2–3 detik/panggilan vs 16–19 detik Qwen lokal). Tahap 1-nya juga jauh lebih baik (hit@1 83% vs 64%). Gap ke oracle menyusut dari 14,6 ke 8,2 poin (dev41).
4. Struktur biaya sama untuk kedua model: rank1 memakai ±53–55% token prompt llm-full.

### Catatan validitas

- API temperature 0 / seed 0 belum tentu deterministik. Hasil tersimpan di `data/hybrid_cache__glm-5.3-flash.json`, sehingga analisis dapat diulang tanpa memanggil API lagi.
- Skema publik GitHub kemungkinan ada di data latih kedua model; yang tidak mungkin ada adalah GT kami.
- Kunci API hanya dibaca dari variabel lingkungan `NEURALWATT_API_KEY` (`hybrid.py`); kunci tidak disimpan di repo.

## Langkah berikutnya

1. ~~Uji target besar.~~ ~~Pipeline dua tahap.~~ ~~Ablasi nama tabel.~~ ~~Kamus istilah domain.~~ ~~Tambah pasangan ke ≥ 40.~~ ~~Katalog tahap 1 yang lebih kaya.~~ ~~Satu resource utama di tahap 2.~~ ~~Peringkat 1 tahap 1 lewat prompt.~~ ~~Konfirmasi pada pasangan non-Khanza.~~ ~~Analisis korespondensi.~~ ~~Model kedua (GLM-5.3 Flash).~~ Selesai, lihat di atas.
2. **Pemilihan resource dari hasil matching, bukan dari deskripsi.** Prompt tahap 1 sudah mentok (katalog `elements` +3 hit@1 tanpa kenaikan recall; instruksi anti-FK kontraproduktif). Opsi yang tersisa:
   (a) LLM melihat 2–3 hasil matching per resource lalu memilih satu (satu panggilan kecil tambahan);
   (b) aturan struktural tanpa LLM, misalnya resource yang hanya ter-match lewat kolom FK (`*.encounter`, `*.subject`, `*.identifier`) didiskualifikasi;
   (c) model yang lebih besar (Gemini) khusus untuk tahap 1.
   Uji juga nama tabel sumber di tahap 1 untuk skema berkolom generik (`sipuskesmas`). Setiap perubahan pipeline harus dikonfirmasi ulang pada set held-out baru, karena set konfirmasi 18 pasangan sekarang sudah "terpakai".
4. Perbaiki ekor kamus: seed kecil akronim medis/administrasi, atau minta LLM mengekspansi singkatan sekali per sistem (ala Columbo), lalu bandingkan dengan kamus hasil tambang.
5. Ganti atau perkuat retriever (bge-m3 → retriever yang di-fine-tune ala Magneto, atau BM25 + embedding), karena recall@10 0,69 adalah plafon saat ini.
