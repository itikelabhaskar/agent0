# agent/tools.py
from google.cloud import bigquery
import pandas as pd

def run_bq_query(project, sql):
    client = bigquery.Client(project=project)
    job = client.query(sql)
    return job.to_dataframe()

def detect_missing_dob(project, dataset, table, limit=100):
    sql = f"SELECT customer_id, customer_name, email, status FROM `{project}.{dataset}.{table}` WHERE date_of_birth IS NULL LIMIT {limit}"
    return run_bq_query(project, sql).to_dict(orient='records')

# local CSV fallback
def read_local_csv(path):
    return pd.read_csv(path).to_dict(orient='records')


def run_bq_nonquery(project, sql):
    """
    Execute non-query BigQuery operations (INSERT, UPDATE, DELETE, DDL)
    """
    client = bigquery.Client(project=project)
    job = client.query(sql)
    job.result()  # wait for completion
    return True
