# Big Data Analytics: REES46

Tugas akhir Big Data Analytics. Datanya log event toko online REES46 (Oktober dan November 2019, sekitar 23 juta sesi). Di repo ini ada notebook untuk bersihin data, bikin fitur, deteksi anomali pakai K-Means, rekomendasi pakai ALS, dan analisis graph di Neo4j. Hasil akhirnya ditampilkan di dashboard Superset.

Beberapa tahap sengaja dikerjakan dua kali, satu pakai Spark dan satu lagi tanpa Spark, buat dibandingkan hasilnya.

Semua jalan lewat Docker, jadi tidak perlu install Spark, Neo4j, atau Superset di laptop.

## Isi repo

```
.
├── docker-compose.yml       Jupyter dan Neo4j
├── docker/                  Dockerfile Jupyter + PySpark 3.5.3
├── superset/                dashboard Superset (punya compose sendiri)
├── 01_csv_to_silver.ipynb
├── 02_feature_engineering.ipynb
├── 03a_anomaly_mllib.ipynb
├── 03b_anomaly_sklearn.ipynb
├── 04a_als_mllib.ipynb
├── 04b_als_implicit.ipynb
├── 05a_export_graph.ipynb
├── 05b_graph_analytics.ipynb
├── 05c_graph_refinement.ipynb
├── 05d_product_similarity.ipynb
└── 05e_fanout_check.ipynb
```

Folder `data/` dan `ml/outputs/` tidak ada di repo. Keduanya dibuat sendiri oleh notebook, kecuali CSV mentah yang harus ditaruh manual.

## Kebutuhan

- Docker dan Docker Compose
- RAM 16 GB untuk container Jupyter (batasnya ada di `docker-compose.yml`). Kalau Neo4j ikut nyala, butuh lebih banyak lagi karena heap-nya 10 GB dan page cache 6 GB
- Disk yang lega, soalnya ada Parquet, file sementara Spark, dan data Neo4j
- Dataset dari Kaggle, *eCommerce behavior data from multi category store*. Ambil `2019-Oct.csv` dan `2019-Nov.csv`

## Menjalankan notebook

### 1. Taruh CSV

Buat folder `data/` di root proyek, lalu isi dengan:

```
data/2019-Oct.csv
data/2019-Nov.csv
```

Folder proyek di-mount ke `/home/jovyan/work` di dalam container, jadi notebook membaca dari `/home/jovyan/work/data`.

### 2. Nyalakan JupyterLab

```bash
docker compose up -d --build
```

Build pertama lumayan lama karena harus mengunduh image Spark. Kalau sudah selesai:

- JupyterLab di http://localhost:8888 (token `bda2`)
- Spark UI di http://localhost:4040 (hanya hidup kalau ada job Spark yang jalan)

Token Jupyter dan password Neo4j bisa diganti lewat `JUPYTER_TOKEN` dan `NEO4J_PASSWORD`, misalnya di file `.env` di root proyek.

### 3. Jalankan notebook berurutan

Notebook saling bergantung, jadi urutannya jangan dibalik.

| Notebook | Isi | Output |
|---|---|---|
| `01_csv_to_silver` | Baca CSV dengan schema eksplisit, validasi, buang duplikat, simpan ke Parquet | `data/silver/events` |
| `02_feature_engineering` | Fitur per sesi dan matriks interaksi user-produk untuk ALS (split temporal di 2019-11-24) | `data/gold/session_features`, `als_train`, `als_test` |
| `03a_anomaly_mllib` | K-Means di Spark pada 22,99 juta sesi. Sesi dengan jarak terjauh ke centroid (0,5%) dianggap anomali | `ml/outputs/03a_metrics.json` |
| `03b_anomaly_sklearn` | K-Means yang sama pakai scikit-learn, plus Isolation Forest. Jalankan 03a dulu | `ml/outputs/03b_metrics.json` |
| `04a_als_mllib` | ALS implicit feedback di Spark, dengan baseline popularitas | Precision, Recall, NDCG, HitRate @10 |
| `04b_als_implicit` | Evaluasi yang sama pakai library `implicit` tanpa Spark | metrik untuk dibandingkan dengan 04a |
| `05a_export_graph` | Ekspor node dan relasi ke CSV untuk import Neo4j | `data/neo4j-import` |
| `05b_graph_analytics` | PageRank dan Louvain di Neo4j + GDS | analisis komunitas |
| `05c_graph_refinement` | Leiden pada graph cart/purchase supaya komunitasnya lebih kecil dan gampang dibaca | komunitas yang lebih halus |
| `05d_product_similarity` | Node Similarity antar produk, menggantikan bagian 6 di 05b | similarity produk |
| `05e_fanout_check` | Cek apakah user fan-out yang ditandai memang berbagi produk yang sama | `ml/outputs/05e_*.json` |

Seri 03 dan 04 tidak harus berurutan satu sama lain, tapi dua-duanya butuh output 02. Seri 05 butuh hasil 01 dan flag anomali dari 03a.

### 4. Neo4j untuk seri 05

Neo4j tidak ikut menyala di langkah 2 karena cuma dipakai di bagian graph. Setelah `05a` selesai menulis CSV, import dulu datanya ke database Neo4j (pakai `neo4j-admin database import`), lalu nyalakan servicenya:

```bash
docker compose --profile graph up -d neo4j
```

Neo4j Browser ada di http://localhost:7474 dan Bolt di port 7687. Plugin APOC dan Graph Data Science terpasang otomatis lewat compose. Login default `neo4j` / `neo4jpassword`.

Lanjut jalankan `05b` sampai `05e`. Graph-nya besar (sekitar 5,5 juta node dan 59,9 juta relasi), jadi ada beberapa sel yang makan waktu.

## Dashboard Superset

Dashboard ada di folder `superset/` dan jalan terpisah dari Jupyter. Isinya angka hasil akhir dari bab IV sampai VI yang dimasukkan ke PostgreSQL kecil, jadi tidak perlu menjalankan notebook dulu dan tidak perlu dataset mentah.

Stack-nya Apache Superset 4.1.2 dan PostgreSQL 16, masing-masing di container sendiri.

### Cara menjalankan

Masuk ke folder superset, lalu nyalakan containernya:

```bash
cd superset
docker compose up -d --build
```

Tunggu sampai Superset siap. Start pertama bisa makan beberapa menit karena image dibuild, migrasi database jalan, dan data seed dimuat. Progresnya bisa dilihat dengan:

```bash
docker compose logs -f superset
```

Kalau sudah muncul log server dan `docker compose ps` menunjukkan status `healthy`, buat chart dan dashboard-nya:

```bash
python3 scripts/build_dashboard.py
```

Script ini hanya memakai standard library Python 3, tidak perlu `pip install`. Ia memanggil REST API Superset untuk membuat koneksi database, dataset, 15 chart, dan dashboard, lalu menyimpan hasil export ke `exports/dashboard_export.zip`.

Setelah itu buka http://localhost:8088 dan login dengan `admin` / `admin`. Dashboard-nya bernama **Fraud Detection and Personalization Dashboard**, ada di menu Dashboards.

### Kalau mau import dari file export

Cara ini berguna kalau Superset-nya sudah jalan dan kamu tidak mau menjalankan script:

1. Buka Dashboards, klik tombol Import.
2. Pilih `superset/exports/dashboard_export.zip`.
3. Saat diminta password database, isi `superset`.

Instance tujuan harus punya PostgreSQL yang bisa dijangkau lewat URI di `databases/BDA_Final_Project.yaml` dalam zip tersebut.

### Mengubah data

Angka dashboard ada di `superset/db/seed.sql`. Tiap blok diberi komentar yang menyebut tabel asalnya di laporan. Kalau ada angka yang berubah di laporan, ubah juga di file ini. Seed hanya dibaca saat volume database masih kosong, jadi reset dulu lalu build ulang:

```bash
docker compose down -v
docker compose up -d --build
python3 scripts/build_dashboard.py
```

### Menghentikan

```bash
docker compose down
```

Tambahkan `-v` kalau volume database juga mau dihapus.

Username, password, dan secret key di folder ini hanya untuk lokal. Jangan dipakai di server yang bisa diakses dari luar.

## Menghentikan Jupyter dan Neo4j

Dari root proyek:

```bash
docker compose --profile graph down
```

Data Neo4j disimpan di volume `neo4j-data`, jadi tidak hilang setelah `down`. Pakai `-v` kalau memang mau dihapus.

## Kalau ada masalah

- **Kernel mati waktu menjalankan 03b atau 04b.** Pendekatan tanpa Spark memang bisa kehabisan memori di data penuh. Notebook 03b menjalankan data penuh di subprocess terpisah, jadi kegagalan OOM tercatat dan kernel tidak ikut mati.
- **Port 8888, 4040, 7474, 7687, atau 8088 sudah dipakai.** Ubah angka di sisi kiri pemetaan port di `docker-compose.yml` yang bersangkutan.
- **Neo4j tidak mau start.** Cek jatah RAM Docker Desktop. Heap 10 GB ditambah page cache 6 GB tidak akan muat kalau batasnya terlalu kecil.
- **`build_dashboard.py` gagal konek.** Superset belum siap. Tunggu sampai `docker compose ps` menunjukkan `healthy`, lalu jalankan lagi.
- **Dashboard kosong atau chart error.** Pastikan script `build_dashboard.py` sudah dijalankan, dan data seed sudah masuk. Kalau ragu, ulangi dari `docker compose down -v`.
