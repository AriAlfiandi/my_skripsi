================================================================================
                    SISTEM VIRTUAL MOUSE DENGAN HAND TRACKING
                         + FITUR PENGUJIAN AKURASI
================================================================================

DESKRIPSI PROYEK:
-----------------
Sistem virtual mouse yang menggunakan webcam dan hand tracking untuk mengontrol
mouse komputer. Dilengkapi dengan sistem pengujian lengkap untuk mengukur
akurasi, true positive, false positive, dan false negative.

DIBUAT OLEH:
------------
Ari Alfiandi
NIM: 2105903040091
Program Studi Teknologi Informasi
Universitas Teuku Umar

================================================================================
FITUR UTAMA:
================================================================================

1. KONTROL MOUSE DENGAN GESTURE TANGAN:
   ✓ Gerakkan kursor dengan telunjuk
   ✓ Scroll ke atas (jempol-telunjuk dekat)
   ✓ Scroll ke bawah (jempol-telunjuk jauh)
   ✓ Klik kiri (jempol-kelingking dekat)
   ✓ Toggle scroll on/off (kepal tangan)

2. SISTEM PENGUJIAN TERINTEGRASI:
   ✓ Tracking real-time setiap gesture
   ✓ Konfirmasi True Positive / False Positive
   ✓ Pencatatan False Negative
   ✓ Perhitungan akurasi otomatis
   ✓ Laporan lengkap (JSON & TXT)

3. ANALISIS DAN VISUALISASI:
   ✓ Chart akurasi per gesture
   ✓ Chart confusion metrics (TP/FP/FN)
   ✓ Pie chart distribusi keseluruhan
   ✓ Tabel analisis untuk skripsi

================================================================================
PERSYARATAN SISTEM:
================================================================================

HARDWARE:
---------
• Webcam (built-in atau eksternal)
• RAM minimal 4GB
• Prosesor minimal Intel i3 atau setara

SOFTWARE:
---------
• Python 3.7 atau lebih baru
• Webcam driver yang terinstal

LIBRARY PYTHON:
---------------
Jalankan command berikut untuk install semua library:

pip install opencv-python cvzone mediapipe pynput screeninfo matplotlib numpy

atau:

pip install -r requirements.txt

================================================================================
CARA INSTALASI:
================================================================================

1. Clone atau download repository ini
2. Buka terminal/command prompt di folder project
3. Install dependencies:
   pip install -r requirements.txt
4. Jalankan program:
   python virtual_mouse_with_testing.py

================================================================================
FILE-FILE DALAM PROJECT:
================================================================================

1. virtual_mouse_with_testing.py
   → Program utama dengan fitur pengujian

2. analisis_hasil_pengujian.py
   → Script untuk analisis dan visualisasi hasil

3. PANDUAN_PENGUJIAN.txt
   → Panduan lengkap cara melakukan pengujian

4. README.txt
   → File ini (dokumentasi lengkap)

5. laporan_pengujian.json (auto-generated)
   → File hasil pengujian dalam format JSON

6. laporan_pengujian.txt (auto-generated)
   → File hasil pengujian dalam format text untuk skripsi

7. chart_*.png (auto-generated)
   → File visualisasi hasil pengujian

================================================================================
CARA PENGGUNAAN:
================================================================================

LANGKAH 1: JALANKAN PROGRAM PENGUJIAN
--------------------------------------
python virtual_mouse_with_testing.py

LANGKAH 2: LAKUKAN PENGUJIAN
-----------------------------
• Posisikan tangan di depan kamera
• Lakukan gesture yang ingin diuji
• Konfirmasi setiap deteksi:
  [Y] = Deteksi benar (True Positive)
  [N] = Deteksi salah (False Positive)
  [F] = Gesture tidak terdeteksi (False Negative)

LANGKAH 3: LIHAT STATISTIK
---------------------------
• Tekan [S] untuk melihat statistik real-time
• Tekan [Q] untuk keluar dan menyimpan laporan

LANGKAH 4: ANALISIS HASIL
--------------------------
python analisis_hasil_pengujian.py

Ini akan menghasilkan:
• 3 file chart (PNG) untuk visualisasi
• 1 file tabel analisis (TXT) untuk skripsi

================================================================================
TOMBOL KONTROL:
================================================================================

SAAT MENJALANKAN PROGRAM:
--------------------------
[Y]     = Konfirmasi True Positive (deteksi benar)
[N]     = Konfirmasi False Positive (deteksi salah)
[F]     = Input False Negative (gesture tidak terdeteksi)
[S]     = Tampilkan statistik saat ini
[R]     = Reset statistik
[Q]     = Keluar dan simpan laporan

GESTURE TANGAN:
---------------
Telunjuk              → Gerakkan kursor
Jempol-Telunjuk dekat → Scroll ke atas
Jempol-Telunjuk jauh  → Scroll ke bawah
Jempol-Kelingking     → Klik kiri
Kepal tangan          → Toggle scroll on/off

================================================================================
METODOLOGI PENGUJIAN UNTUK SKRIPSI:
================================================================================

PENGUJIAN TERSTRUKTUR (RECOMMENDED):
-------------------------------------
1. Siapkan 10-20 percobaan untuk setiap gesture
2. Catat setiap hasil (TP/FP/FN)
3. Hitung akurasi per gesture dan keseluruhan
4. Dokumentasikan kondisi pengujian:
   - Pencahayaan
   - Jarak dari kamera
   - Spesifikasi hardware

CONTOH PROTOKOL PENGUJIAN:
--------------------------
• 20 kali Scroll Up
• 20 kali Scroll Down
• 20 kali Klik
• 20 kali Toggle Scroll
• 20 kali Gerak Kursor
------------------------
Total: 100 gesture

Target minimal: Akurasi ≥ 80%

================================================================================
INTERPRETASI HASIL:
================================================================================

METRIK PENGUJIAN:
-----------------
• True Positive (TP)   : Deteksi benar
• False Positive (FP)  : Deteksi salah
• False Negative (FN)  : Gagal mendeteksi
• Akurasi = (TP / (TP + FP + FN)) × 100%

KATEGORI AKURASI:
-----------------
≥ 90% = Sangat Baik (Excellent)
80-90% = Baik (Good)
70-80% = Cukup (Fair)
< 70% = Perlu Perbaikan

METRIK TAMBAHAN:
----------------
• Precision = TP / (TP + FP) × 100%
• Recall = TP / (TP + FN) × 100%
• F1-Score = 2 × (Precision × Recall) / (Precision + Recall)

================================================================================
STRUKTUR LAPORAN UNTUK SKRIPSI:
================================================================================

BAB IV - HASIL DAN PEMBAHASAN
------------------------------

4.1 Implementasi Sistem
   • Screenshot interface
   • Penjelasan fitur

4.2 Metodologi Pengujian
   • Metode yang digunakan
   • Protokol pengujian
   • Kondisi pengujian

4.3 Hasil Pengujian
   • Tabel hasil (gunakan tabel_analisis.txt)
   • Chart akurasi per gesture
   • Chart confusion metrics
   • Pie chart distribusi

4.4 Analisis Hasil
   • Interpretasi akurasi
   • Identifikasi gesture terbaik/terburuk
   • Analisis error (FP dan FN)
   • Faktor yang mempengaruhi

4.5 Pembahasan
   • Kelebihan sistem
   • Keterbatasan sistem
   • Solusi untuk peningkatan
   • Perbandingan dengan penelitian terkait

================================================================================
TIPS MENDAPATKAN AKURASI TINGGI:
================================================================================

1. PENCAHAYAAN
   ✓ Cahaya terang dan merata
   ✗ Backlight atau cahaya berkedip

2. LATAR BELAKANG
   ✓ Polos atau sederhana
   ✗ Kompleks atau ramai

3. POSISI
   ✓ Jarak 30-60 cm dari kamera
   ✗ Terlalu dekat atau jauh

4. GERAKAN
   ✓ Gerakan jelas dan konsisten
   ✗ Gerakan terlalu cepat atau ragu

5. KONFIRMASI
   ✓ Objektif dan jujur
   ✗ Bias atau terburu-buru

================================================================================
TROUBLESHOOTING:
================================================================================

MASALAH: Kamera tidak terdeteksi
SOLUSI: 
• Cek koneksi webcam
• Ubah cv2.VideoCapture(0) → VideoCapture(1)
• Cek permission kamera

MASALAH: Hand tracking tidak stabil
SOLUSI:
• Perbaiki pencahayaan
• Ubah detectionCon (0.3 → 0.5)
• Simplify latar belakang

MASALAH: Banyak False Positive
SOLUSI:
• Tingkatkan gesture_cooldown
• Adjust threshold jarak
• Tambah validasi gesture

MASALAH: Banyak False Negative
SOLUSI:
• Turunkan threshold deteksi
• Perbaiki pencahayaan
• Perlambat gerakan

MASALAH: Mouse terlalu sensitif
SOLUSI:
• Tambah smoothing
• Adjust screen mapping
• Turunkan resolusi kamera

================================================================================
REFERENSI & DOKUMENTASI:
================================================================================

LIBRARY YANG DIGUNAKAN:
------------------------
• OpenCV: https://opencv.org/
• CVZone: https://github.com/cvzone/cvzone
• MediaPipe: https://mediapipe.dev/
• PyNput: https://pynput.readthedocs.io/

PAPER & ARTIKEL TERKAIT:
------------------------
• Hand Tracking using MediaPipe
• Computer Vision for HCI
• Virtual Mouse Systems

================================================================================
KONTRIBUSI & PENGEMBANGAN:
================================================================================

FITUR YANG BISA DITAMBAHKAN:
----------------------------
• Klik kanan dan klik tengah
• Drag and drop
• Gesture custom
• Multi-hand support
• Voice command integration
• Kalibrasi otomatis

OPTIMISASI YANG BISA DILAKUKAN:
--------------------------------
• Smoothing pergerakan cursor
• Adaptive threshold
• Machine learning untuk gesture recognition
• Multi-threading untuk performa

================================================================================
LISENSI & KREDIT:
================================================================================

Project ini dibuat untuk keperluan Tugas Akhir (Skripsi)
Program Studi Teknologi Informasi
Universitas Teuku Umar

Boleh digunakan dan dimodifikasi untuk keperluan akademik
dengan menyertakan kredit kepada pembuat asli.

================================================================================
KONTAK:
================================================================================

Untuk pertanyaan atau bantuan terkait project ini,
silakan hubungi melalui:

Email: [email universitas]
GitHub: [jika ada]

================================================================================
CHANGELOG:
================================================================================

Version 1.0 (2025)
------------------
• Initial release
• Basic virtual mouse functionality
• Testing system implementation
• Analysis and visualization tools
• Complete documentation

================================================================================
                              SELAMAT MENGGUNAKAN!
                         SEMOGA SKRIPSI ANDA SUKSES!
================================================================================
