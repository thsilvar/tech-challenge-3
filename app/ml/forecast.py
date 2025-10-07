import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

COL_DATA  = "Data"
COL_CLOSE = "Fech_Ajustado"

def _make_regression_features(df: pd.DataFrame):
    d = df.copy().sort_values(COL_DATA).reset_index(drop=True)
    d["ret"] = d[COL_CLOSE].pct_change(1)
    for k in [1,2,3,5,10]:
        d[f"ret_lag_{k}"] = d["ret"].shift(k)
    d = d.dropna().copy()
    X = d[[f"ret_lag_{k}" for k in [1,2,3,5,10]]]
    y = d["ret"]
    return d, X, y

def train_simple_return_model(df: pd.DataFrame) -> Pipeline:
    _, X, y = _make_regression_features(df)
    pipe = Pipeline([("scaler", StandardScaler()), ("linreg", LinearRegression())])
    pipe.fit(X, y)
    return pipe

def project_next_7_days(df: pd.DataFrame, model: Pipeline):
    d = df.copy().sort_values(COL_DATA).reset_index(drop=True)
    d["ret"] = d[COL_CLOSE].pct_change(1)
    last_close = float(d[COL_CLOSE].iloc[-1])
    for k in [1,2,3,5,10]:
        d[f"ret_lag_{k}"] = d["ret"].shift(k)
    row = {f"ret_lag_{k}": float(d[f'ret_lag_{k}'].dropna().iloc[-1]) for k in [1,2,3,5,10]}

    preds = []
    cur_close = last_close
    cur_lags = row.copy()
    for step in range(1, 8):
        X_last = pd.DataFrame([cur_lags])
        ret_pred = float(model.predict(X_last)[0])
        cur_close = cur_close * (1.0 + ret_pred)
        preds.append({"d": step, "ret_pred": ret_pred, "close_pred": cur_close})
        cur_lags = {"ret_lag_1": ret_pred,
                    "ret_lag_2": cur_lags.get("ret_lag_1", ret_pred),
                    "ret_lag_3": cur_lags.get("ret_lag_2", ret_pred),
                    "ret_lag_5": cur_lags.get("ret_lag_3", ret_pred),
                    "ret_lag_10": cur_lags.get("ret_lag_5", ret_pred)}
    return preds
