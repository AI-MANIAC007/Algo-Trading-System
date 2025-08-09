from data_logger import update_google_sheet
import pandas as pd

signals_df = pd.read_csv("data/backtest_signals.csv")

summary_df = signals_df.groupby("Ticker").agg({
    "Strategy_Return": "sum",
    "Buy_Signal": "sum",
    "Sell_Signal": "sum"
}).reset_index()

# Win ratio logic
signals_df["Win"] = signals_df["Strategy_Return"] > 0
win_ratio_df = signals_df.groupby("Ticker")["Win"].mean().reset_index(name="Win_Ratio")

# Upload to Google Sheet
update_google_sheet(
    sheet_name="Algo_Trading_Logs",
    df_dict={
        "Trade_Log": signals_df.tail(50),  # last 50 trades
        "Summary": summary_df,
        "Win_Ratio": win_ratio_df
    },
    creds_path="C:\\Users\\asus\\Downloads\\algo-trading-system-468317-e3ddb7efa99a.json"
)
