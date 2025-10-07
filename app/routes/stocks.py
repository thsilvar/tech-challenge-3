from fastapi import APIRouter
from typing import Dict, Any

from app.ml.features import build_features
from app.ml.forecast import train_simple_return_model, project_next_7_days
from app.utils.api_helpers import load_last_n_days, load_latest_model_artifact

router = APIRouter()

@router.get("/stocks/{ticker}")
def stock_detail(ticker: str) -> Dict[str, Any]:
    df = load_last_n_days(ticker, n=180)
    if df.empty:
        return {"error": "ticker sem dados"}

    df = df.sort_values("Data").reset_index(drop=True)

    hist = df.tail(30)[["Data","Fechamento"]].copy()
    history = [{"date": str(r["Data"]), "close": float(r["Fechamento"])} for _, r in hist.iterrows()]

    d1_pred, p_up, metrics = None, None, {}
    art, metrics = load_latest_model_artifact(ticker)
    if art is not None:
        df_feat, feat_cols = build_features(df)
        if not df_feat.empty:
            X_last = df_feat[feat_cols].tail(1)
            p_up = float(art["model"].predict_proba(X_last)[:,1][0])
            d1_pred = int(p_up >= 0.5)

    proj = []
    try:
        reg_model = train_simple_return_model(df.rename(columns={"Fech_Ajustado":"Fech_Ajustado"}))
        proj = project_next_7_days(df.rename(columns={"Fech_Ajustado":"Fech_Ajustado"}), reg_model)
        proj = [{"d_plus": p["d"], "close_pred": p["close_pred"], "ret_pred": p["ret_pred"]} for p in proj]
    except Exception as e:
        proj = []
        metrics = metrics or {}
        metrics["projection_error"] = str(e)

    return {
        "ticker": ticker,
        "history_30d": history,
        "classification_d1": {"pred_up": d1_pred, "prob_up": p_up, "model_metrics": metrics},
        "projection_7d": proj
    }
