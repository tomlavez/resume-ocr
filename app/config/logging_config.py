import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging():
    """
    Configura o sistema de logging da aplicação
    """
    # Cria diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuração do formato
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Remove handlers existentes para evitar duplicação
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Configuração básica
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[]
    )
    
    # Handler para arquivo com rotação
    file_handler = logging.handlers.RotatingFileHandler(
        filename="logs/app.log",
        maxBytes=10*1024*1024,  # Max 10MB por arquivo
        backupCount=5,          # Mantém 5 arquivos de backup
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Adiciona handlers ao logger raiz
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log inicial do sistema
    logger = logging.getLogger(__name__)
    logger.info("🔧 Sistema de logging configurado")
    
    return True 