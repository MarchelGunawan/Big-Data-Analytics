FROM apache/superset:4.1.2

USER root
# the official image has no PostgreSQL driver
RUN pip install --no-cache-dir psycopg2-binary
USER superset
