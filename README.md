# Stock Analysis Dashboard

A comprehensive stock analysis platform that combines financial data with news sentiment analysis to provide insights into stock market trends and company performance.

## Features

- Real-time stock price data (OHLCV) visualization
- News sentiment analysis for major tech companies
- Interactive dashboard with multiple visualization options
- Historical data analysis from January to June 2024
- RESTful API endpoints for data access
- Heatmap visualization of sentiment across companies
- Daily statistics and trend analysis

## Tech Stack

- **Backend**: FastAPI, MongoDB
- **Data Processing**: Pandas, NumPy
- **Visualization**: Streamlit, Plotly
- **Data Collection**: yfinance, GDELT
- **Sentiment Analysis**: TextBlob

## Project Structure

- `main.py` - FastAPI backend server with REST endpoints
- `dashboard.py` - Streamlit dashboard application
- `gdelt_loader.py` - GDELT data collection and processing
- `db.py` - Database operations and utilities
- `mongo.py` - MongoDB connection and query handlers
- `combine.py` - Data combination and processing utilities
- `requirements.txt` - Project dependencies

## Data Files

- `combined_analysis_jan_june_2024.csv` - Combined stock and sentiment data
- `ohlcv_data_jan_june_2024.csv` - Historical stock price data
- Company logo images (apple.jpeg, google.jpeg, etc.)

## Setup Instructions

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
MONGO_ATLAS_URI_1=your_mongodb_uri_1
MONGO_ATLAS_URI_2=your_mongodb_uri_2
MONGO_ATLAS_URI_3=your_mongodb_uri_3
```

## Running the Application

1. Start the FastAPI backend:
```bash
python main.py
```
The API will be available at `http://localhost:8000`

2. Launch the Streamlit dashboard:
```bash
streamlit run dashboard.py
```
The dashboard will be available at `http://localhost:8501`

## API Endpoints

- `GET /` - Welcome message
- `GET /companies` - List of available companies
- `GET /time-range` - Available date range
- `GET /ohlcv/{symbol}` - OHLCV data for a specific company
- `GET /sentiment/{symbol}` - Sentiment data for a specific company
- `GET /heatmap` - Heatmap data for all companies
- `GET /daily-stats` - Daily statistics across all companies

## Data Sources

- Stock data: Yahoo Finance (via yfinance)
- News data: GDELT Project
- Company information: Various financial APIs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Contact

[Add your contact information here] 