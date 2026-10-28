# Tanggapan terhadap Reviewer

Naskah: *Single-Resource LLM Schema Matching of Indonesian Health Systems to FHIR* (judul sebelumnya: *Single-Resource Two-Stage LLM Matching of Indonesian Hospital Schemas to FHIR*)

Terima kasih atas review yang teliti. Semua angka baru dihitung dari respons model yang tersimpan di cache, tanpa menjalankan ulang model (`revision_analyses.py`). Rujukan halaman dan tabel di bawah mengacu pada naskah revisi.

Status: ✅ selesai di naskah · ⏳ menunggu data dari penulis (tidak bisa dikerjakan tanpa itu).

---

## Major comments

**1. Ground truth dan inter-annotator agreement** ⏳ (sebagian ✅)
- ✅ §2.1 kini menjelaskan empat kategori label (1:1, n:1, ambiguous, none), prosedur anotasi buta oleh annotator kedua, dua tingkat agreement, dan adjudikasi lewat diskusi.
  - Tingkat resource: proporsi tabel yang resource-nya disetujui.
  - Tingkat elemen: Cohen's κ atas label per kolom, plus F1 antar-tautan 1:1.
- ✅ Kit anotasi kini juga mengukur agreement tingkat resource (sheet "Resource"). Skrip `annotation_kit.py score` menghitung semua angka di atas dan menghasilkan daftar ketidaksepakatan untuk adjudikasi.
- ⏳ Nilai κ, agreement resource, jumlah label yang berubah, dan dua contoh disagreement belum bisa diisi karena annotator kedua belum menyelesaikan anotasi. Placeholder `[TBD]` di §2.1 akan diganti, dan semua tabel hasil akan dihitung ulang dari cache dengan gold standard hasil adjudikasi sebelum submisi.

**2. Asumsi one-resource-per-table** ✅
- Lingkup kini dinyatakan eksplisit:
  - di judul ("Single-Resource");
  - di abstrak ("each table maps to a single FHIR resource");
  - di tujuan (§1: "This paper studies the single-resource case").
- §3.4 menambah analisis sensitivitas. Dari 30 prediksi acak llm-full yang jatuh di luar resource gold, 6 (20%) dapat dibenarkan dalam pembacaan multi-resource, sebagian besar FK yang menunjuk resource rujukan. Jadi gold standard single-resource hanya sedikit mengurangi kredit lintas-resource.
- Tabel yang benar-benar mengisi beberapa resource dinyatakan sebagai batasan di §3.4 dan sebagai future work di §5.

**3. Definisi metrik** ✅
- §2.3 kini memuat prosedur evaluasi empat langkah (parse → hapus n:1/ambiguous → R@|GT| → assignment greedy tanpa |GT|), aturan tie-break, dan satu contoh perhitungan lengkap (`resep_obat`: R@|GT| = 0,40; P/R/F1 = 0,50/0,60/0,55).
- Tabel 6 (baru) melaporkan precision, recall, dan F1 *threshold-free*. Keputusannya adalah assignment greedy one-to-one atas semua prediksi dengan confidence > 0, tanpa mengetahui jumlah gold. Pola hasilnya sama dengan R@|GT|, jadi keunggulan metode bukan artefak pemeringkatan yang memakai |GT|.
- Catatan: F1 di naskah awal sudah threshold-free; hal ini kini dinyatakan eksplisit.

**4. Hasil konfirmatori belum signifikan** ✅
- §3.2 kini membedakan tiga tingkat bukti:
  - replikasi antar-model di set pengembangan;
  - konsistensi arah di sistem held-out, yang tidak terkonfirmasi secara statistik;
  - tidak ada klaim generalisasi lintas sistem.
- Abstrak dan kesimpulan memakai bahasa *directionally consistent but not statistically confirmed*.

**5. Keterkaitan seleksi stage-1 dan akurasi end-to-end** ✅
- Tabel 7 (baru) memuat:
  - akurasi top-1 dan top-3 per model dan set;
  - akurasi stage-2 yang dikondisikan pada pemilihan resource, dibandingkan dengan oracle pada tabel yang sama.
- Temuan utama: bila rank-1 benar, primary mencapai 0,728 (Qwen) dan 0,833 (GLM), di atas oracle pada tabel yang sama. Bila salah, skornya 0. Jadi pemilihan resource adalah hambatan utama.
- Pola confusion antar-resource diringkas di teks (Qwen: Patient untuk tabel staf; Encounter/DiagnosticReport untuk semua tabel rujukan, order, dan Observation yang meleset; GLM: kebanyakan Encounter, 7 dari 10). Matriks lengkap ada di output `revision_analyses.py` dalam repositori.

**6. Reproducibility dan preregistration** ✅ / ⏳
- ✅ §2.3 kini menyebut tanggal pra-registrasi dan isinya. Kami juga menyatakan terus terang bahwa protokol tidak didepositkan di registri eksternal, sehingga waktunya tidak dapat diverifikasi secara independen. Referensi [23] kini hanya dipakai sebagai rujukan praktik, bukan bukti.
- ✅ Teks prompt stage 1 dan stage 2 kini dikutip di §2.2.
- ✅ Pernyataan ketersediaan data dan kode ditambahkan: nama tabel/kolom, anotasi gold, pedoman, prompt, parser, respons model ter-cache, pra-registrasi, dan skrip statistik.
- ⏳ URL repositori dan hash commit belum diisi (lihat catatan untuk penulis di bawah).

## Pemeriksaan konsistensi

| Temuan reviewer | Tindakan |
| --- | --- |
| Tabel 4 vs abstrak (+12,3 vs +12,2) | Caption Tabel 5 dan §2.3: selisih dihitung dari nilai per tabel yang belum dibulatkan (0,1222 → +12,2) |
| Primary > oracle di tabel per resource | Dijelaskan di §3.2: oracle bukan batas atas. Prompt oracle memakai nama elemen polos (`identifier`), sedangkan prompt target besar memakai `Resource.path`, dan prefiks resource tampaknya membantu. Tabel 7 menunjukkan primary melampaui oracle pada tabel yang rank-1-nya benar. n kecil juga berperan |
| Caption Tabel 7 lama (31 vs 17) | Diganti Tabel 9 dengan definisi populasi yang eksplisit: tabel dev41 yang resource gold-nya bukan Encounter dan termasuk pilihan stage 1, dipisah menurut apakah Encounter juga dipilih. Analisis juga dihitung ulang dengan katalog `definition` (konfigurasi utama; versi lama memakai katalog `short`) dan diperluas ke GLM. Untuk GLM, tabel yang memicu Encounter tidak lebih sulit (oracle 0,75 vs 0,83), tetapi recall union jatuh dari 0,82 ke 0,32 |
| Presisi kamus 25% | §2.2: ukuran sampel (27/36; 10/40 dengan 5 ragu) dan konsekuensinya: ekspansi yang salah tampil di samping nama asli, jadi bisa menyesatkan tetapi tidak menyembunyikan nama kolom |
| "GLM 16–24 poin lebih akurat" | Diverifikasi dan dikoreksi: 21–29 poin di dev41 dan 3–15 poin di confirm18 |

## Minor comments

1. **Judul** ✅ *Single-Resource LLM Schema Matching of Indonesian Health Systems to FHIR* (10 kata, sesuai batas IJCCS). "Hospital" diganti "Health Systems", dan lingkup single-resource masuk ke judul.
2. **"About half its accuracy"** ✅ Diganti dengan angka dan konteksnya: recall turun dari 0,55 ke 0,35 pada tabel pengembangan.
3. **Baseline** ✅ §2.2 menjelaskan alasannya:
   - pencocok hybrid kami adalah desain retrieve-and-rerank ala ReMatch/Magneto tanpa komponen pelatihan;
   - Magneto melakukan fine-tuning retriever dan Matchmaker mengoptimasi demonstrasi in-context, keduanya di luar setting zero-training penelitian ini.
4. **"Seven systems" vs delapan baris** ✅ Tabel 1 kini berlabel "8 code bases, 7 systems". §2.1 menjelaskan bahwa OpenSID (register warga dan modul kesehatan) dihitung satu sistem.
5. **Figure 1** ✅ Korespondensi gold kini berada dalam kotak putus-putus berlabel "gold correspondences (illustration)", dan caption menyatakan bahwa itu bukan output model. Gambar sudah memakai lebar penuh area teks.
6. **Uji statistik** ✅ §2.3 menyatakan keluarga konfirmatori secara eksplisit: H1 dan H2, confirm18, Qwen3-8B, R@|GT|, satu sisi, Holm. Semua analisis lain, termasuk seluruh hasil GLM, set gabungan, dan analisis korespondensi, dinyatakan eksploratif dan tanpa koreksi.
7. **Placeholder** ⏳ Nama penulis, afiliasi, email, nama di footer, dan acknowledgement menunggu data penulis. Isian Vol./No./DOI dan tanggal Received/Revised/Accepted adalah bagian masthead template IJCCS yang diisi redaksi.

---

## Catatan untuk penulis (bukan untuk dikirim ke reviewer)

Sebelum submisi ulang:
1. **Annotator kedua.** Isi `annotation/anotasi_kedua.xlsx` (sheet "Resource" dan "Anotasi"), lalu jalankan `python annotation_kit.py score <file>`, adjudikasi, dan rescore.
2. **Nama, afiliasi, dan email penulis** untuk header dan footer.
3. **URL repositori dan hash commit.** Repositori `harrisonhys/indosm` saat ini **publik dan memuat dump mentah** (`data/subset_e/raw/`, termasuk `sik.sql`) yang menurut SUBSET_E.md tidak boleh diredistribusi. Sebelum tautannya dicantumkan di naskah, sebaiknya buat repositori rilis yang bersih (tanpa `raw/`), atau bersihkan repositori ini.

---

# Putaran 2

Analisis baru ada di `revision2_analyses.py`, yang dijalankan per model. Panggilan LLM baru hanya untuk prompt yang belum ada di cache: 55 untuk Qwen (lokal) dan 66 untuk GLM (API). Kebijakan evaluasi deployment ditulis di docstring skrip **sebelum** angkanya dihitung.

## Major comments

**1. Evaluasi memakai label gold untuk menyaring prediksi** ✅
- §2.3 kini mendefinisikan tiga kebijakan:
  - *annotation-neutral*: metrik lama yang dipra-registrasi. Dinyatakan eksplisit bahwa metrik ini mengukur subset pasangan yang dapat dinilai dan memakai label gold untuk menyaring.
  - *deployment-strict*: tanpa penyaringan berbasis gold. Setiap pasangan yang di-assign dan bukan gold 1:1 dihitung false positive; ini batas bawah kinerja operasional.
  - *deployment-lenient*: n:1 dan ambiguous dihitung benar dalam presisi; ini acuan atas.
- Juga dinyatakan bahwa kebijakan deployment ditambahkan setelah review pertama tetapi ditetapkan sebelum dihitung.
- Tabel 6 kini melaporkan P/R/F1 deployment-strict, plus F1 neutral dan lenient, untuk kedua model. Ketiga kebijakan berbeda paling banyak 0,04 F1, dan urutan konfigurasinya sama.
- Tabel 5 menambah selisih F1 deployment-strict: primary − llm-full gabungan +11,7 (Qwen, p = 0,004) dan +13,8 (GLM, p < 0,001). Semuanya eksploratif.

**2. Klaim "oracle bukan batas atas" perlu diuji** ✅ (eksperimen dijalankan)
- Kami menjalankan ablasi yang disarankan (Tabel 8):
  - oracle-A: resource gold, nama elemen polos;
  - oracle-B: resource gold, nama `Resource.path`;
  - primary.
- Temuan mekanis: untuk tabel yang rank-1-nya benar, prompt primary identik dengan prompt oracle-B, dan skornya terbukti sama persis untuk kedua model. Jadi primary = oracle-B × [rank-1 benar].
- Hasil: oracle-B − oracle-A gabungan +5,0 poin R@|GT| untuk Qwen (CI 0,5..9,5; p = 0,026) dan +2,1 untuk GLM (CI −1,9..6,3; p = 0,35).
- Klaim di naskah disesuaikan: format berprefiks membantu model kecil, dan efeknya kecil atau tidak terdeteksi pada model besar. Kalimat lama "the resource prefix appears to help the model" dihapus.

**3. Inter-annotator agreement** ⏳ (prosedur ✅)
- Skrip skor kini melaporkan empat ukuran secara terpisah, sesuai permintaan:
  - agreement pemilihan resource;
  - agreement kategori (1:1/n:1/ambiguous/none), raw dan κ;
  - agreement elemen, κ;
  - exact agreement/F1 pasangan (kolom sumber, elemen FHIR).
- Jumlah label yang berubah setelah adjudikasi dihitung dari daftar ketidaksepakatan.
- Angkanya tetap menunggu annotator kedua.

**4. Baseline dan klaim novelty** ✅ (kedua opsi)
- Klaim kontribusi dibatasi eksplisit ke setting *zero-training, schema-only, single-resource*. Ditambahkan juga: "We do not claim superiority over trained matchers, which we do not evaluate."
- Baseline struktural yang disarankan ditambahkan (Tabel 8): klasifikasi resource berbasis embedding (bge-m3, tabel vs definisi resource, dengan dan tanpa nama elemen), lalu stage-2 LLM yang sama.
- Hasilnya:
  - top-1 hanya 27% (vs 64% Qwen dan 83% GLM untuk stage-1 LLM);
  - end-to-end di bawah llm-full (Qwen −11,9; GLM −36,0 poin).
- Kesimpulannya: manfaat metode berasal dari penggunaan LLM untuk memilih resource, bukan sekadar dari adanya langkah klasifikasi resource.

**5. Sensitivitas multi-resource** ✅
- Dinyatakan sebagai pemeriksaan kualitatif dan eksploratif. Klaim "understates ... by a modest amount" dihapus.
- Ditambahkan bahwa sampel 30 prediksi tanpa gold alternatif hasil adjudikasi tidak cukup untuk mengestimasi perubahan R@|GT| atau F1.

## Temuan teknis

| Catatan | Tindakan |
| --- | --- |
| Tabel 3 tanpa n per kelompok | n ditambahkan di setiap kolom. Caption menyatakan 25 dari 28 pasangan baseline yang ditampilkan, dan tiga kelompok satu-pasangan yang dihilangkan disebut namanya |
| Agregasi Tabel 6 | §2.3: P, R, F1 dihitung per tabel lalu macro-average; F1 adalah rata-rata F1 per tabel, bukan harmonic mean dari rata-rata P dan R |
| Tabel 7: skor 0 bila rank-1 salah | Dinyatakan sebagai konsekuensi protokol anotasi single-resource, bukan temuan empiris |
| Header "Union R@ \| GT\|" terpisah | Bug pemformatan pada pembangkit naskah (pemisah sel tabel). Sudah diperbaiki, header kini "Union R@\|GT\|" |
| Konfirmasi manusia di §3.4 | Dinyatakan sebagai implikasi yang belum diuji, tanpa user study. Biaya, beban kerja, dan akurasi konfirmasi manusia disebut sebagai hal yang belum diukur |
| Pra-registrasi tanpa bukti waktu independen | Tetap dinyatakan terus terang di §2.3; tidak ada klaim tambahan |
| Placeholder penulis/repositori | ⏳ menunggu data penulis |

Naskah revisi: 12 halaman pada render LibreOffice (halaman 12 terisi ±¼), 11 tabel, 1 gambar, 29 referensi.

---

# Putaran 3

Tidak ada eksperimen model baru di putaran ini. Perubahannya ada pada desain anotasi, definisi formal, dan kalibrasi klaim.

**Penilaian B (ablasi stage 1)** ✅ Kesimpulan disesuaikan persis seperti saran: "LLM resource selection is therefore more effective than the two simple embedding classifiers we tested; this does not show that no non-LLM classifier could work."

**Comment 1: IAA dan "resource acceptance"** ✅ (desain) / ⏳ (angka)
- Reviewer benar: prosedur sebelumnya mengukur *acceptance*, bukan agreement. Karena anotasi kedua belum dilaksanakan, kami **memperbaiki desainnya**, bukan sekadar mengganti istilah.
- Annotator kedua kini bekerja dalam dua tahap:
  - **Tahap 1** (`annotation/anotasi_kedua_tahap1_resource.xlsx`): memilih resource tiap tabel secara independen, hanya dari nama tabel dan kolom. Resource yang ditetapkan tidak tampil di file ini; ini sudah diverifikasi.
  - **Tahap 2**: file tahap 2 baru diberikan setelah tahap 1 dikembalikan, dan berisi label per kolom terhadap resource yang ditetapkan.
- Dengan desain ini agreement pemilihan resource adalah agreement sungguhan antara dua pilihan independen (raw dan Cohen's κ atas 11 resource).
- §2.1 kini melaporkan empat ukuran: seleksi resource, kategori anotasi, elemen target, dan pasangan exact, ditambah jumlah label yang berubah setelah adjudikasi.
- Angkanya tetap menunggu annotator kedua.

**Comment 2: definisi deployment-lenient** ✅
- §2.3 kini memuat definisi formal. G = gold 1:1, X = gold n:1 dan ambiguous, A = assignment greedy one-to-one:
  - A dihitung **sekali atas semua prediksi** untuk kedua kebijakan deployment, sebelum status n:1 dilihat;
  - untuk kebijakan neutral, A dihitung setelah prediksi di X dibuang;
  - P = |A∩G|/|A| (strict, neutral) atau |A∩(G∪X)|/|A| (lenient);
  - R = |A∩G|/|G| untuk semua kebijakan, sehingga penyebut recall selalu jumlah gold 1:1;
  - F1 = 2PR/(P+R) per tabel.
- Ditambahkan penjelasan mengapa F1 neutral bisa melebihi F1 lenient: assignment neutral dihitung tanpa prediksi X, sehingga elemen yang semula direbut prediksi X bisa jatuh ke pasangan gold.

**Comment 3: bukti statistik eksploratif** ✅ Satu kalimat eksplisit ditambahkan di §3.2: hasil GLM deployment-strict pada confirm18 (+12,0; CI 0,5..24,2; p = 0,037) adalah bukti eksploratif dari analisis yang ditambahkan setelah pra-registrasi, tanpa koreksi multiplisitas, dan bukan konfirmasi independen atas H1.

**Comment 4: kesimpulan human confirmation** ✅ Diganti dengan kalimat yang disarankan: "Human confirmation of the selected resource is a promising safeguard, although its practical cost and effectiveness remain to be evaluated."

**Comment 5: reproducibility dan presentasi**
- ✅ **Versi model** kini spesifik:
  - Ollama 0.40.4, `qwen3:8b` digest 500a1f067a9f (Q4_K_M);
  - `bge-m3` digest 790764642607 (F16);
  - GLM-5.3-Flash lewat API Neuralwatt, model id `glm-5.3-flash` (bobot `zai-org/GLM-5.3-Flash`), diakses 28 Oktober 2026.
  
  Juga dinyatakan bahwa penyedia API tidak mengunci checkpoint, sehingga hasil API direproduksi dari cache respons yang dirilis, bukan dengan memanggil ulang.
- ✅ **Header tabel yang terpecah** (Tabel 8 dan 10, juga caption): "R@|GT|" sebelumnya terpotong setelah "|" di sel sempit. Kini dikunci dengan karakter *word joiner*, sehingga tidak lagi terpecah; sudah diverifikasi pada render.
- ✅ **Pra-registrasi**: file pra-registrasi memuat konfigurasi beku, hipotesis, uji, kriteria, hash SHA-256 GT, dan hasil konfirmatori. Kini ditambahkan **addendum bertanggal** yang mendaftar semua analisis pasca-review (putaran 1 dan 2, termasuk lengan GLM) sebagai eksploratif. Naskah (§2.3) merujuk addendum ini.
- ⏳ URL repositori, hash commit, identitas penulis, dan placeholder anotasi menunggu data penulis. DOI, tahun, dan tanggal editorial adalah isian masthead template yang diisi redaksi IJCCS.

Naskah: 12 halaman (render LibreOffice; halaman 12 terisi ±45%).

---

# Putaran 4

Tidak ada eksperimen model baru. Perubahannya: uji unit evaluator, ukuran agreement tambahan, dan tiga penyesuaian teks.

**Comment 1: IAA** ⏳ (angka) / ✅ (metodologi)
- **κ elemen yang menggelembung karena "none"**: skrip skor kini juga menghitung agreement elemen hanya pada kolom yang dipetakan oleh setidaknya satu annotator. §2.1 menyebut kedua versi, dan exact-link F1 dinyatakan sebagai ukuran agreement utama.
- **Informasi annotator vs model**: §2.1 kini menyatakan bahwa annotator melihat nama tabel dan nama kolom, sedangkan matcher sengaja hanya menerima nama dan tipe kolom. Gold standard adalah acuan yang dibangun dengan konteks lebih kaya daripada yang diberikan ke model.
- Angka agreement tetap menunggu annotator kedua (tahap 1, lalu tahap 2).

**Comment 2: konsistensi implementasi ketiga kebijakan** ✅
- Uji unit evaluator ditambahkan: `tests/test_evaluation.py`, 8 uji assert tanpa framework, dijalankan dengan `python tests/test_evaluation.py`, dan semuanya lulus. Kasus yang dicakup sesuai permintaan reviewer:
  - tabel tanpa prediksi (*unmatched*) dan confidence 0;
  - dua kolom yang memperebutkan elemen yang sama (*collision*);
  - prediksi n:1 di bawah ketiga kebijakan, termasuk kasus F1 neutral > lenient > strict;
  - prediksi ambiguous;
  - confidence sama, dengan urutan output model yang dipertahankan;
  - potongan R@|GT| saat ada nilai yang sama.
- Satu uji memeriksa seluruh 826 baris hasil nyata (dua model): recall strict dan lenient identik di setiap baris, dan presisi lenient tidak pernah di bawah strict. Ini mengonfirmasi bahwa A untuk strict dan lenient benar-benar berasal dari assignment yang sama.

**Comment 3: ketidakmerataan per resource** ✅ Satu kalimat ditambahkan di §3.2: peningkatan rata-rata tidak berlaku untuk setiap resource. Dengan Qwen, ServiceRequest (rujukan dan order) tetap 0 dan Practitioner turun, sehingga mapping ke resource tersebut memerlukan validasi manual yang lebih ketat sebelum dipakai.

**Comment 4: klaim statistik dan istilah pra-registrasi** ✅
- Narasi konfirmatori tidak diubah.
- Istilah kini "internally pre-registered", di abstrak (EN dan ID), kontribusi, dan §2.3. §2.3 menjelaskan eksplisit bahwa protokol adalah dokumen internal di repositori proyek, bukan entri di registri eksternal.

**Penyesuaian panjang.** Naskah tetap 12 halaman (halaman 12 terisi ±65% pada render LibreOffice). Untuk menjaga margin:
- Tabel 2 dipersingkat menjadi cuplikan; caption menyebut isinya: 4 dari 7 pasangan 1:1, kolom n:1, dan 1 dari 2 kolom ambiguous.
- Baris "definisi + nama elemen" di Tabel 8 dipindah ke teks.
- Tabel 11 hanya memuat dua konfigurasi yang dibandingkan.
- Kalimat analisis tingkat korespondensi dihapus; bukti gabungan yang sama sudah ada di Tabel 5.
