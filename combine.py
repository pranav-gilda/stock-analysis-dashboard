from pymongo import MongoClient
import os
from pprint import pprint
from datetime import datetime
import numpy as np
from collections import Counter, defaultdict
import pandas as pd
from textblob import TextBlob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
KEYWORDS = ["tesla", "apple", "google", "nvidia", "microsoft"]

# MongoDB clusters
CLUSTERS = [
    {
        "uri": os.getenv("MONGO_ATLAS_URI_1"),
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-03-01T23:59:59Z"
    },
    {
        "uri": os.getenv("MONGO_ATLAS_URI_2"),
        "start_date": "2024-03-02T00:00:00Z",
        "end_date": "2024-04-26T23:59:59Z"
    },
    {
        "uri": os.getenv("MONGO_ATLAS_URI_3"),
        "start_date": "2024-04-27T00:00:00Z",
        "end_date": "2024-06-30T23:59:59Z"
    }
]

# def connect_to_db(uri):
#     client = MongoClient(uri)
#     return client["gdelt_news"]["articles"]

def connect_to_db(uri):
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10_000,
        connectTimeoutMS=10_000,
        socketTimeoutMS=60_000,
    )
    # verify the connection early
    client.admin.command("ping")
    return client["gdelt_news"]["articles"]

# def get_company_articles(collection, start_date, end_date):
#     """Get articles for each company in the specified date range"""
#     company_articles = defaultdict(list)
    
#     base_query = {
#         "date": {
#             "$gte": start_date,
#             "$lte": end_date
#         }
#     }
    
#     for company in KEYWORDS:
#         query = {
#             "$and": [
#                 base_query,
#                 {"$or": [
#                     {"title": {"$regex": company, "$options": "i"}},
#                     {"url": {"$regex": company, "$options": "i"}}
#                 ]}
#             ]
#         }
#         articles = list(collection.find(query))
#         company_articles[company] = articles
#         print(f"Found {len(articles)} articles for {company}")
    
#     return company_articles

def get_company_articles(collection, start_date, end_date):
    company_articles = defaultdict(list)
    base_query = {
        "date": {"$gte": start_date, "$lte": end_date}
    }

    for company in KEYWORDS:
        q = {
            **base_query,
            "$or": [
                {"title": {"$regex": company, "$options": "i"}},
                {"url":   {"$regex": company, "$options": "i"}}
            ]
        }

        cursor = (collection
                  .find(q, {"_id":1, "date":1, "title":1})
                  .batch_size(1000))
        
        count = 0
        for doc in cursor:
            company_articles[company].append(doc)
            count += 1

        print(f"Found {count} articles for {company}")

    return company_articles


def analyze_sentiment(title):
    """Analyze sentiment of article title"""
    analysis = TextBlob(title)
    return analysis.sentiment.polarity

def create_daily_aggregates(company_articles, start_date, end_date):
    """Create a DataFrame with daily aggregates for each company"""
    # Convert string dates to datetime
    start_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ")
    
    # Create date range
    date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
    
    # Initialize DataFrame
    daily_data = []
    
    for company in company_articles:
        daily_counts = defaultdict(int)
        daily_sentiments = defaultdict(list)
        
        for article in company_articles[company]:
            article_date = datetime.strptime(article['date'], "%Y-%m-%dT%H:%M:%SZ").date()
            daily_counts[article_date] += 1
            sentiment = analyze_sentiment(article['title'])
            daily_sentiments[article_date].append(sentiment)
        
        # Calculate aggregates for each day
        for date in date_range:
            date_obj = date.date()
            count = daily_counts[date_obj]
            avg_sentiment = np.mean(daily_sentiments[date_obj]) if daily_sentiments[date_obj] else 0
            
            daily_data.append({
                'date': date_obj,
                'company': company,
                'article_count': count,
                'avg_sentiment': avg_sentiment
            })
    
    # Create DataFrame
    df = pd.DataFrame(daily_data)
    
    # Sort by date and company
    df = df.sort_values(['date', 'company'])
    
    return df

def merge_with_stock_prices(articles_df, stock_prices_path):
    """Merge article data with stock prices, handling missing values intelligently"""
    # Read stock prices
    stock_df = pd.read_csv(stock_prices_path)
    
    # Convert date columns to datetime
    stock_df['Date'] = pd.to_datetime(stock_df['Date']).dt.date
    articles_df['date'] = pd.to_datetime(articles_df['date']).dt.date
    
    # Create a mapping of company names to stock symbols
    company_to_symbol = {
        'tesla': 'TSLA',
        'apple': 'AAPL',
        'google': 'GOOGL',
        'nvidia': 'NVDA',
        'microsoft': 'MSFT'
    }
    
    # Initialize the merged DataFrame
    merged_data = []
    
    # For each company and date in articles
    for company in articles_df['company'].unique():
        company_articles = articles_df[articles_df['company'] == company]
        symbol = company_to_symbol[company]
        
        # Get stock data for this company
        company_stocks = stock_df[stock_df['Ticker'] == symbol].copy()
        
        # Create a date range for this company
        min_date = min(company_articles['date'].min(), company_stocks['Date'].min())
        max_date = max(company_articles['date'].max(), company_stocks['Date'].max())
        date_range = pd.date_range(start=min_date, end=max_date, freq='D').date
        
        # Create a DataFrame with all dates
        all_dates = pd.DataFrame({'date': date_range})
        
        # Merge articles
        articles_merged = pd.merge(all_dates, company_articles, on='date', how='left')
        
        # Merge stock prices
        stocks_merged = pd.merge(all_dates, company_stocks, 
                               left_on='date', right_on='Date', how='left')
        
        # Forward fill missing stock prices
        stocks_merged = stocks_merged.sort_values('date')
        stocks_merged = stocks_merged.fillna(method='ffill')
        
        # Backward fill any remaining missing values (for earliest dates)
        stocks_merged = stocks_merged.fillna(method='bfill')
        
        # Combine the data
        for _, row in articles_merged.iterrows():
            date = row['date']
            stock_data = stocks_merged[stocks_merged['date'] == date].iloc[0]
            
            merged_data.append({
                'date': date,
                'company': company,
                'symbol': symbol,
                'article_count': row['article_count'],
                'avg_sentiment': row['avg_sentiment'],
                'open': stock_data['Open'],
                'high': stock_data['High'],
                'low': stock_data['Low'],
                'close': stock_data['Close'],
                'volume': stock_data['Volume']
            })
    
    # Create final DataFrame
    final_df = pd.DataFrame(merged_data)
    
    # Sort by date and company
    final_df = final_df.sort_values(['date', 'company'])
    
    return final_df

def main():
    # Initialize combined articles DataFrame
    all_articles_df = pd.DataFrame()
    
    # Process each cluster
    for cluster in CLUSTERS:
        print(f"\nProcessing cluster: {cluster['uri']}")
        print(f"Date range: {cluster['start_date']} to {cluster['end_date']}")
        
        # Connect to database
        collection = connect_to_db(cluster['uri'])
        
        # Get articles for each company
        company_articles = get_company_articles(collection, cluster['start_date'], cluster['end_date'])
        
        # Create daily aggregates DataFrame
        articles_df = create_daily_aggregates(company_articles, cluster['start_date'], cluster['end_date'])
        
        # Append to combined DataFrame
        all_articles_df = pd.concat([all_articles_df, articles_df], ignore_index=True)
    
    # Merge with stock prices
    stock_prices_path = 'ohlcv_data_jan_june_2024.csv'
    final_df = merge_with_stock_prices(all_articles_df, stock_prices_path)
    
    # Save to CSV
    final_df.to_csv('combined_analysis_jan_june_2024.csv', index=False)
    print("\nData saved to 'combined_analysis_jan_june_2024.csv'")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    for company in KEYWORDS:
        company_data = final_df[final_df['company'] == company]
        print(f"\n{company.capitalize()}:")
        print(f"Total articles: {company_data['article_count'].sum()}")
        print(f"Average sentiment: {company_data['avg_sentiment'].mean():.3f}")
        print(f"Date range: {company_data['date'].min()} to {company_data['date'].max()}")
        print(f"Days with articles: {company_data[company_data['article_count'] > 0]['date'].nunique()}")
        print(f"Days with stock data: {company_data[company_data['close'].notna()]['date'].nunique()}")

if __name__ == "__main__":
    main()
