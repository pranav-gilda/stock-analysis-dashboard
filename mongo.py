from pymongo import MongoClient
import hashlib
from dotenv import load_dotenv
import os
import time
from pymongo.errors import ServerSelectionTimeoutError, BulkWriteError
from datetime import datetime

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

# Keywords to match
KEYWORDS = ["tesla", "apple", "google", "nvidia", "microsoft"]

def get_client_for_date(date_str):
    """Get the appropriate MongoDB client based on the date"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    
    for cluster_name, cluster in CLUSTERS.items():
        start_date = datetime.strptime(cluster["start_date"], "%Y-%m-%dT%H:%M:%SZ")
        end_date = datetime.strptime(cluster["end_date"], "%Y-%m-%dT%H:%M:%SZ")
        
        if start_date <= date_obj <= end_date:
            return MongoClient(cluster["uri"])
    
    # Default to first cluster if date is outside ranges
    return MongoClient(CLUSTERS["cluster1"]["uri"])

def insert_articles(articles):
    global collection  # ✅ Declare once here if we are going to refresh it inside

    documents = []
    inserted_count = 0
    duplicate_count = 0

    # Prepare documents
    for article in articles:
        if article.get("lang") != "ENGLISH":
            continue

        title = article.get("title", "").lower()
        url = article.get("url", "").lower()

        if not any(keyword in title or keyword in url for keyword in KEYWORDS):
            continue

        url_or_title = article.get("url") or article.get("title") or str(article)
        _id = hashlib.md5(url_or_title.encode('utf-8')).hexdigest()

        doc = {
            "_id": _id,
            "date": article.get("date"),
            "title": article.get("title"),
            "url": article.get("url"),
            "lang": article.get("lang"),
            "docembed": article.get("docembed", []),
        }
        documents.append(doc)

    if documents:
        retries = 3
        while retries > 0:
            try:
                # Get the appropriate client based on the first article's date
                client = get_client_for_date(documents[0]["date"])
                db = client["gdelt_news"]
                collection = db["articles"]
                
                result = collection.insert_many(documents, ordered=False)
                inserted_count = len(result.inserted_ids)
                break  # success
            except ServerSelectionTimeoutError:
                print(f"⚠️ Connection Timeout. Refreshing Mongo Client and Retrying in 5 seconds... ({retries-1} retries left)")
                time.sleep(5)
                retries -= 1
            except BulkWriteError as bwe:
                inserted_count = bwe.details['nInserted']
                duplicate_count = len(bwe.details['writeErrors'])
                break  # partial insert ok

        if retries == 0:
            print("❌ All retries failed. Skipping current batch to continue ETL...")

    return inserted_count, duplicate_count

