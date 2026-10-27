-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 06 Jan 2023 pada 09.54
-- Versi server: 10.4.24-MariaDB
-- Versi PHP: 8.1.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_puskesmas`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `obat`
--

CREATE TABLE `obat` (
  `id_obat` int(11) NOT NULL,
  `nama` varchar(255) NOT NULL,
  `kategori` varchar(255) NOT NULL,
  `deskripsi` varchar(1000) NOT NULL,
  `harga` double NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data untuk tabel `obat`
--

INSERT INTO `obat` (`id_obat`, `nama`, `kategori`, `deskripsi`, `harga`) VALUES
(2, 'Naproxen', 'Obat Radang', 'Naproxen adalah obat untuk meredakan nyeri, demam, bengkak, dan kemerahan akibat peradangan.', 350000),
(3, 'Obat Tikus', 'Racun', 'Ini adalah Obat Tikoes', 50000),
(5, 'Sanmol', 'Obat Demam', 'Sanmol mengandung paracetamol yang efektif dalam membantu meringankan gejala flu seperti demam, sakit kepala, serta badan nyeri atau pegal-pegal', 15000);

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `id_user` int(10) NOT NULL,
  `nama` varchar(255) NOT NULL,
  `no_telp` varchar(15) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(256) NOT NULL,
  `role` varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`id_user`, `nama`, `no_telp`, `email`, `password`, `role`) VALUES
(17, 'Faza Alexander Riawan', '081234664826', 'fazaalexander@gmail.com', '$2y$10$/nnBpQHj6wcaK/jBKqFSiuzZpbc3XEliy6UK6JemYI2j94FaS2yDO', ''),
(20, 'fazaaa', '081', 'fazaaa@gmail.com', '$2y$10$QnpmsvtIrj.GXWSTz/bgnOOPhRRhxy.1FE4wcnGQczT6ZCEHrktVi', ''),
(21, 'mahendra', '081', 'mahendra@gmail.com', '$2y$10$NIao8L83N2luBQX.ujLHIOcceucmcjMRr9dxHEKn2M.MQK/CFIqY.', ''),
(22, 'Dasha Taran', '08123999', 'dashataran@gmail.com', '$2y$10$uO8xC6UhFDXbOlHPMSsT1.aqMIaRqnadZDivTpEdfMEV9UxpUMqk6', 'pasien'),
(23, 'inidokter', '081234664827', 'dokter@gmail.com', '$2y$10$t4thrmz.5v1Ts7PHPCGfr.PijQwbdv9oN5FRC6dzr2uVQrJSZKnIG', 'dokter');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `obat`
--
ALTER TABLE `obat`
  ADD PRIMARY KEY (`id_obat`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `obat`
--
ALTER TABLE `obat`
  MODIFY `id_obat` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT untuk tabel `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int(10) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
