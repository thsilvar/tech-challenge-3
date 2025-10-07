from pymongo import MongoClient
from typing import List
from app.utils.config import MONGO_URI, DB_NAME, PRICES_COL, MODELS_COL

def get_client() -> MongoClient:
    return MongoClient(MONGO_URI)

def prices_col(cli: MongoClient):
    return cli[DB_NAME][PRICES_COL]

def models_col(cli: MongoClient):
    return cli[DB_NAME][MODELS_COL]

def list_tickers(cli: MongoClient) -> List[str]:
    return sorted(prices_col(cli).distinct("Ticker"))
