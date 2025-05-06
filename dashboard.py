import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np
import base64
import os

# Ticker to logo filename mapping
TICKER_LOGO_MAP = {
    "AAPL": "apple.jpeg",
    "GOOGL": "google.jpeg",
    "NVDA": "nvidia.jpeg",
    "TSLA": "tesla.jpeg",
    "MSFT": "microsoft.jpeg"
}

# Page config
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"   # <-- optional
)

# Constants
API_BASE_URL = "http://localhost:8000"
DEFAULT_START_DATE = "2024-01-01"
DEFAULT_END_DATE = "2024-06-22"

# Company color mapping
COMPANY_COLORS = {
    "TSLA": "#E82127",  # Tesla Red
    "AAPL": "#FF69B4",  # Apple Pink
    "GOOGL": "#FFA500", # Google Orange
    "NVDA": "#76B900",  # NVIDIA Green
    "MSFT": "#0078D4"   # Microsoft Blue
}

# Helper functions
def fetch_companies():
    try:
        response = requests.get(f"{API_BASE_URL}/companies")
        if response.status_code == 200:
            return response.json()["companies"]
        st.error("Failed to fetch companies from API")
        return []
    except Exception as e:
        st.error(f"Error fetching companies: {str(e)}")
        return []

def fetch_time_range():
    try:
        response = requests.get(f"{API_BASE_URL}/time-range")
        if response.status_code == 200:
            return response.json()
        return {
            "start_date": DEFAULT_START_DATE,
            "end_date": DEFAULT_END_DATE
        }
    except Exception as e:
        st.error(f"Error fetching time range: {str(e)}")
        return {
            "start_date": DEFAULT_START_DATE,
            "end_date": DEFAULT_END_DATE
        }

def fetch_ohlcv_data(symbol, start_date, end_date):
    try:
        response = requests.get(
            f"{API_BASE_URL}/ohlcv/{symbol}",
            params={"start_date": start_date, "end_date": end_date}
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch OHLCV data for {symbol}")
        return None
    except Exception as e:
        st.error(f"Error fetching OHLCV data: {str(e)}")
        return None

def fetch_sentiment_data(symbol, start_date, end_date):
    try:
        response = requests.get(
            f"{API_BASE_URL}/sentiment/{symbol}",
            params={"start_date": start_date, "end_date": end_date}
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch sentiment data for {symbol}")
        return None
    except Exception as e:
        st.error(f"Error fetching sentiment data: {str(e)}")
        return None

def fetch_heatmap_data(start_date, end_date):
    try:
        response = requests.get(
            f"{API_BASE_URL}/heatmap",
            params={"start_date": start_date, "end_date": end_date}
        )
        if response.status_code == 200:
            return response.json()["data"]
        st.error("Failed to fetch heatmap data")
        return []
    except Exception as e:
        st.error(f"Error fetching heatmap data: {str(e)}")
        return []

def fetch_daily_stats(start_date, end_date):
    try:
        response = requests.get(
            f"{API_BASE_URL}/daily-stats",
            params={"start_date": start_date, "end_date": end_date}
        )
        if response.status_code == 200:
            return response.json()["data"]
        st.error("Failed to fetch daily statistics")
        return []
    except Exception as e:
        st.error(f"Error fetching daily statistics: {str(e)}")
        return []

# Custom CSS (add padding-bottom for footer)
st.markdown(
    """
    <style>
    /* Hide the redundant collapsed‐sidebar toggle on the far left */
    button[data-testid="collapsedControl"] {
        display: none !important;
    }

    /* App background */
    .main {
        background-color: #1a1a1a;
        color: white;
    }

    /* Ensure footer has bottom padding */
    .stApp > footer {
        padding-bottom: 70px !important;
    }

    /* Metric card styling */
    .metric-card {
        background-color: #2d2d2d;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        color: white;
        margin-bottom: 20px;
    }
    .metric-card h3 {
        color: #a3a3a3;
        font-size: 14px;
        margin-bottom: 8px;
        font-weight: normal;
    }
    .metric-card h2 {
        color: white;
        font-size: 24px;
        margin: 0;
        font-weight: bold;
    }

    /* Company header */
    .company-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        color: white;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .company-logo {
        width: 40px;
        height: 40px;
        border-radius: 5px;
        object-fit: contain;
    }

    /* Positive/negative value coloring */
    .positive-value {
        color: #00C805 !important;
    }
    .negative-value {
        color: #FF5B5B !important;
    }

    /* Footer bar */
    .footer-flex {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        background: #181818;
        color: #aaa;
        font-size: 0.95em;
        z-index: 100;
        padding: 10px 24px 10px 24px;
        border-top: 1px solid #333;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .footer-flex a {
        color: #aaa;
        text-decoration: underline;
        margin: 0 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main dashboard
st.title("📊 Stock Analysis Dashboard")

# GitHub badge/link at the top
st.markdown(
    '''
    <a href="https://github.com/pranav-gilda/stock-analysis-dashboard" target="_blank" style="text-decoration:none;">
        <img src="https://img.shields.io/badge/GitHub-Repo-blue?logo=github" alt="GitHub Repo" style="height:28px;"/>
    </a>
    ''',
    unsafe_allow_html=True
)

# Sidebar - All sidebar elements consolidated here
with st.sidebar:
    st.header("📅 Date Range")
    time_range = fetch_time_range()
    start_date = st.date_input(
        "Start Date",
        value=datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d"),
        min_value=datetime.strptime(time_range["start_date"], "%Y-%m-%d"),
        max_value=datetime.strptime(time_range["end_date"], "%Y-%m-%d")
    )
    end_date = st.date_input(
        "End Date",
        value=datetime.strptime(DEFAULT_END_DATE, "%Y-%m-%d"),
        min_value=datetime.strptime(time_range["start_date"], "%Y-%m-%d"),
        max_value=datetime.strptime(time_range["end_date"], "%Y-%m-%d")
    )

    st.header("🏢 Company Selection")
    companies = fetch_companies()
    if not companies:
        st.error("No companies available. Please check your API connection.")
        st.stop()

    company_symbols = [company["symbol"] for company in companies]
    selected_company = st.selectbox(
        "Select Company",
        company_symbols,
        index=0
    )

    # Display company logo in sidebar with correct mapping and fallback
    logo_file = TICKER_LOGO_MAP.get(selected_company)
    logo_path = f"logos/{logo_file}" if logo_file else None
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=100)
    else:
        st.markdown('<span style="font-size:2em;">📈</span>', unsafe_allow_html=True)

# Get company name for display
company_name = next((company["company"] for company in companies if company["symbol"] == selected_company), selected_company)

# Format dates for API
start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

# Fetch data
ohlcv_data = fetch_ohlcv_data(selected_company, start_date_str, end_date_str)
sentiment_data = fetch_sentiment_data(selected_company, start_date_str, end_date_str)
heatmap_data = fetch_heatmap_data(start_date_str, end_date_str)
daily_stats = fetch_daily_stats(start_date_str, end_date_str)

# Company header with color
company_color = COMPANY_COLORS.get(selected_company, "#000000")
st.markdown(f"""
    <div class="company-header" style="color: {company_color}">
        {company_name} ({selected_company})
    </div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["📈 OHLCV & Volume", "😊 Sentiment Analysis", "📊 Daily Statistics"])

# OHLCV & Volume Tab
with tab1:
    if ohlcv_data and "data" in ohlcv_data:
        df_ohlcv = pd.DataFrame(ohlcv_data["data"])
        
        # Calculate key metrics
        current_price = df_ohlcv['close'].iloc[-1]
        price_change = ((current_price - df_ohlcv['close'].iloc[0]) / df_ohlcv['close'].iloc[0]) * 100
        avg_volume = df_ohlcv['volume'].mean()
        end_date_display = df_ohlcv['date'].iloc[-1]
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Latest Price</h3>
                    <h2>${current_price:.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Price Change</h3>
                    <h2 class="{'positive-value' if price_change >= 0 else 'negative-value'}">{price_change:.2f}%</h2>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Avg Daily Volume</h3>
                    <h2>{avg_volume:,.0f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add OHLCV candlestick with standard colors
        fig.add_trace(
            go.Candlestick(
                x=df_ohlcv['date'],
                open=df_ohlcv['open'],
                high=df_ohlcv['high'],
                low=df_ohlcv['low'],
                close=df_ohlcv['close'],
                name="OHLC",
                increasing_line_color='#00C805',  # Standard green
                decreasing_line_color='#FF5B5B',  # Standard red
                increasing_fillcolor='#00C805',
                decreasing_fillcolor='#FF5B5B'
            ),
            secondary_y=False,
        )
        
        # Add volume bars with company color
        fig.add_trace(
            go.Bar(
                x=df_ohlcv['date'],
                y=df_ohlcv['volume'],
                name="Volume",
                opacity=0.3,
                marker_color=COMPANY_COLORS.get(selected_company, '#808080')  # Use company color
            ),
            secondary_y=True,
        )
        
        # Update layout with dark theme
        fig.update_layout(
            title=f"{company_name} ({selected_company}) - OHLCV Chart",
            yaxis_title="Price ($)",
            yaxis2_title="Volume",
            height=600,
            template="plotly_dark",
            hovermode="x unified",
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white')
        )
        
        # Update axes
        fig.update_xaxes(gridcolor='#333333', zerolinecolor='#333333')
        fig.update_yaxes(gridcolor='#333333', zerolinecolor='#333333')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No OHLCV data available for the selected period")

# Sentiment Analysis Tab
with tab2:
    if sentiment_data and "data" in sentiment_data:
        df_sentiment = pd.DataFrame(sentiment_data["data"])
        
        # Calculate sentiment metrics for the selected date range
        df_sentiment['date'] = pd.to_datetime(df_sentiment['date'])
        mask = (df_sentiment['date'] >= pd.to_datetime(start_date_str)) & (df_sentiment['date'] <= pd.to_datetime(end_date_str))
        df_sentiment_filtered = df_sentiment[mask]
        
        avg_sentiment = df_sentiment_filtered['avg_sentiment'].mean()
        total_articles = df_sentiment_filtered['article_count'].sum()
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Average Sentiment</h3>
                    <h2 class="{'positive-value' if avg_sentiment >= 0 else 'negative-value'}">{avg_sentiment:.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Total Articles</h3>
                    <h2>{total_articles:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add sentiment line
        fig.add_trace(
            go.Scatter(
                x=df_sentiment_filtered['date'],
                y=df_sentiment_filtered['avg_sentiment'],
                name="Average Sentiment",
                line=dict(color=company_color, width=2),
                mode='lines+markers'
            ),
            secondary_y=False,
        )
        
        # Add article count bars
        fig.add_trace(
            go.Bar(
                x=df_sentiment_filtered['date'],
                y=df_sentiment_filtered['article_count'],
                name="Article Count",
                opacity=0.5,
                marker_color=company_color
            ),
            secondary_y=True,
        )
        
        # Update layout
        fig.update_layout(
            title=f"{company_name} ({selected_company}) - Sentiment Analysis",
            yaxis_title="Average Sentiment",
            yaxis2_title="Article Count",
            height=600,
            template="plotly_white",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap
        if heatmap_data:
            df_heatmap = pd.DataFrame(heatmap_data)
            
            # Filter heatmap data for selected date range
            df_heatmap['date'] = pd.to_datetime(df_heatmap['date'])
            mask = (df_heatmap['date'] >= pd.to_datetime(start_date_str)) & (df_heatmap['date'] <= pd.to_datetime(end_date_str))
            df_heatmap_filtered = df_heatmap[mask]
            
            pivot_table = df_heatmap_filtered.pivot(
                index='date',
                columns='company',
                values='avg_sentiment'
            )
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_table.values,
                x=pivot_table.columns,
                y=pivot_table.index,
                colorscale='RdYlGn',
                zmid=0,
                hoverongaps=False
            ))
            
            fig.update_layout(
                title="Sentiment Heatmap Across Companies",
                height=600,
                template="plotly_white",
                xaxis_title="Company",
                yaxis_title="Date"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No sentiment data available for the selected period")

# Daily Statistics Tab
with tab3:
    if daily_stats:
        df_daily = pd.DataFrame(daily_stats)
        
        # Filter daily stats for selected date range
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        mask = (df_daily['date'] >= pd.to_datetime(start_date_str)) & (df_daily['date'] <= pd.to_datetime(end_date_str))
        df_daily_filtered = df_daily[mask]
        
        # Calculate daily metrics
        total_articles = df_daily_filtered['article_count'].sum()
        avg_sentiment = df_daily_filtered['avg_sentiment'].mean()
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Total Articles</h3>
                    <h2>{total_articles:,}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Average Daily Sentiment</h3>
                    <h2 class="{'positive-value' if avg_sentiment >= 0 else 'negative-value'}">{avg_sentiment:.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add total article count
        fig.add_trace(
            go.Bar(
                x=df_daily_filtered['date'],
                y=df_daily_filtered['article_count'],
                name="Total Articles",
                opacity=0.5,
                marker_color=company_color
            ),
            secondary_y=False,
        )
        
        # Add average sentiment
        fig.add_trace(
            go.Scatter(
                x=df_daily_filtered['date'],
                y=df_daily_filtered['avg_sentiment'],
                name="Average Sentiment",
                line=dict(color=company_color, width=2),
                mode='lines+markers'
            ),
            secondary_y=True,
        )
        
        # Update layout
        fig.update_layout(
            title="Daily Statistics",
            yaxis_title="Article Count",
            yaxis2_title="Average Sentiment",
            height=600,
            template="plotly_white",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No daily statistics available for the selected period")

# Footer: GitHub left, sources center, created by right
st.markdown(
    """
    <div class="footer-flex">
        <div>
            <a href="https://github.com/pranav-gilda/stock-analysis-dashboard" target="_blank">GitHub Repo</a>
        </div>
        <div>
            Data sources:
            <a href="https://ranaroussi.github.io/yfinance/" target="_blank">Yahoo Finance</a> |
            <a href="https://www.gdeltproject.org/" target="_blank">GDELT</a>
        </div>
        <div>
            Created by
            <a href="https://www.linkedin.com/in/pranavgilda/" target="_blank">Pranav Gilda</a>,
            <a href="https://www.linkedin.com/in/ramesh-keshav/" target="_blank">Keshav Ramesh</a>,
            <a href="https://www.linkedin.com/in/rakesh-prasanna/" target="_blank">Rakesh Prasanna</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
) 
