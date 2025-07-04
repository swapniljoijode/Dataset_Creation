# bigquery_loader.py
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

def ensure_bq_dataset(key:str, pid:str, did: str, location: str = "US"):
    """
    Create the dataset if it doesn't already exist.
    """
    client = bigquery.Client.from_service_account_json(key, project=pid)
    # Create dataset if needed
    dataset_ref = f"{pid}.{did}"
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        client.create_dataset(dataset_ref)


def upload_all_to_bq(grade_df, students_df, academic_df, grads_df, term_df,
                     project_id, dataset_id, key):
    client = bigquery.Client.from_service_account_json(key, project=project_id)

    # 1) ensure dataset
    ensure_bq_dataset(key=key,pid=project_id, did=dataset_id)

    # 2) upload each table (truncating any existing)
    def _upload(df, table_name):
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        job = client.load_table_from_dataframe(
            df,
            table_ref,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        job.result()
        print(f"Uploaded {len(df)} rows to {table_ref}")

    _upload(grade_df,    "grades")
    _upload(students_df, "students")
    _upload(academic_df, "academic")
    _upload(grads_df,    "graduates")
    _upload(term_df,     "terminated")
