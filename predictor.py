# predictor.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import ta

def prepare_ml_data(df):
    df = df.copy()
    df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"]).rsi()
    df["MACD"] = ta.trend.MACD(close=df["Close"]).macd()
    df["20DMA"] = df["Close"].rolling(window=20).mean()
    df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    df.dropna(inplace=True)

    features = ["RSI", "MACD", "Volume", "20DMA"]
    X = df[features]
    y = df["Target"]
    return X, y

def train_and_evaluate_model(df):
    X, y = prepare_ml_data(df)
    # time-based split: don't shuffle
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    return acc, cm, model

if __name__ == "__main__":
    # Quick CLI usage if run directly
    df = pd.read_csv("data/stock_data.csv")
    tickers = [col.replace("Close_", "") for col in df.columns if col.startswith("Close_")]
    results = []
    for ticker in tickers:
        close_col = f"Close_{ticker}"
        volume_col = f"Volume_{ticker}"
        if close_col not in df.columns or volume_col not in df.columns:
            continue
        df_ticker = df[[close_col, volume_col]].copy()
        df_ticker.columns = ["Close", "Volume"]
        acc, cm, model = train_and_evaluate_model(df_ticker)
        results.append({"Ticker": ticker, "Accuracy": acc, "Confusion_Matrix": cm.tolist()})
    print(pd.DataFrame(results))
