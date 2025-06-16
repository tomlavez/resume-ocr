from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
import time

from app.routers import analysis
from app.services.database_service import close_database_connection
from app.config.logging_config import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI.
    
    Startup: Inicialização de recursos
    Shutdown: Limpeza de recursos
    """
    # Startup
    start_time = time.time()
    logger.info("🚀 Iniciando TechMatch Resume Analyzer v1.0.0")
    
    try:
        # Aqui poderiam ser adicionadas validações de dependências
        logger.info("✅ Aplicação inicializada com sucesso")
    except Exception as e:
        logger.critical(f"❌ Falha crítica na inicialização: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Encerrando aplicação...")
    try:
        await close_database_connection()
        shutdown_time = time.time() - start_time
        logger.info(f"✅ Aplicação encerrada com sucesso - Uptime: {shutdown_time:.1f}s")
    except Exception as e:
        logger.error(f"❌ Erro durante encerramento: {e}")

# Criação da aplicação FastAPI
app = FastAPI(
    title="🎯 TechMatch Resume Analyzer",
    description="""
## Sistema de Análise de Currículos com IA

Analise currículos automaticamente usando OCR e Inteligência Artificial.

### Funcionalidades Principais:
- **Análise com Query**: Ranqueia currículos por adequação à vaga (0-10)
- **Análise sem Query**: Gera resumos identificando senioridade
- **Processamento Assíncrono**: Múltiplos arquivos simultaneamente
- **Múltiplos Formatos**: PDF, PNG, JPG, JPEG

### Limites Técnicos:
- **Arquivos**: Máximo 20 por requisição
- **Tamanho**: Máximo 10MB por arquivo
- **Processamento**: 5 arquivos simultâneos
- **Formatos**: PDF, PNG, JPG, JPEG
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Inclusão dos routers
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 