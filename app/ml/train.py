import os
from datetime import datetime
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report

from app.db.db import get_client, prices_col, models_col, list_tickers
from app.ml.features import build_features
from app.utils.config import ARTIFACTS_DIR

def train_one_ticker(ticker: str, version: str | None = None):
    cli = get_client()
    try:
        cur = prices_col(cli).find({"Ticker": ticker}, {"_id":0}).sort("Data", 1)
        df = pd.DataFrame(list(cur))
    finally:
        cli.close()

    if df.empty or len(df) < 60:
        raise RuntimeError(f"[{ticker}] poucos dados para treinar.")

    df_feat, feature_cols = build_features(df)
    X = df_feat[feature_cols].copy()
    y = df_feat["target"].astype(int).copy()

    cat_cols = ["weekday"]
    num_cols = [c for c in feature_cols if c not in cat_cols]

    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ])

    clf = Pipeline([("pre", pre),
                    ("logreg", LogisticRegression(max_iter=1000))])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, shuffle=False)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:,1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "report": classification_report(y_test, y_pred, output_dict=False)
    }

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    version = version or datetime.now().strftime("%Y%m%d")
    path = os.path.join(ARTIFACTS_DIR, f"{ticker}_{version}.joblib")
    joblib.dump({"model": clf, "feature_cols": feature_cols}, path)

    cli = get_client()
    try:
        models_col(cli).update_one(
            {"ticker": ticker},
            {"$set": {"ticker": ticker, "version": version, "artifact_path": path, "metrics": metrics}},
            upsert=True
        )
    finally:
        cli.close()

    return metrics, path

def train_all(version: str | None = None):
    cli = get_client()
    try:
        tickers = list_tickers(cli)
    finally:
        cli.close()
    if not tickers:
        raise RuntimeError("Nenhum ticker encontrado para treinar.")
    out = {}
    for t in tickers:
        try:
            m, p = train_one_ticker(t, version)
            out[t] = {"status":"ok","metrics":m,"artifact_path":p}
        except Exception as e:
            out[t] = {"status":"error","error":str(e)}
    return out
