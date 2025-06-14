import uuid
import time
import asyncio

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Union
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field

import app.ocr as ocr
import app.llm_service as llm_service
import app.database as database

class ResumeResult(BaseModel):
    """Resultado da análise de um currículo individual."""
    filename: str = Field(..., description="Nome do arquivo processado", example="joao_silva.pdf")
    score: Union[float, str] = Field(..., description="Pontuação 0-10 (com query) ou nível de senioridade (sem query)", examples=[8.5, "sênior"])
    summary: str = Field(..., description="Resumo detalhado da análise do candidato", example="Desenvolvedor full-stack com 8 anos de experiência em React, Node.js e AWS. Liderança técnica em projetos de grande escala.")

class AnalysisResponse(BaseModel):
    """Resposta completa da análise de currículos."""
    request_id: str = Field(..., description="UUID v4 da requisição", example="f47ac10b-58cc-4372-a567-0e02b2c3d479")
    results: List[ResumeResult] = Field(..., description="Lista de currículos analisados com sucesso")

class ErrorDetail(BaseModel):
    """Detalhes de erro para falhas de processamento."""
    message: str = Field(..., description="Mensagem de erro principal")
    failed_files: List[str] = Field(..., description="Lista de arquivos que falharam no processamento")
    request_id: str = Field(..., description="UUID da requisição que falhou")

class ValidationError(BaseModel):
    """Erro de validação de entrada."""
    detail: str = Field(..., description="Descrição detalhada do erro de validação", 
                       examples=[
                           "request_id deve ser um UUID v4 válido.",
                           "user_id não pode ser vazio.",
                           "user_id muito longo. Máximo de 50 caracteres.",
                           "query muito longa. Máximo de 2500 caracteres.",
                           "Pelo menos um arquivo deve ser enviado.",
                           "Um dos arquivos foi enviado sem nome."
                       ])

class PayloadTooLargeError(BaseModel):
    """Erro de payload muito grande."""
    detail: str = Field(..., description="Descrição do erro de tamanho", 
                       examples=[
                           "Payload Too Large: O número máximo de arquivos é 20.",
                           "Arquivo 'curriculo_grande.pdf' é muito grande. Máximo de 10MB.",
                           "Payload Too Large: Tamanho total da requisição excede o limite permitido."
                       ])

class UnsupportedMediaTypeError(BaseModel):
    """Erro de tipo de arquivo não suportado."""
    detail: str = Field(..., description="Descrição do erro de formato", 
                       examples=[
                           "Unsupported Media Type: O formato do arquivo 'curriculo.docx' não é suportado. Use PDF, PNG, JPG ou JPEG.",
                           "Unsupported Media Type: O arquivo 'curriculo' não possui extensão.",
                           "Unsupported Media Type: O formato do arquivo 'curriculo.txt' não é suportado. Use PDF, PNG, JPG ou JPEG."
                       ])

class ProcessingFailureError(BaseModel):
    """Erro de falha total no processamento."""
    detail: ErrorDetail = Field(..., description="Detalhes da falha de processamento")

class InternalServerError(BaseModel):
    """Erro interno do servidor."""
    detail: str = Field(..., description="Descrição do erro interno", 
                       examples=[
                           "Internal Server Error: Erro inesperado no servidor. Tente novamente mais tarde.",
                           "Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde.",
                           "Internal Server Error: Serviço de OCR indisponível. Tente novamente mais tarde.",
                           "Internal Server Error: Serviço de IA indisponível. Tente novamente mais tarde.",
                           "Internal Server Error: Timeout no processamento. Reduza o número de arquivos ou tente novamente."
                       ])

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
)

print("🚀 TechMatch Resume Analyzer iniciado - versão 1.0.0")

MAX_FILES = 20
MAX_USER_ID_LENGTH = 50
MAX_QUERY_LENGTH = 2500
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_RETRIES = 3
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
MAX_CONCURRENT_PROCESSES = 5 

def validate_form_inputs(request_id: str, user_id: str, query: Optional[str]):
    """Valida os campos de texto e UUID do formulário."""
    try:
        uuid_obj = uuid.UUID(request_id)
        if uuid_obj.version != 4:
            raise ValueError("UUID deve ser versão 4")
    except ValueError:
        raise HTTPException(status_code=422, detail="request_id deve ser um UUID v4 válido.")

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
    """Executa OCR de forma assíncrona usando thread pool."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            ocr.extract_text_from_file, 
            file_bytes, 
            filename
        )

async def _run_llm_analysis(text: str, query: Optional[str]) -> Union[llm_service.AnalysisResponse, llm_service.AnalysisResponseNoQuery, llm_service.AnalysisError]:
    """Executa análise LLM de forma assíncrona usando thread pool."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            llm_service.get_llm_analysis, 
            text, 
            query
        )

async def _process_single_resume(file: UploadFile, query: Optional[str]) -> dict:
    """Processa um único currículo de forma assíncrona com retry automático."""
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
    """Processa os currículos de forma assíncrona e concorrente com limite de concorrência."""
    
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

def safe_get_score(candidate: dict) -> float:
    """Extrai a pontuação de forma segura para ordenação."""
    try:
        score = candidate.get('score', 0.0)
        return float(score) if score is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

# --- Endpoint Único e Validado ---
@app.post(
    "/analyze/", 
    summary="Analisa Currículos com IA",
    description="""
## Análise Inteligente de Currículos

Processa um ou múltiplos currículos usando OCR e IA para extrair informações relevantes.

### Modos de Operação:

#### **Sem Query** (Análise Geral)
- Gera resumo identificando senioridade do candidato
- Score retornado como string: "júnior", "pleno", "sênior"

#### **Com Query** (Análise Direcionada)  
- Ranqueia candidatos por adequação à vaga específica
- Score retornado como float de 0.0 a 10.0
- Resultados ordenados por pontuação (maior para menor)
    """,
    response_model=AnalysisResponse,
    responses={
        200: {
            "description": "Análise realizada com sucesso",
            "content": {
                "application/json": {
                    "examples": {
                        "analise_sem_query": {
                            "summary": "Análise Geral (Sem Query)",
                            "description": "Exemplo de resposta para análise sem uma query específica",
                            "value": {
                                "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                                "results": [
                                    {
                                        "filename": "nicolas_azevedo.png",
                                        "score": "Senior",
                                        "summary": "Nicolas Azevedo é um arquiteto de software sênior com 15 anos de experiência, especializado em desenhar e implementar soluções complexas, seguras e otimizadas para a nuvem. Possui certificações em AWS e Azure e áreas de especialização em arquitetura de microserviços e serverless, estratégias de migração para nuvem, governança e otimização de custos, segurança e compliance em nuvem e arquitetura orientada a eventos. Com uma carreira consolidada em empresas como Accenture e Telefénica Vivo, Nicolas demonstra uma grande experiência em liderança e gestão de projetos."
                                    },
                                    {
                                        "filename": "fernanda_lima.pdf",
                                        "score": "Pleno",
                                        "summary": "Fernanda Lima é uma desenvolvedora frontend com 4 anos de experiência em criação de interfaces de usuário reativas, performáticas e acessíveis. Ela tem um foco em componentização com React e melhoria da experiência do usuário (UX). Com experiência em empresas como Fintech Neon e Startup Voo Livre, Fernanda demonstra habilidades em desenvolvimento de aplicativos em React.js e TypeScript, colaboração em design systems, implementação de testes e otimização de performance e SEO."
                                    },
                                ]
                            }
                        },
                        "analise_com_query": {
                            "summary": "Análise Direcionada (Com Query)",
                            "description": "Exemplo de resposta para análise com uma query específica de vaga",
                            "value": {
                                "request_id": "550e8400-e29b-41d4-a716-446655440001",
                                "results": [
                                    {
                                        "filename": "tatiana_guedes.pdf",
                                        "score": 6.5,
                                        "summary": "O currículo de Tatiana Guedes apresenta uma boa alinhamento com a requisição, especialmente em relação às habilidades em bancos de dados relacionais e otimização de performance. No entanto, falta experiência direta com o ecossistema de Big Data, serviços de dados da AWS e ferramentas de orquestração como Apache Airflow."
                                    },
                                    {
                                        "filename": "nicolas_azevedo.png",
                                        "score": 6.4,
                                        "summary": "O currículo de Nicolas Azevedo apresenta uma boa alinhamento com a requisição, especialmente em relação à experiência com AWS, arquitetura de soluções e governança de custos. No entanto, falta experiência direta com ferramentas de orquestração como Apache Airflow e processamento de dados com Python ou Scala. Além disso, a falta de experiência com Big Data e serviços de dados da AWS (S3, Glue, EMR, Redshift) é um ponto negativo."
                                    },
                                    {
                                        "filename": "fernanda_lima.pdf",
                                        "score": 2.5,
                                        "summary": "O currículo não apresenta alinhamento com a requisição, pois o candidato tem experiência em desenvolvimento frontend e não em engenharia de dados. A falta de experiência em Python, Scala, Apache Airflow, Apache Spark, AWS e SQL é significativa."
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "❌ Erro de Request - Dados inválidos ou malformados",
            "content": {
                "application/json": {
                    "examples": {
                        "request_malformado": {
                            "summary": "Request malformado",
                            "description": "Quando o request não está no formato correto (ex: JSON inválido, form-data malformado)",
                            "value": {
                                "detail": "Bad Request: Request malformado ou dados inválidos."
                            }
                        },
                        "multipart_invalido": {
                            "summary": "Multipart/form-data inválido",
                            "description": "Quando o formato multipart/form-data está corrompido ou incompleto",
                            "value": {
                                "detail": "Bad Request: Formato multipart/form-data inválido."
                            }
                        }
                    }
                }
            }
        },
        413: {
            "description": "❌ Payload muito grande - Limites de tamanho excedidos",
            "content": {
                "application/json": {
                    "examples": {
                        "muitos_arquivos": {
                            "summary": "Muitos arquivos enviados",
                            "description": "Enviados mais de 20 arquivos na requisição",
                            "value": {
                                "detail": "Payload Too Large: O número máximo de arquivos é 20."
                            }
                        },
                        "arquivo_muito_grande": {
                            "summary": "Arquivo individual muito grande",
                            "description": "Um arquivo específico excede o limite de 10MB",
                            "value": {
                                "detail": "Arquivo 'curriculo_grande.pdf' é muito grande. Máximo de 10MB."
                            }
                        },
                        "payload_total_grande": {
                            "summary": "Payload total muito grande",
                            "description": "O tamanho total da requisição excede os limites do servidor",
                            "value": {
                                "detail": "Payload Too Large: Tamanho total da requisição excede o limite permitido."
                            }
                        }
                    }
                }
            }
        },
        415: {
            "description": "❌ Formato não suportado - Tipo de arquivo inválido", 
            "content": {
                "application/json": {
                    "examples": {
                        "formato_nao_suportado": {
                            "summary": "Formato de arquivo não suportado",
                            "description": "Arquivo com extensão não permitida (apenas PDF, PNG, JPG, JPEG são aceitos)",
                            "value": {
                                "detail": "Unsupported Media Type: O formato do arquivo 'curriculo.docx' não é suportado. Use PDF, PNG, JPG ou JPEG."
                            }
                        },
                        "arquivo_sem_extensao": {
                            "summary": "Arquivo sem extensão",
                            "description": "Arquivo enviado sem extensão no nome",
                            "value": {
                                "detail": "Unsupported Media Type: O arquivo 'curriculo' não possui extensão."
                            }
                        },
                        "extensao_desconhecida": {
                            "summary": "Extensão desconhecida",
                            "description": "Arquivo com extensão não reconhecida pelo sistema",
                            "value": {
                                "detail": "Unsupported Media Type: O formato do arquivo 'curriculo.txt' não é suportado. Use PDF, PNG, JPG ou JPEG."
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "❌ Erros de Validação e Processamento",
            "content": {
                "application/json": {
                    "examples": {
                        "uuid_invalido": {
                            "summary": "request_id inválido",
                            "description": "UUID fornecido não é válido ou não é versão 4",
                            "value": {
                                "detail": "request_id deve ser um UUID v4 válido."
                            }
                        },
                        "user_id_vazio": {
                            "summary": "user_id vazio",
                            "description": "Campo user_id não foi preenchido ou contém apenas espaços",
                            "value": {
                                "detail": "user_id não pode ser vazio."
                            }
                        },
                        "user_id_muito_longo": {
                            "summary": "user_id muito longo",
                            "description": "Campo user_id excede o limite de 50 caracteres",
                            "value": {
                                        "detail": [
                                            {
                                            "type": "string_too_long",
                                            "loc": [
                                                "body",
                                                "user_id"
                                            ],
                                            "msg": "String should have at most 50 characters",
                                            "input": "012345678901234567890123456789012345678901234567890",
                                            "ctx": {
                                                "max_length": 50
                                            }
                                            }
                                        ]
                                    }
                        },
                        "query_muito_longa": {
                            "summary": "query muito longa",
                            "description": "Campo query excede o limite de 2500 caracteres",
                            "value": {
                                "detail": [
                                    {
                                    "type": "string_too_long",
                                    "loc": [
                                        "body",
                                        "query"
                                    ],
                                    "msg": "String should have at most 2500 characters",
                                    "input": "Input string",
                                    "ctx": {
                                        "max_length": 2500
                                    }
                                    }
                                ]
                            }
                        },
                        "arquivo_sem_nome": {
                            "summary": "Arquivo sem nome",
                            "description": "Um dos arquivos foi enviado sem nome de arquivo",
                            "value": {
                                "detail": "Um dos arquivos foi enviado sem nome."
                            }
                        },
                        "falha_total_processamento": {
                            "summary": "Falha total no processamento",
                            "description": "Nenhum arquivo pôde ser processado com sucesso após todas as tentativas",
                            "value": {
                                "detail": {
                                    "message": "Nenhum currículo pôde ser processado com sucesso após 3 tentativas.",
                                    "failed_files": [
                                        "curriculo_corrompido.pdf", 
                                        "arquivo_vazio.pdf",
                                        "imagem_ilegivel.png"
                                    ],
                                    "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
                                }
                            }
                        },
                        "campos_obrigatorios": {
                            "summary": "Campos obrigatórios ausentes",
                            "description": "Um ou mais campos obrigatórios não foram fornecidos",
                            "value": {
                                "detail": [
                                    {
                                        "type": "missing",
                                        "loc": ["body", "request_id"],
                                        "msg": "Field required",
                                        "input": None
                                    },
                                    {
                                        "type": "missing", 
                                        "loc": ["body", "user_id"],
                                        "msg": "Field required",
                                        "input": None
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "❌ Erro interno do servidor",
            "content": {
                "application/json": {
                    "examples": {
                        "erro_interno_generico": {
                            "summary": "Erro interno genérico",
                            "description": "Erro inesperado no servidor durante o processamento",
                            "value": {
                                "detail": "Internal Server Error: Erro inesperado no servidor. Tente novamente mais tarde."
                            }
                        },
                        "erro_banco_dados": {
                            "summary": "Erro de banco de dados",
                            "description": "Falha ao conectar ou gravar no banco de dados",
                            "value": {
                                "detail": "Internal Server Error: Erro ao acessar banco de dados. Tente novamente mais tarde."
                            }
                        },
                        "erro_servico_ocr": {
                            "summary": "Erro no serviço de OCR",
                            "description": "Falha crítica no sistema de OCR",
                            "value": {
                                "detail": "Internal Server Error: Serviço de OCR indisponível. Tente novamente mais tarde."
                            }
                        },
                        "erro_servico_ai": {
                            "summary": "Erro no serviço de IA",
                            "description": "Falha crítica no sistema de análise de IA",
                            "value": {
                                "detail": "Internal Server Error: Serviço de IA indisponível. Tente novamente mais tarde."
                            }
                        },
                        "timeout_processamento": {
                            "summary": "Timeout no processamento",
                            "description": "Processamento excedeu o tempo limite permitido",
                            "value": {
                                "detail": "Internal Server Error: Timeout no processamento. Reduza o número de arquivos ou tente novamente."
                            }
                        }
                    }
                }
            }
        }
    },
    tags=["Análise de Currículos"]
)
async def analyze_resumes(
    request_id: str = Form(
        ..., 
        description="**UUID v4 único** para identificar esta requisição",
        example="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    ),
    user_id: str = Form(
        ..., 
        description="**Identificador do usuário** solicitante (máx. 50 caracteres)",
        example="recrutador_tech_01",
        max_length=MAX_USER_ID_LENGTH
    ),
    files: List[UploadFile] = File(
        ..., 
        description="**Lista de currículos** para análise (PDF, PNG, JPG, JPEG - máx. 10MB cada, 20 arquivos total)",
    ),
    query: Optional[str] = Form(
        None, 
        description="""**Query opcional** para análise direcionada:
        
**Sem Query**: Gera resumo geral identificando senioridade
**Com Query**: Ranqueia candidatos por adequação à vaga (0-10)
        """,
        example="Desenvolvedor React Senior: TypeScript, Next.js, microservices, AWS, Docker, testes automatizados, liderança técnica",
        max_length=MAX_QUERY_LENGTH
    )
):
    """
    ## Análise Inteligente de Currículos

    Processa currículos usando **OCR + IA** para extrair informações relevantes e gerar insights.

    ### 📋 **Parâmetros:**
    - **request_id**: UUID v4 único para rastreamento
    - **user_id**: Identificador do usuário (máx. 50 chars)  
    - **files**: Currículos em PDF/PNG/JPG/JPEG (máx. 20 arquivos, 10MB cada)
    - **query**: Opcional - descrição da vaga para ranqueamento

    ### 🔄 **Comportamento:**
    - **Sem Query**: Análise geral → Score como string ("júnior", "pleno", "sênior")
    - **Com Query**: Análise direcionada → Score numérico (0.0-10.0) + ordenação

    ### ⚡ **Performance:**
    - Processamento assíncrono e concorrente
    - Retry automático para falhas temporárias
    - Limite de 5 arquivos simultâneos

    ### 📊 **Retorno:**
    - **200**: Pelo menos 1 arquivo processado com sucesso
    - **422**: Nenhum arquivo pôde ser processado (falha total)
    """
    print(f"\n🎯 Nova requisição recebida - ID: {request_id}")
    print(f"👤 Usuário: {user_id}")
    print(f"📊 Query: {query if query else 'Nenhuma'}")
    print(f"📁 Arquivos: {len(files)}")
    
    # 1. Validação das entradas
    validate_form_inputs(request_id, user_id, query)
    validate_file_list(files)

    # Normaliza a query (remove espaços e converte string vazia para None)
    query = query.strip() if query else None
    if query == "":
        query = None

    # 2. Processamento assíncrono e concorrente dos arquivos com retry
    all_results = await process_resumes_concurrently(files, query)
    
    # 3. Separação dos resultados
    successful_results = [res for res in all_results if "error" not in res]
    failed_results = [res for res in all_results if "error" in res]
    
    print(f"📈 Resultados: {len(successful_results)} sucessos, {len(failed_results)} falhas")

    # 4. Verificação se pelo menos um arquivo foi processado com sucesso
    if not successful_results:
        print(f"💥 Falha total - nenhum arquivo processado com sucesso")
        
        # Log da falha no banco de dados
        log_entry = {
            "request_id": request_id, 
            "user_id": user_id,
            "query": query, 
            "resultado": "falha_total"
        }
        print(f"💾 Salvando log de falha total no banco")
        database.log_request_sync(log_entry)
        
        failed_filenames = [res["filename"] for res in failed_results]
        raise HTTPException(
            status_code=422, 
            detail={
                "message": f"Nenhum currículo pôde ser processado com sucesso após {MAX_RETRIES} tentativas.", 
                "failed_files": failed_filenames,
                "request_id": request_id
            }
        )

    # 5. Preparação da Resposta Final
    if query:
        print(f"🔢 Ordenando resultados por pontuação (query presente)")
        # Ordena apenas quando há query para ranqueamento
        sorted_results = sorted(successful_results, key=safe_get_score, reverse=True)
        final_response = {
            "request_id": request_id,
            "results": sorted_results
        }
    else:
        print(f"📋 Mantendo ordem original (sem query)")

        # Mantém ordem original quando não há query
        final_response = {
            "request_id": request_id,
            "results": successful_results
        }
    
    # 6. Log no Banco de Dados
    log_entry = {
        "request_id": request_id, 
        "user_id": user_id,
        "query": query, 
        "resultado": final_response["results"]
    }
    
    database.log_request_sync(log_entry)

    print(f"✅ Requisição {request_id} finalizada com sucesso\n")
    return final_response
