import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pymongo import MongoClient

from app.utils.config import MONGO_URI, DB_NAME, PRICES_COL
from app.db.db import get_client, prices_col

# lista dos principais 60 tickers do Ibovespa (com sufixo .SA para yfinance)
tickers_ibov = [
    'VALE3.SA', 'ITUB4.SA', 'PETR4.SA', 'PETR3.SA', 'ELET3.SA', 'BBDC4.SA',
    'SBSP3.SA', 'B3SA3.SA', 'BPAC11.SA', 'ITSA4.SA', 'BBAS3.SA', 'EMBR3.SA',
    'WEGE3.SA', 'ABEV3.SA', 'EQTL3.SA', 'RDOR3.SA', 'RENT3.SA', 'SUZB3.SA',
    'ENEV3.SA', 'PRIO3.SA', 'VBBR3.SA', 'VIVT3.SA', 'TOTS3.SA', 'RADL3.SA',
    'UGPA3.SA', 'BBDC3.SA', 'CMIG4.SA', 'GGBR4.SA', 'CPLE6.SA', 'RAIL3.SA',
    'ALOS3.SA', 'BBSE3.SA', 'BRFS3.SA', 'NTCO3.SA', 'HYPE3.SA', 'KLBN11.SA',
    'TIMS3.SA', 'CSAN3.SA', 'CCRO3.SA', 'MULT3.SA', 'MGLU3.SA', 'CSNA3.SA',
    'JBSS3.SA', 'HAPV3.SA', 'LREN3.SA', 'ASAI3.SA', 'CIEL3.SA', 'CRFB3.SA',
    'PCAR3.SA', 'YDUQ3.SA', 'AZUL4.SA', 'SLCE3.SA', 'USIM5.SA', 'TAEE11.SA',
    'CYRE3.SA', 'COGN3.SA', 'BRKM5.SA', 'CMIN3.SA', 'GOAU4.SA', 'MRFG3.SA',
    'CVCB3.SA', 'IRBR3.SA', 'BEEF3.SA', 'RRRP3.SA', 'MRVE3.SA', 'EZTC3.SA',
    'PETZ3.SA', 'CASH3.SA', 'DXCO3.SA'
]

def update_ibov_db(days: int = 365) -> int:
    """
    Baixa dados históricos dos tickers do ibovespa e atualiza a coleção PRICES_COL.
    Retorna o número de documentos inseridos.
    """
    data_final = datetime.now()
    data_inicial = data_final - timedelta(days=days)
    print(f"Baixando dados de {data_inicial.date()} a {data_final.date()} para {len(tickers_ibov)} tickers.")
    data_final_str = data_final.strftime('%Y-%m-%d')
    data_inicial_str = data_inicial.strftime('%Y-%m-%d')

    dados_historicos_totais = pd.DataFrame()

    for i, ticker in enumerate(tickers_ibov):
        try:
            dados_acao = yf.download(ticker, start=data_inicial_str, end=data_final_str, progress=False)
            if not dados_acao.empty:
                dados_acao['Ticker'] = ticker.replace('.SA', '')
                dados_historicos_totais = pd.concat([dados_historicos_totais, dados_acao])
            # silencioso em caso de ausência de dados
        except Exception:
            # ignora falhas por ticker para tentar prosseguir com o restante
            continue

    if dados_historicos_totais.empty:
        return 0

    # Prepara o DataFrame: garante que 'Date' esteja como índice para operações de stack
    if 'Date' in dados_historicos_totais.columns:
        dados_historicos_totais = dados_historicos_totais.set_index('Date')

    # Se as colunas forem MultiIndex (formato wide com tickers em segundo nível),
    # empilha o segundo nível (ticker) para converter para formato long (rows = Date + Ticker)
    if isinstance(dados_historicos_totais.columns, pd.MultiIndex):
        if 'Ticker' in dados_historicos_totais.columns:
            dados_historicos_totais = dados_historicos_totais.drop(columns=['Ticker'])
        dados_historicos_totais = dados_historicos_totais.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index()
    else:
        if 'Date' not in dados_historicos_totais.columns:
            dados_historicos_totais = dados_historicos_totais.reset_index()

    # Colunas esperadas e normalização
    required = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    available = list(dados_historicos_totais.columns)
    missing = [c for c in required if c not in available]

    if 'Adj Close' in missing and 'Close' in available:
        dados_historicos_totais['Adj Close'] = dados_historicos_totais['Close']
        missing.remove('Adj Close')

    for c in missing:
        dados_historicos_totais[c] = pd.NA

    colunas_ordenadas = [c for c in required if c in dados_historicos_totais.columns]
    dados_historicos_totais = dados_historicos_totais[colunas_ordenadas]

    rename_map = {
        'Date': 'Data', 'Ticker': 'Ticker', 'Open': 'Abertura',
        'High': 'Maxima', 'Low': 'Minima', 'Close': 'Fechamento',
        'Adj Close': 'Fech_Ajustado', 'Volume': 'Volume'
    }
    dados_historicos_totais = dados_historicos_totais.rename(columns={k: v for k, v in rename_map.items() if k in dados_historicos_totais.columns})

    dados_para_inserir = dados_historicos_totais.to_dict('records')

    # Conecta ao MongoDB e insere os dados
    inserted = 0
    client = None
    try:
        client = get_client()
        collection = prices_col(client)

        # Limpa coleção e insere
        collection.delete_many({})
        if dados_para_inserir:
            res = collection.insert_many(dados_para_inserir)
            inserted = len(res.inserted_ids)
    finally:
        if client:
            client.close()

    return inserted

if __name__ == "__main__":
    inserted = update_ibov_db(days=30)
    print(f"Registros inseridos: {inserted}")