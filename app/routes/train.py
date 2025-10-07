from fastapi import APIRouter, Body
from typing import Optional, Dict, Any

from app.ml.train import train_one_ticker, train_all

router = APIRouter()

@router.post("/train")
def train_models(
    ticker: Optional[str] = Body(None, embed=True),
    version: Optional[str] = Body(None, embed=True)
) -> Dict[str, Any]:
    if ticker:
        metrics, path = train_one_ticker(ticker, version)
        return {"status": "ok", "ticker": ticker, "metrics": metrics, "artifact_path": path}
    return train_all(version)
