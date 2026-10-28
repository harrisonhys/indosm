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
