Prediksi Kelulusan Mahasiswa Menggunakan AI & Machine Learning

Aplikasi web berbasis Flask untuk memprediksi kemungkinan mahasiswa lulus tepat waktu berdasarkan data akademik sederhana menggunakan model Machine Learning (Random Forest).
Sistem juga memberikan probabilitas kelulusan dan rekomendasi tindakan akademik.

🎯 Tujuan Proyek

Mendeteksi risiko mahasiswa terlambat lulus lebih awal

Membantu pengambilan keputusan akademik secara data-driven

Memberikan rekomendasi akademik yang konstruktif

Contoh implementasi AI pada sistem pendidikan

🧠 Fitur Utama

Prediksi status kelulusan (Lulus / Terlambat)

Probabilitas kelulusan (%)

Rekomendasi langkah akademik

Ringkasan input data

UI modern & responsif

🛠 Teknologi yang Digunakan

Python

Flask

Pandas

Scikit-learn

HTML, CSS, Jinja2 Template

📥 Input Data Model
Variabel Deskripsi
IPK Indeks Prestasi Kumulatif
SKS Lulus Total SKS yang telah diselesaikan
Presensi (%) Persentase kehadiran kuliah
Mata Kuliah Mengulang Jumlah mata kuliah yang diulang
🚀 Cara Menjalankan Aplikasi
1️⃣ Clone Repository
git clone https://github.com/USERNAME/prediksi-kelulusan-mahasiswa.git
cd prediksi-kelulusan-mahasiswa

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Database (PostgreSQL)

- Buat database: `db_prediksi_kelulusan` di server PostgreSQL Anda.
- Set environment variable `DATABASE_URL` dengan connection string PostgreSQL Anda, misal:

  `postgresql://postgres:postgres@db.ltrpqqaagkhzqfatyvir.supabase.co:5432/db_prediksi_kelulusan`

- Seed data awal (user & student):
  `python scripts/seed_db.py`

4️⃣ Jalankan Aplikasi
python app.py

5️⃣ Buka di browser
http://127.0.0.1:5000/

📁 Struktur Project
├── app.py
├── requirements.txt
├── README.md
└── templates/
└── index.html

# ai-for-education
