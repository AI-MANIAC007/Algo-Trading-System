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
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    return acc, cm

# Load your CSV
df = pd.read_csv("data/stock_data.csv")

# Detect tickers from column names
tickers = [col.replace("Close_", "") for col in df.columns if col.startswith("Close_")]

results = []

for ticker in tickers:
    close_col = f"Close_{ticker}"
    volume_col = f"Volume_{ticker}"
    
    # Skip if volume data is missing
    if close_col not in df.columns or volume_col not in df.columns:
        continue
    
    df_ticker = df[[close_col, volume_col]].copy()
    df_ticker.columns = ["Close", "Volume"]
    
    acc, cm = train_and_evaluate_model(df_ticker)
    results.append({
        "Ticker": ticker,
        "Accuracy": acc,
        "Confusion_Matrix": cm.tolist()
    })

# Convert results to DataFrame for easy view/export
results_df = pd.DataFrame(results)
print(results_df)
