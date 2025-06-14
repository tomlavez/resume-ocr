"""Constantes de configuração do sistema."""

# Limites de arquivos
MAX_FILES = 20 # Máximo de 20 arquivos por requisição
MAX_FILE_SIZE = 10 * 1024 * 1024  # Máximo de 10MB por arquivo

# Limites de campos
MAX_USER_ID_LENGTH = 50 # User ID máximo de 50 caracteres
MAX_QUERY_LENGTH = 2500 # Query máximo de 2500 caracteres

# Configurações de processamento
MAX_RETRIES = 3 # Máximo de 3 retentativas no OCR
MAX_CONCURRENT_PROCESSES = 5 # Máximo de 5 processos concorrentes

# Extensões permitidas
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'} 