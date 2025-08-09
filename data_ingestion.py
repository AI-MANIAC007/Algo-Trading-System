# data_ingestion.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def fetch_data(tickers, days=180):
    """
    Fetch daily OHLCV for tickers (default 180 days) and return a wide-format DataFrame
    where columns are like Close_RELIANCE, Volume_RELIANCE, etc.
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    combined_df = pd.DataFrame()

    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        # If no data, skip
        if df.empty:
            print(f"⚠ No data for {ticker}")
            continue

        # Keep desired columns and rename with ticker suffix
        df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].copy()
        # rename columns to e.g. Close_RELIANCE
        suffix = ticker.split(".")[0]  # RELIANCE from RELIANCE.NS
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{col[0].replace(' ', '_')}_{col[1]}" for col in df.columns]
        else:
            df.columns = [f"{col.replace(' ', '_')}" for col in df.columns]
        if combined_df.empty:
            combined_df = df
        else:
            combined_df = combined_df.join(df, how="outer")

    combined_df.reset_index(inplace=True)
    return combined_df

def save_to_csv(df, filepath="data/stock_data.csv"):
    os.makedirs("data", exist_ok=True)
    df.to_csv(filepath, index=False)
