from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routers import analysis
from app.services.database_service import close_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI.
    
    Startup: Inicialização de recursos
    Shutdown: Limpeza de recursos
    """
    # Startup
    print("🚀 Iniciando TechMatch Resume Analyzer - versão 1.0.0")
    print("✅ Aplicação inicializada com sucesso")
    
    yield
    
    # Shutdown
    print("🔄 Encerrando aplicação...")
    await close_database_connection()
    print("✅ Aplicação encerrada com sucesso")


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

# Log de inicialização
print("🚀 TechMatch Resume Analyzer iniciado - versão 1.0.0")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 