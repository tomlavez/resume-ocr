import uuid
from typing import List, Optional
from fastapi import HTTPException, UploadFile

from ..config.constants import (
    MAX_FILES, MAX_FILE_SIZE, MAX_USER_ID_LENGTH, 
    MAX_QUERY_LENGTH, ALLOWED_EXTENSIONS
)


def validate_form_inputs(request_id: str, user_id: str, query: Optional[str]):
    """Valida os campos de texto e UUID do formulário."""
    uuid_obj = uuid.UUID(request_id)
    if uuid_obj.version != 4:
        raise HTTPException(status_code=422, detail="UUID deve ser versão 4")

    if not user_id or not user_id.strip():
        raise HTTPException(status_code=422, detail="user_id não pode ser vazio.")
        
    if len(user_id) > MAX_USER_ID_LENGTH:
        raise HTTPException(status_code=422, detail=f"user_id muito longo. Máximo de {MAX_USER_ID_LENGTH} caracteres.")

    if query and len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=422, detail=f"query muito longa. Máximo de {MAX_QUERY_LENGTH} caracteres.")


def validate_file_list(files: List[UploadFile]):
    """Valida a lista de arquivos como um todo."""
    if not files:
        raise HTTPException(status_code=422, detail="Pelo menos um arquivo deve ser enviado.")
    
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=413, detail=f"Payload Too Large: O número máximo de arquivos é {MAX_FILES}.")

    for i, file in enumerate(files):
        if not file.filename or not file.filename.strip():
            raise HTTPException(status_code=422, detail="Um dos arquivos foi enviado sem nome.")
        
        if '.' not in file.filename:
            raise HTTPException(status_code=415, detail=f"Unsupported Media Type: O arquivo '{file.filename}' não possui extensão.")
        
        file_ext = '.' + file.filename.lower().rsplit('.', 1)[-1]
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail=f"Unsupported Media Type: O formato do arquivo '{file.filename}' não é suportado. Use PDF, PNG, JPG ou JPEG.")

        if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"Arquivo '{file.filename}' é muito grande. Máximo de {MAX_FILE_SIZE // (1024*1024)}MB.")


def get_score(candidate: dict) -> float:
    """Extrai a pontuação para ordenação."""
    try:
        score = candidate.get('score', 0.0)
        return float(score) if score is not None else 0.0
    except (ValueError, TypeError):
        return 0.0 
    