# Pra-registrasi: konfirmasi primary[rank1] pada pasangan non-Khanza → FHIR

Ditulis 27 Okt 2026, **sebelum** GT pasangan baru didraf dan sebelum pipeline dijalankan pada skema baru. Setelah file ini ditulis, konfigurasi tidak boleh diubah. Ini untuk menghindari bias *post hoc* yang tercatat di HYBRID.md (katalog `def`, satu resource utama, dan aturan `rank1` semuanya dipilih di 41 pasangan Khanza yang sama).

## Data

- Set konfirmasi = pasangan tabel → FHIR R4 dari sistem Indonesia **selain Khanza** (dan selain turunan Khanza seperti mLITE). Set ini disimpan terpisah di `data/subset_e/pairs_confirm.json` / `pairs_confirm_large.json`, tidak dicampur ke `pairs_e.json`.
- Nama kolom sumber berbahasa Indonesia (atau campuran ID). Skema dengan identifier berbahasa Inggris (mis. `aisahana/eclinic_api`) tidak dimasukkan.
- GT didraf dengan konvensi SUBSET_E.md, plus aturan tanda vital dari `draft_pairs_e_more.py`. Penyusun draf (Claude) **tidak melihat output model** pada skema ini sebelum GT dibekukan. GT dibekukan dengan menulis file pairs dan mencatat hash SHA-256-nya di bawah sebelum run pertama.
- Target = gabungan 11 resource FHIR (`fhir__ALL`, 289 elemen), sama seperti n=41.

## Konfigurasi (beku)

Semua memakai Qwen3-8B lokal (temp 0, seed 0) dan kamus singkatan **Khanza** (`data/abbrev_khanza.json`, tanpa ditambang ulang; jadi ini juga uji transfer kamus).

| Nama | Definisi |
| --- | --- |
| `llm-full+dict` | satu prompt, semua kolom × 289 elemen (`hybrid.llm_full`) |
| `union[def]` | tahap 1 katalog `def` (`stage1_rich.catalogs()["def"]`), tanpa hint; tahap 2 gabungan resource terpilih (`two_stage.two_stage(..., catalog=def)`) |
| `primary[rank1]` | tahap 1 sama; tahap 2 hanya pada resource peringkat 1 (`stage1_primary_hint.py`, sel `def\|none`) |
| `oracle+dict` | resource benar diberikan (target kecil); plafon, bukan uji |

## Hipotesis dan uji

- Metrik utama: **R@|GT| n:1-netral** per pasangan (`rescore_n40.neutral`). Metrik sekunder: F1 n:1-netral.
- **H1:** primary[rank1] > llm-full+dict.
- **H2:** primary[rank1] > union[def].
- Uji: Wilcoxon signed-rank **satu sisi**, α = 0,05, koreksi **Holm** untuk H1 dan H2. Selain itu dilaporkan bootstrap 95% CI (10k, seed 0) dari selisih rata-rata, dan w/t/l.
- Power yang diperkirakan rendah: dengan SD selisih ±0,28 (dari n=41) dan efek +0,137, n = 20 memberi power satu sisi ±0,70. **Hasil tidak signifikan bukan bukti tidak ada efek.** Yang diharapkan adalah arah dan besar efek yang konsisten dengan n=41.
- Analisis sekunder (eksploratif, tidak dikoreksi): hit/hit@1 tahap 1 per resource; gabungan n=41 + set konfirmasi.

## Kriteria "terkonfirmasi"

H1 terkonfirmasi bila p_Holm < 0,05. Bila tidak, dilaporkan "arah konsisten" jika selisih rata-rata > 0 dan CI-nya tumpang tindih dengan CI n=41 (+3,8..+23,7), atau "tidak konsisten" jika selisihnya ≤ 0.

## Hash GT (diisi saat GT dibekukan)

Dibekukan 27 Okt 2026 sebelum run pertama (`draft_confirm.py`): 18 pasangan dari 6 sistem, 69 gt, 6 n:1, 10 ambigu.

- `pairs_confirm.json`: `f488e8b687ac617fd5fd840019824b9e2b96303fe506236584350b40364f7057`
- `pairs_confirm_large.json`: `36e7ca9f7d91f1eb0af562021eaeb8d0530c08d33ac5a0546e8793e295b5702f`

Penyimpangan dari rencana: n = 18, bukan ±20. Sumber berlisensi jelas yang punya tabel klinis dengan ≥ 2 korespondensi ternyata terbatas. Power satu sisi untuk efek +0,137 menjadi ±0,65.

## Hasil (ditambahkan setelah run, 27 Okt 2026)

`run_confirm.py` (90 panggilan LLM baru, hash GT terverifikasi) → `results/confirm.csv`; `analyze_confirm.py`.

| Uji | Δ R@\|GT\| (95% CI) | w/t/l | p satu sisi | p Holm | Status |
| --- | --- | --- | --- | --- | --- |
| H1 primary[rank1] − llm-full+dict | +12,2 (−0,2..+27,2) | 4/13/1 | 0,069 | 0,138 | **tidak terkonfirmasi; arah konsisten** (CI tumpang tindih dengan +3,8..+23,7) |
| H2 primary[rank1] − union[def] | +6,5 (−6,7..+20,2) | 4/12/2 | 0,173 | 0,173 | tidak terkonfirmasi; arah konsisten |

F1 (sekunder): H1 +8,6 (CI −2,7..+21,1), H2 +6,7 (CI −6,1..+20,3), keduanya ns. Interpretasi dan analisis eksploratif ada di HYBRID.md.

## Addendum: analisis setelah review (28 Okt 2026, ditambahkan setelah hasil konfirmatori diketahui)

Semua analisis di bawah ini **eksploratif**. Analisis ini tidak termasuk keluarga uji konfirmatori (H1 dan H2) dan tidak mengubah hasil H1/H2 di atas. Hash GT tetap sama dan masih diverifikasi oleh skrip.

1. **Review putaran 1** (`revision_analyses.py`): P/R/F1 threshold-free dengan kebijakan annotation-neutral; seleksi stage 1 (top-1/top-3) dan akurasi stage 2 kondisional; absorpsi Encounter dengan katalog `definition` untuk dua model.
2. **Review putaran 2** (`revision2_analyses.py`). Kebijakan evaluasinya ditulis di docstring skrip sebelum angka dihitung:
   - *deployment-strict*: tanpa penyaringan berbasis gold;
   - *deployment-lenient*: n:1/ambiguous dihitung benar dalam presisi;
   - *oracle-B*: resource gold dengan nama `Resource.path`;
   - stage 1 berbasis embedding (bge-m3; definisi, atau definisi + nama elemen).
3. **Model kedua (GLM-5.3-Flash)**: semua hasilnya eksploratif. Konfigurasi dibekukan pada Qwen dan tidak disetel ulang.
