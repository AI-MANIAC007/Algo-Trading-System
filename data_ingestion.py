import yfinance as yf
import pandas as pd
from datetime import datetime,timedelta

#This function fetches the 6 months price data of the given stocks 
def fetch_data(tickers, days=180):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    all_data = []

    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False,auto_adjust=True)
        df["Ticker"] = ticker
        all_data.append(df)

    df_combined = pd.concat(all_data)
    df_combined.reset_index(inplace=True)
    return df_combined

#This function creates a csv file to store the stock price data
def save_to_csv(df, filepath="data/stock_data.csv"):
    df.to_csv(filepath, index=False)

if __name__ == "__main__":
    tickers = ["ADANIPOWER.NS", "ITC.NS", "NATCOPHARM.NS"]  
    df = fetch_data(tickers)
    save_to_csv(df)
    print("Stock data is successfully saved.")