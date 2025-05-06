from datetime import datetime, timedelta
from pymongo import MongoClient
import time
import os
from dotenv import load_dotenv
from gdelt_loader import process_articles_for_day

# Load environment variables
load_dotenv()

# MongoDB cluster configurations
CLUSTERS = {
    "cluster1": {
        "uri": os.getenv("MONGO_ATLAS_URI_1"),
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-03-01T23:59:59Z"
    },
    "cluster2": {
        "uri": os.getenv("MONGO_ATLAS_URI_2"),
        "start_date": "2024-03-02T00:00:00Z",
        "end_date": "2024-04-26T23:59:59Z"
    },
    "cluster3": {
        "uri": os.getenv("MONGO_ATLAS_URI_3"),
        "start_date": "2024-04-27T00:00:00Z",
        "end_date": "2024-06-30T23:59:59Z"
    }
}

def get_client_for_date(date_obj):
    """Get the appropriate MongoDB client based on the date"""
    for cluster_name, cluster in CLUSTERS.items():
        start_date = datetime.strptime(cluster["start_date"], "%Y-%m-%dT%H:%M:%SZ")
        end_date = datetime.strptime(cluster["end_date"], "%Y-%m-%dT%H:%M:%SZ")
        
        if start_date <= date_obj <= end_date:
            return MongoClient(cluster["uri"])
    
    # Default to first cluster if date is outside ranges
    return MongoClient(CLUSTERS["cluster1"]["uri"])

def check_storage_limit(date_obj):
    """Check storage limit for the appropriate cluster based on date"""
    client = get_client_for_date(date_obj)
    db = client["gdelt_news"]
    stats = db.command("dbstats")
    storage_mb = stats["storageSize"] / (1024 * 1024)
    client.close()
    return storage_mb

def load_articles_for_date_range(bucket, start_date, end_date):
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime("%Y%m%d")
        print(f"\n🚀 Processing {date_str}...")
        day_start_time = time.time()

        inserted, duplicates = process_articles_for_day(bucket, date_str)

        day_end_time = time.time()
        elapsed_time = round((day_end_time - day_start_time) / 60, 2)

        print(f"✅ Finished {date_str}: Inserted {inserted} articles, Skipped {duplicates} duplicates, Time taken: {elapsed_time} minutes")

        # Write to ETL log file
        with open("etl_log.txt", "a") as log_file:
            log_file.write(f"{date_str}: Inserted={inserted}, Duplicates={duplicates}, Time={elapsed_time} min\n")

        # Check MongoDB space for the appropriate cluster
        storage_mb = check_storage_limit(current_date)
        print(f"📦 Current MongoDB storage used: {round(storage_mb, 2)} MB")

        if storage_mb > 490:
            print("\n🛑 WARNING: Approaching 512MB limit. Stopping ETL safely!")
            break

        current_date += timedelta(days=1)

if __name__ == "__main__":
    bucket = "gdelt-peace-speech"
    start = datetime.strptime("20240111", "%Y%m%d")
    end = datetime.strptime("20241031", "%Y%m%d")

    load_articles_for_date_range(bucket, start, end)
