import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    logger.critical("❌ MONGO_URI não encontrada nas variáveis de ambiente")
    raise ValueError("MONGO_URI não encontrada nas variáveis de ambiente")

# Cliente assíncrono
async_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)
async_database = async_client["resume_analyzer"]
async_log_collection = async_database["requests"]

async def check_database_connection() -> bool:
    """
    Verifica se o MongoDB está acessível.
    
    Returns:
        bool: True se a conexão for bem-sucedida, False caso contrário.
    """
    try:
        # Tenta executar um comando simples para testar a conexão
        await async_client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        logger.warning("⚠️ MongoDB não acessível - timeout na conexão")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao conectar com MongoDB: {e}")
        return False

async def get_database_dependency():
    """
    Verifica se o banco de dados está disponível.
    
    Esta função é usada como dependência do FastAPI.
    
    Returns:
        bool: Status da conexão do banco de dados
        
    Raises:
        HTTPException: Se o banco estiver indisponível
    """
    db_status = await check_database_connection()
    if not db_status:
        logger.error("🔴 Banco de dados indisponível - requisições serão rejeitadas")
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: Banco de dados indisponível. Tente novamente mais tarde."
        )
    return db_status

async def log_request_async(log_data: dict):
    """
    Insere um documento de log na coleção 'requests'.
    """
    try:
        log_data["timestamp"] = datetime.now()
        await async_log_collection.insert_one(log_data)
    except Exception as e:
        logger.error(f"❌ Falha ao salvar log no banco - request_id: {log_data.get('request_id')}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")
    

async def get_analysis_by_request_id_async(request_id: str) -> dict | None:
    """
    Busca um log de requisição pelo seu request_id.
    """
    try:
        result = await async_log_collection.find_one({"request_id": request_id}, {"_id": 0})
        if not result:
            logger.debug(f"🔍 Nenhum log encontrado para request_id: {request_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Erro ao buscar log do banco - request_id: {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")


async def close_database_connection():
    """
    Fecha a conexão com o banco de dados.
    
    Esta função deve ser chamada no shutdown da aplicação.
    """
    try:
        async_client.close()
        logger.info("🔌 Conexão com MongoDB fechada")
    except Exception as e:
        logger.error(f"❌ Erro ao fechar conexão com MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao fechar conexão com MongoDB. Tente novamente mais tarde.")