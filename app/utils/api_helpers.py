from typing import Tuple, Dict, Any
import joblib
import pandas as pd

from app.db.db import get_client, prices_col, models_col

def load_last_n_days(ticker: str, n: int = 40) -> pd.DataFrame:
    cli = get_client()
    col = prices_col(cli)
    cur = col.find({"Ticker": ticker}, {"_id": 0}).sort("Data", 1)
    df = pd.DataFrame(list(cur))
    if df.empty:
        return df
    return df.tail(n).copy()

def load_latest_model_artifact(ticker: str) -> Tuple[Any, Dict]:
    cli = get_client()
    m = models_col(cli).find_one({"ticker": ticker}, sort=[("version", -1)])
    if not m:
        return None, {}
    art = joblib.load(m["artifact_path"])
    return art, m.get("metrics", {})