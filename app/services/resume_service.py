import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Union

from fastapi import UploadFile

from .. import ocr
from .. import llm_service
from ..config.constants import MAX_RETRIES, MAX_CONCURRENT_PROCESSES

async def _validate_file_content(file: UploadFile) -> dict:
    """Valida o conteúdo do arquivo de forma assíncrona."""
    filename = file.filename
    
    try:
        file.file.seek(0)
        file_bytes = await file.read()
        
        if not file_bytes:
            return {"filename": filename, "error": "Arquivo vazio."}
        
        return {"file_bytes": file_bytes, "filename": filename}
    
    except Exception as e:
        return {"filename": filename, "error": f"Erro ao ler arquivo: {str(e)}"}

async def _run_ocr(file_bytes: bytes, filename: str) -> Union[ocr.OcrResponse, ocr.OcrError]:
    """Executa OCR usando thread pool."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            ocr.extract_text_from_file, 
            file_bytes, 
            filename
        )

async def _run_llm_analysis(text: str, query: Optional[str]) -> Union[llm_service.AnalysisResponse, llm_service.AnalysisResponseNoQuery, llm_service.AnalysisError]:
    """Executa análise LLM usando thread pool."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            llm_service.get_llm_analysis, 
            text, 
            query
        )

async def _process_single_resume(file: UploadFile, query: Optional[str]) -> dict:
    """Processa um único currículo com retry automático."""
    filename = file.filename
    
    # Validações básicas
    validation_result = await _validate_file_content(file)
    if "error" in validation_result:
        return validation_result
    
    file_bytes = validation_result["file_bytes"]
    
    # OCR com retry
    for attempt in range(MAX_RETRIES):
        try:
            extracted_text = await _run_ocr(file_bytes, filename)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            else:
                return {"filename": filename, "error": f"Erro de OCR: {str(e)}"}
        
        if isinstance(extracted_text, ocr.OcrError):
            return {"filename": filename, "error": f"Erro de OCR: {extracted_text.error}"}

        # Análise do LLM
        try:
            analysis = await _run_llm_analysis(extracted_text.text, query)
        except Exception as e:
            return {"filename": filename, "error": f"Erro na análise de IA: {str(e)}"}
        
        if isinstance(analysis, llm_service.AnalysisError):
            return {"filename": filename, "error": f"Erro na análise de IA: {analysis.error}"}
        
        # Sucesso em ambas as operações
        return {
            "filename": filename,
            "score": analysis.score,
            "summary": analysis.summary
        }

    # Erro final
    return {"filename": filename, "error": "Não foi possível processar o currículo após os retries."}

async def process_resumes_concurrently(files: List[UploadFile], query: Optional[str]) -> List[dict]:
    """Processa os currículos."""
    
    # Semáforo para lidar com concorrências
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PROCESSES)
    
    async def process_with_semaphore(file: UploadFile) -> dict:
        async with semaphore:
            return await _process_single_resume(file, query)
    
    # Executa todos os processamentos de forma concorrente
    tasks = [process_with_semaphore(file) for file in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Processa os resultados e trata exceções
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "filename": files[i].filename,
                "error": f"Erro inesperado: {str(result)}"
            })
        else:
            processed_results.append(result)
    
    return processed_results 