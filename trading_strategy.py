# strategies/rsi_ma_strategy.py

import pandas as pd
import numpy as np
import ta

def add_indicators(df):
    df = df.copy()
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)
    df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
    df["20DMA"] = df["Close"].rolling(window=20).mean()
    df["50DMA"] = df["Close"].rolling(window=50).mean()
    return df

def detect_crossover(short_ma, long_ma):
    return (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))

def apply_strategy(df):
    df = add_indicators(df)

    df["Buy_Signal"] = (df["RSI"] < 30) & detect_crossover(df["20DMA"], df["50DMA"])
    df["Sell_Signal"] = (df["RSI"] > 70) & detect_crossover(df["50DMA"], df["20DMA"])
    
    df["Position"] = 0
    position = 0

    for i in range(1, len(df)):
        if df["Buy_Signal"].iloc[i] and position == 0:
            position = 1
        elif df["Sell_Signal"].iloc[i] and position == 1:
            position = 0
        df.at[df.index[i], "Position"] = position

    df["Daily_Return"] = df["Close"].pct_change()
    df["Strategy_Return"] = df["Daily_Return"] * df["Position"].shift(1)
    df["Cumulative_Strategy_Return"] = (1 + df["Strategy_Return"]).cumprod()

    return df

def backtest_all_stocks(csv_file_path):
    df_all = pd.read_csv(csv_file_path)
    all_results = []

    for ticker in df_all["Ticker"].unique():
        df_ticker = df_all[df_all["Ticker"] == ticker].copy()
        df_ticker = apply_strategy(df_ticker)
        all_results.append(df_ticker)

    result_df = pd.concat(all_results)
    return result_df

if __name__ == "__main__":
    results_df = backtest_all_stocks("data/stock_data.csv")
    results_df.to_csv("data/backtest_signals.csv", index=False)
    print("Backtest signals data is stored sucessfully")