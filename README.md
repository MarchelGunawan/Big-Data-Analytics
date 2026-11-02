# Big Data Analytics: Pipeline ML dan Graph pada Dataset REES46

Kumpulan notebook untuk memproses log event e-commerce REES46 (Oktober dan November 2019, sekitar 23 juta sesi). Isinya mencakup pembersihan data, feature engineering, deteksi anomali dengan K-Means, sistem rekomendasi dengan ALS, dan analisis graph di Neo4j. Beberapa tahap dijalankan dua kali, dengan Spark dan tanpa Spark, supaya hasilnya bisa dibandingkan.

Semuanya jalan di Docker, jadi kamu tidak perlu install Spark atau Neo4j sendiri.

## Yang perlu disiapkan

- Docker dan Docker Compose.
- RAM minimal 16 GB untuk container Jupyter (batasnya diatur di `docker-compose.yml`). Kalau kamu ikut menjalankan Neo4j, siapkan lebih banyak lagi, karena heap-nya diset 10 GB dan page cache 6 GB.
- Ruang disk yang lega untuk Parquet, file sementara Spark, dan data Neo4j.
- Dataset REES46 dari Kaggle (*eCommerce behavior data from multi category store*): `2019-Oct.csv` dan `2019-Nov.csv`.

## Struktur folder

```
.
├── docker-compose.yml
├── docker/Dockerfile        # image Jupyter + PySpark 3.5.3
├── docker/render/           # image LibreOffice untuk render dokumen laporan
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

Folder `data/` dan `ml/outputs/` tidak ikut di repo. Notebook membuatnya sendiri saat dijalankan (kecuali CSV mentah, yang harus kamu taruh sendiri).

## Langkah menjalankan

### 1. Taruh CSV mentah

Buat folder `data/` di root proyek, lalu letakkan dua file ini di dalamnya:

```
data/2019-Oct.csv
data/2019-Nov.csv
```

Folder proyek di-mount ke `/home/jovyan/work` di dalam container, jadi notebook membacanya dari `/home/jovyan/work/data`.

### 2. Jalankan JupyterLab

```bash
docker compose up -d --build
```

Build pertama agak lama karena mengunduh image Spark. Setelah selesai, buka:

- JupyterLab: http://localhost:8888 (token default `bda2`)
- Spark UI: http://localhost:4040 (hanya aktif saat ada job Spark yang berjalan)

Token dan password Neo4j bisa diganti lewat environment variable `JUPYTER_TOKEN` dan `NEO4J_PASSWORD`, misalnya dengan file `.env` di root proyek.

### 3. Jalankan notebook secara berurutan

Notebook saling bergantung, jadi urutannya penting.

| Notebook | Isi | Hasil |
|---|---|---|
| `01_csv_to_silver` | Baca CSV dengan schema eksplisit, validasi, buang duplikat, tulis Parquet | `data/silver/events` |
| `02_feature_engineering` | Fitur per sesi, plus matriks interaksi user-produk untuk ALS (split temporal di 2019-11-24) | `data/gold/session_features`, `als_train`, `als_test` |
| `03a_anomaly_mllib` | K-Means di Spark pada 22,99 juta sesi. Sesi dengan jarak terjauh ke centroid (0,5%) ditandai anomali | `ml/outputs/03a_metrics.json` |
| `03b_anomaly_sklearn` | K-Means yang sama dengan scikit-learn, ditambah Isolation Forest. **Jalankan 03a dulu** | `ml/outputs/03b_metrics.json` |
| `04a_als_mllib` | ALS implicit feedback di Spark, dengan baseline popularitas | metrik Precision, Recall, NDCG, HitRate @10 |
| `04b_als_implicit` | Protokol evaluasi yang sama dengan library `implicit` tanpa Spark | metrik dibandingkan dengan 04a |
| `05a_export_graph` | Ekspor node dan relasi ke CSV untuk bulk import Neo4j | `data/neo4j-import` |
| `05b_graph_analytics` | PageRank dan Louvain di Neo4j + GDS | analisis komunitas |
| `05c_graph_refinement` | Leiden pada graph cart/purchase, supaya komunitasnya lebih kecil dan mudah dibaca | komunitas yang lebih halus |
| `05d_product_similarity` | Node Similarity antar produk. Menggantikan bagian 6 di 05b | similarity produk |
| `05e_fanout_check` | Cek apakah user fan-out yang ditandai berbagi produk yang sama | `ml/outputs/05e_*.json` |

Urutan 03 dan 04 tidak saling mengikat, tapi dua-duanya butuh output 02. Seri 05 butuh hasil 01 dan flag anomali dari 03a.

### 4. Siapkan Neo4j untuk seri 05

Neo4j sengaja tidak ikut jalan di langkah 2, karena hanya dipakai di bagian graph. Setelah `05a` selesai menulis CSV, import dulu ke database Neo4j (format `neo4j-admin database import`), lalu nyalakan servicenya:

```bash
docker compose --profile graph up -d neo4j
```

Browser Neo4j ada di http://localhost:7474, dan koneksi Bolt di port 7687. Plugin APOC dan Graph Data Science dipasang otomatis lewat konfigurasi compose. Kredensial default-nya `neo4j` / `neo4jpassword`.

Setelah itu jalankan `05b` sampai `05e`. Graph-nya besar (sekitar 5,5 juta node dan 59,9 juta relasi), jadi beberapa sel butuh waktu.

## Menghentikan environment

```bash
docker compose --profile graph down
```

Data Neo4j disimpan di volume `neo4j-data`, jadi tidak hilang setelah `down`. Tambahkan `-v` kalau memang mau menghapusnya.

## Troubleshooting

- **Kernel mati saat menjalankan 03b atau 04b.** Pendekatan tanpa Spark memang bisa kehabisan memori di data penuh. Notebook 03b menjalankan data penuh di subprocess terpisah supaya kegagalan OOM tercatat, bukan membuat kernel crash.
- **Port 8888, 4040, 7474, atau 7687 sudah terpakai.** Ubah sisi kiri pemetaan port di `docker-compose.yml`.
- **Neo4j tidak mau start.** Cek RAM yang dialokasikan ke Docker Desktop. Heap 10 GB ditambah page cache 6 GB tidak muat kalau batasnya terlalu kecil.
