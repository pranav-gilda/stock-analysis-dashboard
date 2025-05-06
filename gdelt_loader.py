import boto3
import gzip
import io
import json
import os
from dotenv import load_dotenv
from mongo import insert_articles
import time

load_dotenv()

# Initialize S3 client
s3 = boto3.client("s3")

BATCH_SIZE = 500  # safe, small batches

def list_gz_files_for_day(bucket, date_str):
    prefix = f"{date_str}/"  
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".gz")]
    return sorted(files)

def read_gz_file_from_s3(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    gzipped_body = obj['Body']

    records = []
    with gzip.GzipFile(fileobj=gzipped_body, mode='rb') as gz:
        for line in gz:
            try:
                line = line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                data = json.loads(line)
                records.append(data)
            except json.JSONDecodeError as e:
                print(f"Skipping corrupted line in {key}: {e}")
    return records

def process_articles_for_day(bucket, date_str):
    keys = list_gz_files_for_day(bucket, date_str)

    total_inserted = 0
    total_duplicates = 0
    pending_batch = []

    for key in keys:
        print(f"Processing file: {key}")
        articles = read_gz_file_from_s3(bucket, key)
        if articles:
            pending_batch.extend(articles)

            if len(pending_batch) >= BATCH_SIZE:
                inserted, duplicates = insert_articles(pending_batch)
                total_inserted += inserted
                total_duplicates += duplicates
                pending_batch = []
                time.sleep(1)  # let Mongo breathe

    if pending_batch:
        inserted, duplicates = insert_articles(pending_batch)
        total_inserted += inserted
        total_duplicates += duplicates

    return total_inserted, total_duplicates
