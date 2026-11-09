-- Aggregated results from Chapters IV to VI of the report.
-- The comment above each block gives the source table in the report.
CREATE DATABASE bda;
\connect bda

-- Table 5.1
CREATE TABLE event_funnel (event_type text, step_order int, events bigint);
INSERT INTO event_funnel VALUES ('view',1,104079641),('cart',2,3823980),('purchase',3,1659703);

-- Table 5.8 (k = 6)
CREATE TABLE session_segments (cluster_id int, segment text, sessions bigint, share_pct numeric, avg_events numeric, avg_products numeric);
INSERT INTO session_segments VALUES
 (0,'0 Few events, long gaps',8585143,37.3,3.6,2.4),
 (1,'1 Single-event sessions',8464480,36.8,1.0,1.0),
 (2,'2 Short cart sessions',1093958,4.8,6.0,2.1),
 (3,'3 Purchase without view',7009,0.03,1.6,1.0),
 (4,'4 Cart and purchase',1377224,6.0,7.7,2.8),
 (5,'5 Broad browsing',3467862,15.1,15.2,9.8);

-- Table 5.9
CREATE TABLE flag_groups (grp text, sessions bigint, avg_events numeric, avg_products numeric, events_per_min numeric, cart_per_view numeric, purchase_per_view numeric);
INSERT INTO flag_groups VALUES
 ('Not flagged',22873026,4.6,3.0,23.4,0.05,0.03),
 ('Distance only',115641,34.0,16.4,2.0,1.18,0.28),
 ('Small cluster only',6777,1.5,1.0,36.8,0.44,1.02),
 ('Both',232,4.9,1.1,1.6,3.62,1.29);

-- Tables 5.10 and 5.11
CREATE TABLE reco_quality (model text, metric text, value numeric);
INSERT INTO reco_quality VALUES
 ('Popularity','Precision@10',0.0154),('Popularity','Recall@10',0.1098),('Popularity','NDCG@10',0.0644),('Popularity','Hit rate@10',0.1401),
 ('ALS (Spark)','Precision@10',0.0195),('ALS (Spark)','Recall@10',0.1465),('ALS (Spark)','NDCG@10',0.0893),('ALS (Spark)','Hit rate@10',0.1796),
 ('ALS (implicit)','Precision@10',0.0197),('ALS (implicit)','Recall@10',0.1481),('ALS (implicit)','NDCG@10',0.0900),('ALS (implicit)','Hit rate@10',0.1812);

CREATE TABLE reco_ndcg_by_share (user_share_pct int, model text, ndcg_at_10 numeric);
INSERT INTO reco_ndcg_by_share VALUES
 (2,'Popularity',0.0641),(2,'ALS (Spark)',0.0918),(2,'ALS (implicit)',0.0888),
 (10,'Popularity',0.0642),(10,'ALS (Spark)',0.0907),(10,'ALS (implicit)',0.0898),
 (25,'Popularity',0.0650),(25,'ALS (Spark)',0.0908),(25,'ALS (implicit)',0.0915),
 (100,'Popularity',0.0644),(100,'ALS (Spark)',0.0893),(100,'ALS (implicit)',0.0900);

-- Tables 6.3 and 6.5 (baseline row = all users, 101,532 of 5,315,274 flagged)
CREATE TABLE community_enrichment (community text, users bigint, flagged bigint, flagged_rate_pct numeric, lift numeric);
INSERT INTO community_enrichment VALUES
 ('Community 5185',1771,424,23.9,2.93),('Community 4727',268,60,22.4,2.74),
 ('Community 4561',210,46,21.9,2.68),('Community 6225',344,74,21.5,2.64),
 ('All users (baseline)',5315274,101532,1.9,1.00);

CREATE TABLE pagerank_top10 (rank int, product_id bigint, brand text, category text);
INSERT INTO pagerank_top10 VALUES
 (1,1004856,'samsung','electronics.smartphone'),(2,1004767,'samsung','electronics.smartphone'),
 (3,1005115,'apple','electronics.smartphone'),(4,1005105,'apple','electronics.smartphone'),
 (5,1002544,'apple','electronics.smartphone'),(6,1004833,'samsung','electronics.smartphone'),
 (7,1004870,'samsung','electronics.smartphone'),(8,1004249,'apple','electronics.smartphone'),
 (9,4804056,'apple','electronics.audio.headphone'),(10,1004836,'samsung','electronics.smartphone');

-- Tables 5.5 and 5.6
CREATE TABLE fit_time_kmeans (sessions_label text, sessions bigint, sessions_m numeric, engine text, seconds numeric);
INSERT INTO fit_time_kmeans VALUES
 ('100K',100000,0.1,'Spark MLlib',1.3),('100K',100000,0.1,'scikit-learn',0.1),
 ('500K',500000,0.5,'Spark MLlib',5.1),('500K',500000,0.5,'scikit-learn',0.2),
 ('1M',1000000,1.0,'Spark MLlib',9.9),('1M',1000000,1.0,'scikit-learn',0.4),
 ('2M',2000000,2.0,'Spark MLlib',19.8),('2M',2000000,2.0,'scikit-learn',0.6),
 ('5M',5000000,5.0,'Spark MLlib',21.9),('5M',5000000,5.0,'scikit-learn',1.2),
 ('23M (full)',22995676,23.0,'Spark MLlib',50.3),('23M (full)',22995676,23.0,'scikit-learn',4.4);

CREATE TABLE fit_time_als (user_share_pct int, engine text, seconds numeric);
INSERT INTO fit_time_als VALUES
 (2,'Spark MLlib',7.6),(2,'implicit',4.7),(10,'Spark MLlib',15.6),(10,'implicit',15.0),
 (25,'Spark MLlib',32.0),(25,'implicit',32.9),(100,'Spark MLlib',149.8),(100,'implicit',126.5);

-- Headline numbers (Tables 5.1, 5.9, 6.1)
CREATE TABLE kpis (kpi text, value numeric, note text);
INSERT INTO kpis VALUES
 ('Raw events',109950743,'Table 5.1'),('Distinct users',5315274,'Table 5.1'),('Sessions',22995676,'Table 5.1'),
 ('Flagged sessions',122650,'0.53% of sessions'),('Flagged users',101532,'1.9% of users');
