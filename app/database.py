import os
from datetime import datetime
from pymongo import MongoClient
from fastapi import HTTPException

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ ERRO: A variável de ambiente MONGO_URI não foi definida.")
    exit()

try:
    sync_client = MongoClient(MONGO_URI)
    sync_db = sync_client.techmatch_logs
    sync_log_collection = sync_db.requests
    
    print("✅ Conexão com o MongoDB (Motor e PyMongo) pronta para ser usada.")
except Exception as e:
    print(f"❌ Falha na configuração do cliente MongoDB: {e}")
    raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")

def log_request_sync(log_data: dict):
    """
    Insere um documento de log na coleção 'requests'.
    """
    try:
        log_data["timestamp"] = datetime.now()
        sync_log_collection.insert_one(log_data)
        print(f"-> Log da requisição '{log_data.get('request_id')}' salvo com sucesso.")
    except Exception as e:
        print(f"❌ ERRO ao salvar log síncrono no MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")
    
def get_analysis_by_request_id_sync(request_id: str) -> dict | None:
    """
    Busca um log de requisição pelo seu request_id.
    """
    try:
        result = sync_log_collection.find_one({"request_id": request_id}, {"_id": 0})
        return result
    except Exception as e:
        print(f"❌ ERRO ao buscar log síncrono no MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")