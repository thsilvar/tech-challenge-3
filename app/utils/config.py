import os


def _safe_mongo_uri(val: str | None) -> str:
    # Se vier vazio ou apontar para localhost, usa service 'mongo' (rede do compose/devcontainer)
    if not val or "localhost" in val or "127.0.0.1" in val:
        return "mongodb+srv://dbProject1:gLm3yXyzdYuUXj17@cluster0.vyomg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    return val


MONGO_URI = _safe_mongo_uri(os.getenv("MONGO_URI"))
DB_NAME = os.getenv("DB_NAME", "b3_database")
PRICES_COL = os.getenv("PRICES_COL", "ibovespa_historico")
MODELS_COL = os.getenv("MODELS_COL", "models")

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "models")
COL_CLOSE_FOR_MODEL = "Fech_Ajustado"

