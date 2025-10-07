import pandas as pd
from app.utils.config import COL_CLOSE_FOR_MODEL

COL_DATA   = "Data"
COL_TICKER = "Ticker"
COL_OPEN   = "Abertura"
COL_HIGH   = "Maxima"
COL_LOW    = "Minima"
COL_CLOSE  = COL_CLOSE_FOR_MODEL

def build_features(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame(), []

    d = df.copy()
    d[COL_DATA] = pd.to_datetime(d[COL_DATA])
    d = d.sort_values(COL_DATA)

    d["ret_1"]  = d[COL_CLOSE].pct_change(1)
    d["ret_5"]  = d[COL_CLOSE].pct_change(5)
    d["ret_10"] = d[COL_CLOSE].pct_change(10)

    d["vol_5"]  = d["Volume"].rolling(5).std()
    d["vol_10"] = d["Volume"].rolling(10).std()

    d["sma_5"]  = d[COL_CLOSE].rolling(5).mean()
    d["sma_10"] = d[COL_CLOSE].rolling(10).mean()
    d["sma_20"] = d[COL_CLOSE].rolling(20).mean()
    d["sma_5_vs_20"] = d["sma_5"] / d["sma_20"]

    low14  = d[COL_LOW].rolling(14).min()
    high14 = d[COL_HIGH].rolling(14).max()
    d["stoch_k"] = (d[COL_CLOSE] - low14) / (high14 - low14)

    d["weekday"] = d[COL_DATA].dt.weekday.astype(int)

    d["target"] = (d[COL_CLOSE].shift(-1) / d[COL_CLOSE] - 1.0 > 0).astype(int)

    feature_cols = [
        "ret_1","ret_5","ret_10","vol_5","vol_10",
        "sma_5","sma_10","sma_20","sma_5_vs_20","stoch_k","weekday"
    ]
    d[feature_cols] = d[feature_cols].shift(1)

    d = d.dropna().copy()
    return d, feature_cols
