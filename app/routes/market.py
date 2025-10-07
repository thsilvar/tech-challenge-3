from fastapi import APIRouter
from typing import Dict

from app.db.db import get_client, list_tickers, prices_col, models_col
from app.service.download_b3 import update_ibov_db
from app.ml.features import build_features
from app.utils.api_helpers import load_last_n_days, load_latest_model_artifact

router = APIRouter()

@router.post("/update-market")
def update_market() -> Dict:
    """
    Endpoint que aciona a atualização do banco com os dados do Ibovespa.
    Não recebe lista de tickers — usa a lista interna definida em download_b3.
    """
    inserted = update_ibov_db(days=180)
    return {"Quantidade de linhas atualizadas": inserted}

@router.get("/top-gainers")
def top_gainers():
    cli = get_client()
    tickers = list_tickers(cli)
    rows = []

    for t in tickers:
        df = load_last_n_days(t, n=40)
        if df.empty or len(df) < 31:
            continue
        df = df.sort_values("Data")
        close_now = float(df["Fechamento"].iloc[-1])
        close_30  = float(df["Fechamento"].iloc[-31])
        var_30 = (close_now / close_30) - 1.0

        art, metrics = load_latest_model_artifact(t)
        p_up = None
        if art is not None:
            df_feat, feat_cols = build_features(df)
            if not df_feat.empty:
                X_last = df_feat[feat_cols].tail(1)
                p_up = float(art["model"].predict_proba(X_last)[:,1][0])

        rows.append({
            "ticker": t,
            "var_30d": var_30,
            "price_now": close_now,
            "pred_up_d1": p_up,
            "model_accuracy": metrics.get("accuracy") if metrics else None
        })

    top5 = sorted(rows, key=lambda r: r["var_30d"], reverse=True)[:5]
    return {"top5": top5}