# IndoSM — Laporan Pilot #1

26 Okt 2026 · pilot hari pertama dari PRD "Schema Matching Berbasis LLM untuk Integrasi Data Antar-Sistem"

## Ringkasan

**Sinyal: GO, dengan perubahan sumber data.** Gap kinerja yang dihipotesiskan PRD memang ada, tetapi tidak muncul di tempat yang diperkirakan.

1. **Data terbuka Satu Data (sub-set A) terlalu mudah untuk menguji H1.** Pada 10 pasangan natural antar-portal, COMA mencapai R@GT 0,93 untuk ID–ID, setara dengan LLM (0,90). Hanya 6% kolom di portal terbuka yang memuat singkatan, dan itu pun akronim domain (`SD`, `RS`, `L/P`), bukan gaya `kd_kec`/`jml_lk`.
2. **Singkatan birokrasi ada di skema sistem operasional.** Pada skema SIMRS Khanza (`pasien`) vs OpenSID (`tweb_penduduk`), COMA turun ke 0,44, sedangkan Qwen3-8B lokal tetap 0,78. Selisihnya 34 poin, dan arahnya sesuai H1.
3. **Lintas bahasa ID↔EN adalah gap terbesar dan paling konsisten.** COMA turun 0,93 → 0,50 pada pasangan portal dan ke 0,20 pada Khanza ↔ FHIR/SATUSEHAT. LLM lokal juga turun (0,90 → 0,71), tetapi tetap unggul.
4. **Model terbuka 8B on-premise sudah kompetitif.** Qwen3-8B di M3 Pro berjalan ±8 detik per pasangan tabel tanpa biaya API, sehingga RQ5 bisa diuji dengan murah.

Usulan revisi PRD ada di bagian akhir. Intinya: tambah **sub-set E (skema sistem informasi open-source Indonesia)** sebagai sumber utama pasangan bersingkatan, dan jadikan sub-set A pembanding "mudah".

## Apa yang dikerjakan

| Langkah | Hasil |
| --- | --- |
| Cek ulang kebaruan (Consensus + web) | Belum ada benchmark schema matching tabel berbahasa Indonesia maupun lintas bahasa ID↔EN. Lihat "Literatur tambahan" |
| Probe API CKAN ±90 host portal daerah | **20 portal** punya CKAN API aktif (mis. Kalbar 15 rb dataset, Kaltim 13 rb, Malang Kota 82 rb, Demak 28 rb) |
| Koleksi 3 indikator (penduduk, sekolah, puskesmas) | 103 resource CSV dari 10 portal, 88 tabel terbaca, 536 kolom (15 gagal: xlsx berlabel CSV, file rusak) |
| 10 pasangan natural + ground truth draf | 34 korespondensi, varian ID–ID / ID–EN / EN–EN |
| Pilot skema operasional (tanpa data instance) | SIMRS Khanza `pasien` (36 kolom) vs OpenSID `tweb_penduduk` (60) dan vs FHIR Patient datar (26) |
| Matcher | COMA, Cupid, Similarity Flooding, Jaccard (`valentine` 1.0.1), bge-m3 (Ollama), Qwen3-8B (Ollama, temp 0, seed 0) |

## Hasil

### A. Pasangan natural portal Satu Data (n = 10, metrik Recall@|GT|)

| Metode | ID–ID | ID–EN | EN–EN |
| --- | --- | --- | --- |
| COMA (schema + instance) | **0,925** [0,85–1,00] | 0,500 [0,32–0,68] | 0,925 |
| Similarity Flooding | 0,792 | 0,279 | 0,779 |
| Jaccard (instance) | 0,479 | 0,479 | 0,479 |
| Cupid | 0,258 | 0,000 | 0,083 |
| bge-m3 (nama + 3 sampel nilai) | 0,754 [0,62–0,89] | 0,612 [0,48–0,76] | 0,788 |
| Qwen3-8B zero-shot | 0,900 [0,75–1,00] | **0,712** [0,51–0,88] | 0,917 |

Kurung siku = bootstrap 95% CI atas pasangan. F1 (1:1 greedy) menunjukkan pola yang sama; lihat `results/pilot_scores.csv`.

### B. Skema sistem operasional, schema-only

| Metode | Khanza ↔ OpenSID (ID–ID, 18 GT) | Khanza ↔ FHIR Patient (ID–EN, 20 GT) |
| --- | --- | --- |
| COMA | 0,444 | 0,200 |
| Similarity Flooding | 0,278 | 0,100 |
| Cupid | 0,056 | 0,000 |
| bge-m3 | 0,389 | 0,250 |
| Qwen3-8B | **0,778** | **0,700** |

Contoh yang membedakan: `stts_nikah ↔ status_kawin`, `pnd ↔ pendidikan_kk_id`, `jk ↔ sex`, `tmp_lahir ↔ tempatlahir`, `nm_ibu ↔ mothersMaidenName`.

## Temuan tentang data (penting untuk desain benchmark)

- **Tabel portal kecil dan sering pivot.** Rata-rata 6 kolom; banyak yang "tahun sebagai kolom" (`2015 | 2016 | 2017`) sehingga korespondensi 1:1 tidak terdefinisi. Perlu aturan: hanya tabel format long, atau di-*melt* dulu.
- **Aceh sudah memakai standar penamaan** (`kemendagri_kode_kabupaten_kota`, `bps_kode_provinsi`, `satuan`). Ini kandidat bagus untuk sub-set B (dataset → standar).
- **Noise nyata, bukan sintetis**: header `Kecamatan` di Bengkulu berisi nama kabupaten; spasi nyasar (`kemendagri_kode_ kecamatan`); en-dash rusak (`0?4`); kode sama beda format (`11.01` vs `1101`); BPS vs Kemendagri memakai sistem kode wilayah berbeda.
- **Kasus anotasi yang perlu aturan tertulis**: kolom wilayah beda level administrasi (kecamatan vs kab/kota), satuan beda (`jumlah_penduduk(ribu)` vs jiwa), kolom pivot (`Negeri`/`Swasta` vs `status_satuan_pendidikan`), kode BPS vs kode Kemendagri.

## Status terhadap hipotesis PRD (indikatif, n kecil)

| H | Status pilot |
| --- | --- |
| H1 klasik turun > 20 poin, LLM < 10 | **Tidak** di data portal (tidak ada penurunan, karena header portal tidak bersingkatan). **Ya** di skema operasional (COMA 0,44 vs LLM 0,78) |
| H3 lintas bahasa: string gagal, embedding + LLM menutup gap | Sebagian. String-based jatuh (COMA −43 poin, Cupid → 0). bge-m3 hanya turun 14 poin tetapi titik awalnya rendah. LLM turun 19 poin, jadi gap belum tertutup |
| H5 model terbuka ≤ 14B layak | Menjanjikan: Qwen3-8B setara COMA di data mudah dan jauh di atasnya di data sulit. Pembanding API komersial belum jalan (lihat Keterbatasan) |
| H2, H4 | Belum diuji (pipeline hybrid dan kamus singkatan belum dibuat) |

## Keterbatasan pilot

- **Ground truth dan terjemahan EN dibuat oleh saya (Claude), satu anotator, belum diadjudikasi.** Perlakukan angka sebagai indikasi arah, bukan hasil.
- n = 10 + 2 pasangan; CI lebar.
- **Arm API komersial belum ada.** Kuota free tier Gemini (20 request/hari/model) habis di tengah run. Kode sudah siap (`USE_GEMINI=1`).
- **Risiko kebocoran data latih**: skema Khanza, OpenSID, dan FHIR publik di GitHub, sehingga LLM kemungkinan sudah pernah melihatnya. Ini memperkuat perlunya sub-set yang belum pernah dipublikasi.
- FHIR Patient diratakan secara manual (termasuk ekstensi SATUSEHAT: `birthPlace`, `religion`, `administrativeCode`).
- Cupid jauh di bawah laporan Valentine; kemungkinan konfigurasi default/threshold. Perlu dicek sebelum jadi baseline resmi.
- PRD menyebut `valentine` v1.1.0; yang terpasang dari PyPI adalah 1.0.1.

## Usulan revisi PRD

1. **Tambah sub-set E — skema sistem operasional open-source Indonesia** sebagai sumber utama untuk RQ1/RQ4: SIMRS Khanza (1.189 tabel), OpenSID, SLiMS, ditambah target standar (FHIR/SATUSEHAT, Feeder PDDikti, SIAK). Natural, bersingkatan, dan langsung relevan untuk ESB/ETL. **Cek lisensi dulu**: repo Khanza tidak mencantumkan lisensi; OpenSID dan SLiMS berlisensi GPL. Kemungkinan cukup merilis DDL dan GT saja.
2. **Sub-set A tetap dipakai, sebagai kondisi "mudah"/kontrol**, dan prioritaskan pasangan yang menuju standar Aceh-style (sub-set B).
3. **Jadikan RQ3 (lintas bahasa) kontribusi kedua yang sejajar dengan benchmark.** Desain "pasangan yang sama dalam 3 varian bahasa" mengontrol kesulitan pasangan dan ternyata efektif.
4. **Ubah H1 menjadi bersyarat pada gaya penamaan** (deskriptif vs bersingkatan), bukan pada bahasa Indonesia secara umum.
5. **Tambah Columbo (EMNLP Findings 2025) ke related work dan baseline RQ4.** Ini karya ekspansi singkatan nama kolom; reviewer hampir pasti menanyakannya.

## Literatur tambahan yang belum ada di PRD

- [Columbo: Expanding Abbreviated Column Names for Tabular Data Using LLMs](https://arxiv.org/abs/2508.09403) (Findings of EMNLP 2025) — ekspansi singkatan nama kolom; relevan langsung untuk RQ4
- [Automatic End-to-End Data Integration using LLMs](https://arxiv.org/pdf/2603.10547) (2026) — integrasi end-to-end dengan GPT-5.2
- OAEI MultiFarm — benchmark *ontology* matching multibahasa, tanpa bahasa Indonesia. Klaim "lintas bahasa belum ada" perlu dipersempit menjadi "untuk skema tabel/relasional"
- [Multilingual Schema Matching for Wikipedia Infoboxes](https://arxiv.org/pdf/1110.6651) (2011) — pendahulu matching lintas bahasa, untuk infobox
- [MultiSpider 2.0](https://arxiv.org/pdf/2509.24405) — text-to-SQL dengan skema yang dilokalisasi; pembanding untuk klaim "riset multibahasa hanya di text-to-SQL"

## Langkah berikutnya (urut prioritas)

1. Anotator kedua memeriksa `pairs.json`, GT di `ddl_pilot.py`, dan `data/translations_en.json`. Hitung kappa.
2. ~~Cek lisensi Khanza/OpenSID/SLiMS; susun 20–30 pasangan sub-set E.~~ Selesai 26 Okt: 28 pasangan, lihat [SUBSET_E.md](SUBSET_E.md).
3. Jalankan arm Gemini setelah kuota reset (atau aktifkan billing; perkiraan biaya pilot < 1 USD).
4. ~~Implementasi hybrid (bge-m3 top-k → Qwen rerank) dan kamus singkatan.~~ Selesai 26 Okt, lihat [HYBRID.md](HYBRID.md). Hasilnya: kamus menolong retrieval (+14 poin), hybrid tidak mengalahkan LLM penuh pada skema kecil.
5. Unduh benchmark Valentine untuk sanity check COMA/Cupid.

## Cara menjalankan ulang

```bash
cd indosm
uv run python collect.py        # unduh CSV dari portal (cache di data/raw)
uv run python pilot.py          # 10 pasangan × 3 varian bahasa × 6 matcher → results/pilot_scores.csv
uv run python ddl_pilot.py <sik.sql> <opensid.sql>   # skema operasional → results/ddl_pilot_scores.csv
```

Butuh Ollama dengan `bge-m3` dan `qwen3:8b`. `sik.sql` dari github.com/mas-elkhanza/SIMRS-Khanza, `contoh_data_awal_20210901.sql` dari github.com/OpenSID/OpenSID.
