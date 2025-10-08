from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import market, stocks, train

app = FastAPI(
    title="Stock ML API",
    version="1.0",
    docs_url="/swagger-ui.html",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ✅ Libera todos os CORS (qualquer domínio, header e método)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # permite qualquer origem
    allow_credentials=True,    # permite cookies/autenticação (opcional)
    allow_methods=["*"],       # permite todos os métodos HTTP (GET, POST, etc)
    allow_headers=["*"],       # permite todos os headers
)

@app.get("/")
def health():
    return {"ok": True}

# Routers
app.include_router(market.router, tags=["market"])
app.include_router(stocks.router, tags=["stocks"])
app.include_router(train.router, tags=["train"])
