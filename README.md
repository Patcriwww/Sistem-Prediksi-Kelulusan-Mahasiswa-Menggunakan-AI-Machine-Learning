# Prediksi Kelulusan Mahasiswa Menggunakan AI & Machine Learning

Aplikasi web berbasis **Flask** untuk memprediksi kemungkinan mahasiswa
lulus tepat waktu berdasarkan data akademik menggunakan model **Machine
Learning (Random Forest)**.\
Sistem ini menampilkan **status kelulusan**, **probabilitas**, serta
**rekomendasi akademik** untuk membantu pengambilan keputusan berbasis
data di lingkungan pendidikan.

------------------------------------------------------------------------

## Tujuan Proyek

-   Mendeteksi risiko keterlambatan kelulusan sejak dini\
-   Mendukung pengambilan keputusan akademik berbasis data\
-   Memberikan rekomendasi akademik yang konstruktif\
-   Menjadi contoh implementasi AI dalam sistem pendidikan

------------------------------------------------------------------------

## Fitur Utama

-   Prediksi status kelulusan (Lulus / Terlambat)\
-   Probabilitas kelulusan dalam persentase\
-   Rekomendasi langkah akademik\
-   Ringkasan data input mahasiswa\
-   Antarmuka web modern dan responsif

------------------------------------------------------------------------

## Teknologi yang Digunakan

-   Python\
-   Flask\
-   Pandas\
-   Scikit-learn\
-   PostgreSQL\
-   HTML, CSS, Jinja2

------------------------------------------------------------------------

## Variabel Input Model

  Variabel                Deskripsi
  ----------------------- -----------------------------------
  IPK                     Indeks Prestasi Kumulatif
  SKS Lulus               Total SKS yang telah diselesaikan
  Presensi (%)            Persentase kehadiran kuliah
  Mata Kuliah Mengulang   Jumlah mata kuliah yang diulang

------------------------------------------------------------------------

## Cara Menjalankan Aplikasi

### 1. Clone Repository

``` bash
git clone https://github.com/USERNAME/prediksi-kelulusan-mahasiswa.git
cd prediksi-kelulusan-mahasiswa
```

### 2. Install Dependencies

``` bash
pip install -r requirements.txt
```

### 3. Setup Database (PostgreSQL)

-   Buat database:

``` sql
CREATE DATABASE db_prediksi_kelulusan;
```

-   Set environment variable `DATABASE_URL`:

``` bash
postgresql://postgres:password@host:5432/db_prediksi_kelulusan
```

-   Seed data awal:

``` bash
python scripts/seed_db.py
```

### 4. Jalankan Aplikasi

``` bash
python app.py
```

### 5. Akses di Browser

``` text
http://127.0.0.1:5000/
```

------------------------------------------------------------------------

## Struktur Project

``` bash
prediksi-kelulusan-mahasiswa/
│
├── app.py
├── requirements.txt
├── README.md
├── scripts/
│   └── seed_db.py
└── templates/
    └── index.html
```

------------------------------------------------------------------------

## Tag

`#ai-for-education` `#machine-learning` `#flask` `#data-science`
`#academic-analytics`
