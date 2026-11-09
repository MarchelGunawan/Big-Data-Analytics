# Superset dashboard

Dashboard for Chapter VII of the Big Data Analytics final project (fraud detection and personalization in e-commerce). It runs Apache Superset 4.1.2 on top of a small PostgreSQL database that holds the aggregated results of the earlier chapters.

## Layout

```
superset/
├── config/superset_config.py   Superset settings
├── db/seed.sql                 creates and fills the "bda" database
├── scripts/build_dashboard.py  creates the charts and dashboard via the REST API
├── exports/                    dashboard export (YAML in a zip)
├── Dockerfile                  Superset image plus the PostgreSQL driver
└── docker-compose.yml          Superset and PostgreSQL
```

## Running it

You need Docker. From this folder:

```bash
docker compose up -d --build
python3 scripts/build_dashboard.py
```

The first start takes a few minutes while the image builds and the seed data loads. Then open http://localhost:8088 and log in with `admin` / `admin`. The dashboard is called "Fraud Detection and Personalization Dashboard".

To stop, run `docker compose down`. Add `-v` to also delete the database volume.

## Data

`db/seed.sql` holds the numbers reported in Chapters IV to VI, not the raw events. Each block has a comment with the table it comes from in the report. If a figure changes in the report, change it here too and rebuild the dashboard.

## Importing the export

`exports/dashboard_export.zip` contains the dashboard, 15 charts, 10 datasets and the database connection. To load it into another Superset instance, go to Dashboards, click Import, pick the zip and enter the database password (`superset`) when asked. That instance needs a PostgreSQL database reachable at the URI in `databases/BDA_Final_Project.yaml`.

To export again after editing in the UI, hover over the dashboard row and choose Actions, then Export.

## Notes

The credentials and secret key in this repo are for local use only. Do not reuse them on anything exposed to a network.
