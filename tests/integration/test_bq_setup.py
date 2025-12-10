#!/usr/bin/env python3
"""
Quick test script to create BigQuery dataset and load CSV data
"""

from google.cloud import bigquery
import os

def main():
    # Initialize BigQuery client
    client = bigquery.Client(project="hackathon-practice-480508")

    # Create dataset
    dataset_id = "hackathon-practice-480508.dev_dataset"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"

    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"✅ Dataset {dataset_id} created successfully!")
    except Exception as e:
        print(f"❌ Failed to create dataset: {e}")
        return

    # Load holdings CSV data
    csv_path = "fake_data/holdings_sample.csv"
    table_id = f"{dataset_id}.holdings"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # Skip header row
        autodetect=True,
    )

    try:
        with open(csv_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)

        job.result()  # Wait for the job to complete
        print(f"✅ Holdings CSV loaded successfully into {table_id}!")

        # Load customers CSV data
        csv_path = "fake_data/customers_sample.csv"
        table_id = f"{dataset_id}.customers"

        with open(csv_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)

        job.result()  # Wait for the job to complete
        print(f"✅ Customers CSV loaded successfully into {table_id}!")

        # Test query on customers table
        query = f"SELECT * FROM `{table_id}` LIMIT 10"
        query_job = client.query(query)

        results = query_job.result()
        print("✅ Query test successful! Customers table data:")
        for row in results:
            print(dict(row))

    except Exception as e:
        print(f"❌ Failed to load CSV or run query: {e}")

if __name__ == "__main__":
    main()
