# Draf permintaan izin rilis (dikirim sendiri oleh peneliti)

Yang dirilis dari setiap sumber hanya **nama tabel, nama kolom, dan tipe kolom** dari skema publik, ditambah anotasi korespondensi ke FHIR R4 buatan kami. Tidak ada kode aplikasi, data contoh, atau file SQL asli.

Kirim lewat kanal resmi masing-masing: email di repo/website, atau GitHub issue/discussion bila tidak ada email. Ganti `[...]` sebelum mengirim.

| Sumber | Status lisensi | Kanal yang disarankan | Tanpa izin |
| --- | --- | --- | --- |
| SIMRS Khanza (Khanza.Soft Media) | lisensi khusus, larangan komersial | email/WA di `lisensi.txt` atau README repo | pasangan Khanza (54 + bagian set pengembangan) tidak dirilis; paper tetap bisa melaporkan angka agregat |
| `idiknursidik/siakad` | tidak jelas (lisensi CodeIgniter) | GitHub issue | 6 pasangan SIAKAD↔Feeder tidak dirilis (bukan bagian hasil utama) |
| `arfandotid/ci_rekammedis` | tidak jelas (lisensi CodeIgniter) | GitHub issue | 6 pasangan konfirmasi C09–C14 tidak dirilis |
| `Slyzyy/TUBES_WEBPRO_e-Puskesmas` | tidak jelas (lisensi CodeIgniter) | GitHub issue | 1 pasangan C17 tidak dirilis |

---

## 1. Khanza.Soft Media (SIMRS Khanza)

**Subjek:** Permohonan izin penggunaan skema SIMRS Khanza untuk benchmark riset non-komersial

Yth. Tim Khanza.Soft Media,

Saya [nama], [jabatan/afiliasi]. Saat ini saya meneliti pencocokan skema (*schema matching*) berbasis LLM untuk integrasi data antarsistem di Indonesia, misalnya pemetaan tabel SIMRS ke HL7 FHIR/SATUSEHAT.

Dalam penelitian ini kami memakai nama tabel dan nama kolom dari `sik.sql` (repo mas-elkhanza/SIMRS-Khanza, commit `8a6431dcb3`) untuk sekitar 40 tabel, beserta anotasi pemetaan ke FHIR R4 yang kami susun sendiri. Kami memohon izin untuk:
1. menerbitkan hasil penelitian yang menyebut SIMRS Khanza sebagai sumber skema, dan
2. merilis daftar nama tabel/kolom tersebut beserta anotasi FHIR-nya sebagai dataset riset terbuka non-komersial (lisensi CC BY 4.0 untuk anotasi), dengan atribusi penuh kepada Khanza.Soft Media.

Kami tidak merilis kode, file SQL, maupun data apa pun, dan tidak ada penggunaan komersial. Kami akan dengan senang hati mengirimkan draf paper dan dataset sebelum terbit, dan menyesuaikan atribusi sesuai keinginan Bapak/Ibu.

Terima kasih atas karya SIMRS Khanza yang sangat bermanfaat bagi fasilitas kesehatan di Indonesia.

Hormat saya,
[nama, afiliasi, email, nomor kontak]

---

## 2–4. Repositori GitHub (template issue: `idiknursidik/siakad`, `arfandotid/ci_rekammedis`, `Slyzyy/TUBES_WEBPRO_e-Puskesmas`)

**Judul issue:** Permission to reuse table/column names in a research dataset (izin pemakaian nama tabel/kolom untuk dataset riset)

Halo [username],

Saya [nama] dari [afiliasi]. Saya sedang membuat benchmark riset non-komersial untuk pencocokan skema basis data Indonesia ke standar (HL7 FHIR R4 / PDDikti Feeder).

Kami memakai **nama tabel dan nama kolom** dari `[file, mis. database/rekam_medis.sql]` (commit `[sha]`) di repo ini, beserta anotasi pemetaan buatan kami sendiri. File `license.txt` di repo ini adalah lisensi framework CodeIgniter, sehingga kami belum tahu lisensi untuk aplikasinya sendiri.

Bolehkah kami merilis nama tabel/kolom tersebut (tanpa kode dan tanpa data) dengan atribusi ke repo ini, dalam dataset berlisensi CC BY 4.0? Kalau Anda berkenan menambahkan lisensi untuk aplikasinya (mis. MIT), itu juga sudah cukup.

Terima kasih!

[nama, afiliasi, email]

Isian per repo:
- `idiknursidik/siakad`: file `siakad.sql`, commit `05f0b8fe19`, standar target = PDDikti Feeder.
- `arfandotid/ci_rekammedis`: file `database/rekam_medis.sql`, commit `606cd16795`, target = FHIR R4.
- `Slyzyy/TUBES_WEBPRO_e-Puskesmas`: file `db_puskesmas.sql`, commit `82f97d411f`, target = FHIR R4.
