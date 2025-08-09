import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_data(tickers, days=180):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    combined_df = pd.DataFrame()

    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        df.columns = [f"{col}_{ticker.split('.')[0]}" if not isinstance(col, tuple) else f"{col[0]}_{ticker.split('.')[0]}" for col in df.columns]

        if combined_df.empty:
            combined_df = df
        else:
            combined_df = combined_df.join(df, how="outer")

    combined_df.reset_index(inplace=True)
    return combined_df

def save_to_csv(df, filepath="data/stock_data.csv"):
    df.to_csv(filepath, index=False)
