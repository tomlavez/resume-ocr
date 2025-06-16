import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise HTTPException(status_code=500, detail="Internal Server Error: A variável de ambiente MONGO_URI não foi definida.")

try:
    async_client = AsyncIOMotorClient(MONGO_URI)
    async_db = async_client.techmatch_logs
    async_log_collection = async_db.requests
    
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")


async def check_database_connection() -> bool:
    """
    Verifica se a conexão com o banco de dados está funcionando.
    
    Returns:
        bool: True se a conexão estiver OK, False caso contrário
        
    Raises:
        HTTPException: Se houver erro crítico na conexão
    """
    try:
        # Tenta fazer um ping no servidor MongoDB
        await async_client.admin.command('ping')
        
        # Verifica se o banco de dados existe e está acessível
        db_names = await async_client.list_database_names()
        
        # Verifica se a coleção existe ou pode ser criada
        collections = await async_db.list_collection_names()
        
        return True
        
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: Banco de dados indisponível. Tente novamente mais tarde."
        )


async def get_database_dependency():
    """
    Dependência do FastAPI para verificar a conexão com o banco de dados.
    
    Esta função será usada como dependência nas rotas que precisam do banco.
    
    Returns:
        bool: True se a conexão estiver OK
        
    Raises:
        HTTPException: Se o banco estiver indisponível
    """
    return await check_database_connection()


async def log_request_async(log_data: dict):
    """
    Insere um documento de log na coleção 'requests'.
    """
    try:
        log_data["timestamp"] = datetime.now()
        await async_log_collection.insert_one(log_data)
        print(f"-> Log da requisição '{log_data.get('request_id')}' salvo com sucesso.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")
    

async def get_analysis_by_request_id_async(request_id: str) -> dict | None:
    """
    Busca um log de requisição pelo seu request_id.
    """
    try:
        result = await async_log_collection.find_one({"request_id": request_id}, {"_id": 0})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.")


async def close_database_connection():
    """
    Fecha a conexão com o banco de dados.
    
    Esta função deve ser chamada no shutdown da aplicação.
    """
    try:
        async_client.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: Erro ao fechar conexão com MongoDB. Tente novamente mais tarde.")