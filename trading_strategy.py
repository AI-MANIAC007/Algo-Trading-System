import pandas as pd
import numpy as np
import ta

# ========================
# 1. Indicator Calculation
# ========================
def add_indicators(df):
    df = df.copy()
    
    # Ensure Close is numeric
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)

    # RSI
    df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()

    # Moving Averages
    df["20DMA"] = df["Close"].rolling(window=20).mean()
    df["50DMA"] = df["Close"].rolling(window=50).mean()

    return df

# ========================
# 2. Detect Crossovers
# ========================
def detect_crossover(short_ma, long_ma):
    """
    Returns True on the exact day a bullish crossover occurs:
    short_ma crosses above long_ma from below.
    """
    return (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))

# ========================
# 3. Trading Strategy
# ========================
def apply_strategy(df, ticker):
    df = add_indicators(df)

    # Buy when RSI < 50 and 20DMA > 50DMA (trend up)
    df["Buy_Signal"] = (df["RSI"] < 50) & (df["20DMA"] > df["50DMA"])

    # Sell when RSI > 55 and 20DMA < 50DMA (trend down)
    df["Sell_Signal"] = (df["RSI"] > 55) & (df["20DMA"] < df["50DMA"])

    # Track Position
    df["Position"] = 0
    position = 0
    for i in range(1, len(df)):
        if df["Buy_Signal"].iloc[i]:
            position = 1
            buy_price = df["Close"].iloc[i]
            df.at[df.index[i], "Buy_Price"] = buy_price
        elif df["Sell_Signal"].iloc[i]:
            position = 0
            df.at[df.index[i], "Sell_Price"] = df["Close"].iloc[i]
        df.at[df.index[i], "Position"] = position

    # Returns
    df["Daily_Return"] = df["Close"].pct_change()
    df["Strategy_Return"] = df["Daily_Return"] * df["Position"].shift(1)
    df["Cumulative_Strategy_Return"] = (1 + df["Strategy_Return"]).cumprod()

    # Add ticker column for identification
    df["Ticker"] = ticker

    # Reset index for final DataFrame
    df.reset_index(inplace=True)
    return df
# ========================
# 4. Backtesting Function
# ========================
def backtest_all(csv_file_path):
    df_all = pd.read_csv(csv_file_path, parse_dates=["Date"])
    df_all.set_index("Date", inplace=True)

    print("Columns found in CSV:")
    print(df_all.columns.tolist())

    # Detect tickers from "Close_<TICKER>" columns
    tickers = set()
    for col in df_all.columns:
        if "Close_" in col:
            ticker = col.split("Close_")[1]
            tickers.add(ticker)

    print(f"🔍 Tickers detected: {tickers}")
    if not tickers:
        print("No valid stock data found. Please check column names and data.")
        return pd.DataFrame()

    all_results = []
    for ticker in tickers:
        try:
            df = pd.DataFrame({
                "Close": df_all[f"Close_{ticker}"]
            }, index=df_all.index)

            # Apply strategy to each ticker
            df = apply_strategy(df, ticker)
            all_results.append(df)

        except KeyError as e:
            print(f"Skipping {ticker} due to missing data: {e}")
            continue

    if not all_results:
        print("No backtest results to save.")
        return pd.DataFrame()

    # Merge all results
    result_df = pd.concat(all_results)
    return result_df
