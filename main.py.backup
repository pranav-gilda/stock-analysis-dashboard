from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, date
import logging
from bson import ObjectId
import pytz
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Stock Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Default date range
DEFAULT_START_DATE = "2024-01-01"
DEFAULT_END_DATE = "2024-06-12"

# MongoDB connections
try:
    # First cluster (Jan-Feb)
    client1 = MongoClient(os.getenv("MONGO_ATLAS_URI_1"))
    db1 = client1["stock_analysis"]
    articles1 = db1["articles"]
    logger.info("Successfully connected to first MongoDB cluster")
    
    # Second cluster (Mar-Apr)
    client2 = MongoClient(os.getenv("MONGO_ATLAS_URI_2"))
    db2 = client2["stock_analysis"]
    articles2 = db2["articles"]
    logger.info("Successfully connected to second MongoDB cluster")
    
    # Third cluster (Apr27 onwards)
    client3 = MongoClient(os.getenv("MONGO_ATLAS_URI_3"))
    db3 = client3["stock_analysis"]
    articles3 = db3["articles"]
    logger.info("Successfully connected to third MongoDB cluster")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")
    raise

# Load and cache the CSV data
try:
    df = pd.read_csv('combined_analysis_jan_june_2024.csv')
    df['date'] = pd.to_datetime(df['date'])
    logger.info("Successfully loaded CSV data")
except Exception as e:
    logger.error(f"Error loading CSV data: {str(e)}")
    raise

# Pydantic models for request/response
class OHLCVData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class SentimentData(BaseModel):
    date: str
    avg_sentiment: float
    article_count: int

class CompanyData(BaseModel):
    company: str
    symbol: str
    data: List[OHLCVData]

class HeatmapData(BaseModel):
    date: str
    company: str
    avg_sentiment: float
    article_count: int

class TimeRange(BaseModel):
    start_date: str
    end_date: str

# Helper function to get appropriate collection based on date
def get_collection_for_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    if date_obj >= datetime(2024, 4, 27):
        return articles3
    elif date_obj >= datetime(2024, 3, 2):
        return articles2
    return articles1

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to Stock Analysis API"}

@app.get("/companies")
async def get_companies():
    """Get list of available companies"""
    companies = df[['company', 'symbol']].drop_duplicates().to_dict('records')
    return {"companies": companies}

@app.get("/time-range")
async def get_time_range():
    """Get available date range"""
    return {
        "start_date": df['date'].min().strftime('%Y-%m-%d'),
        "end_date": df['date'].max().strftime('%Y-%m-%d'),
        "default_start_date": DEFAULT_START_DATE,
        "default_end_date": DEFAULT_END_DATE
    }

@app.get("/ohlcv/{symbol}")
async def get_ohlcv_data(
    symbol: str,
    start_date: str = Query(DEFAULT_START_DATE, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(DEFAULT_END_DATE, description="End date in YYYY-MM-DD format")
):
    """Get OHLCV data for a specific company"""
    mask = (df['symbol'] == symbol) & (df['date'] >= start_date) & (df['date'] <= end_date)
    data = df[mask].sort_values('date')
    
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol} in the specified date range")
    
    return {
        "company": data['company'].iloc[0],
        "symbol": symbol,
        "data": data[['date', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
    }

@app.get("/sentiment/{symbol}")
async def get_sentiment_data(
    symbol: str,
    start_date: str = Query(DEFAULT_START_DATE, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(DEFAULT_END_DATE, description="End date in YYYY-MM-DD format")
):
    """Get sentiment data for a specific company"""
    mask = (df['symbol'] == symbol) & (df['date'] >= start_date) & (df['date'] <= end_date)
    data = df[mask].sort_values('date')
    
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol} in the specified date range")
    
    return {
        "company": data['company'].iloc[0],
        "symbol": symbol,
        "data": data[['date', 'avg_sentiment', 'article_count']].to_dict('records')
    }

@app.get("/heatmap")
async def get_heatmap_data(
    start_date: str = Query(DEFAULT_START_DATE, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(DEFAULT_END_DATE, description="End date in YYYY-MM-DD format")
):
    """Get heatmap data for all companies"""
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    data = df[mask].sort_values(['date', 'company'])
    
    if data.empty:
        raise HTTPException(status_code=404, detail="No data found in the specified date range")
    
    return {
        "data": data[['date', 'company', 'avg_sentiment', 'article_count']].to_dict('records')
    }

@app.get("/daily-stats")
async def get_daily_stats(
    start_date: str = Query(DEFAULT_START_DATE, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(DEFAULT_END_DATE, description="End date in YYYY-MM-DD format")
):
    """Get daily statistics across all companies"""
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    daily_stats = df[mask].groupby('date').agg({
        'article_count': 'sum',
        'avg_sentiment': 'mean'
    }).reset_index()
    
    return {
        "data": daily_stats.to_dict('records')
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 