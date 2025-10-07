# app/app.py
from fastapi import FastAPI
from app.routes import market, stocks, train

app = FastAPI(
    title="Stock ML API",
    version="1.0",
    docs_url="/swagger-ui.html",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

@app.get("/")
def health():
    return {"ok": True}

app.include_router(market.router, tags=["market"])
app.include_router(stocks.router, tags=["stocks"])
app.include_router(train.router, tags=["train"])
