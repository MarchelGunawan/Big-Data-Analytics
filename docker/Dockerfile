FROM quay.io/jupyter/pyspark-notebook:spark-3.5.3

ENV PYTHONPATH=/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip

RUN pip install --no-cache-dir \
    scikit-learn pandas pyarrow matplotlib seaborn \
    implicit scipy neo4j
