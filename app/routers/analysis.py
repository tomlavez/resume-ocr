"""Router para análise de currículos."""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from ..models.models import AnalysisResponse
from ..config.constants import MAX_USER_ID_LENGTH, MAX_QUERY_LENGTH, MAX_RETRIES
from ..utils.utils import validate_form_inputs, validate_file_list, get_score
from ..services.resume_service import process_resumes_concurrently
from ..database import get_database_dependency, log_request_async, check_database_connection
from ..llm_service import validate_query

router = APIRouter(prefix="/analyze", tags=["Análise de Currículos"])


@router.post(
    "/", 
    summary="Analisa Currículos com IA",
    description="""
## Análise Inteligente de Currículos

Processa um ou múltiplos currículos usando OCR e IA para extrair informações relevantes.

## Como Usar

### Formato da Requisição
- **Content-Type**: `multipart/form-data`
- **Método**: `POST`
- **Endpoint**: `/analyze/`

### Campos Obrigatórios
- `request_id`: UUID v4 único para identificar a requisição
- `user_id`: Identificador do usuário (máx. 50 caracteres)
- `files`: Lista de arquivos de currículos

### Campos Opcionais
- `query`: Descrição do perfil para análise direcionada (máx. 2500 caracteres)

## Modos de Operação

### **Análise Geral** (Sem Query)
- Identifica automaticamente a senioridade do candidato
- **Score**: String ("Júnior", "Pleno", "Sênior")
- **Summary**: Resumo do currículo

### **Análise Direcionada** (Com Query)  
- Ranqueia candidatos por adequação à requisição específica
- **Score**: Float de 0.0 a 10.0 (maior pontuação = melhor adequação)
- **Summary**: Resumo do currículo com base na requisição
- **Limite**: Retorna até os 5 melhores candidatos

## Limites e Restrições

### Arquivos
- **Formatos aceitos**: PDF, PNG, JPG, JPEG
- **Tamanho máximo por arquivo**: 10MB
- **Número máximo de arquivos**: 20 por requisição

## Exemplos de Requisição

### Exemplo 1: Análise Geral (form-data)
```
POST /analyze/
Content-Type: multipart/form-data

request_id: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
user_id: "fabio"
files: [curriculo1.pdf, curriculo2.png]
```

### Exemplo 2: Análise Direcionada (form-data)
```
POST /analyze/
Content-Type: multipart/form-data

request_id: "550e8400-e29b-41d4-a716-446655440001"
user_id: "fabio"
query: "Desenvolvedor React Senior: TypeScript, Next.js, microservices, AWS"
files: [curriculo1.pdf, curriculo2.png, curriculo3.jpg]
```

### Exemplo 3: cURL
```bash
curl -X POST "http://localhost:8000/analyze/" \
  -H "Content-Type: multipart/form-data" \
  -F "request_id=f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -F "user_id=recrutador_tech_01" \
  -F "query=Desenvolvedor Python Senior com experiência em FastAPI" \
  -F "files=@./path/to/curriculo1.pdf" \
  -F "files=@./path/to/curriculo2.png"
```
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
            "description": "Erro de Request - Dados inválidos ou malformados",
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
        405: {
            "description": "Método não permitido",
            "content": {
                "application/json": {
                    "examples": {
                        "metodo_nao_permitido": {
                            "summary": "Método não permitido",
                            "description": "Método HTTP não permitido para a requisição. Requisição deve ser feita via POST.",
                            "value": {
                                "detail": "Method Not Allowed."
                            }
                        }
                    }
                }
            }
        },
        413: {
            "description": "Payload muito grande - Limites de tamanho excedidos",
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
            "description": "Formato não suportado - Tipo de arquivo inválido", 
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
            "description": "Erros de Validação e Processamento",
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
                        "query_inválida": {
                            "summary": "Query inválida",
                            "description": "A query fornecida não é relevante para análise de currículo, sendo considerada ou fora do escopo ou voltada para uma análise pessoal e não técnica.",
                            "value": {
                                "detail": "Query inválida. Por favor forneça uma query relevante para uma análise de currículo."
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
            "description": "Erro interno do servidor",
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
        },
        503: {
            "description": "Serviço indisponível - Banco de dados inacessível",
            "content": {
                "application/json": {
                    "examples": {
                        "banco_indisponivel": {
                            "summary": "Banco de dados indisponível",
                            "description": "Falha na conexão ou verificação do banco de dados",
                            "value": {
                                "detail": "Service Unavailable: Banco de dados indisponível. Tente novamente mais tarde."
                            }
                        }
                    }
                }
            }
        }
    }
)
async def analyze_resumes(
    request_id: str = Form(
        ..., 
        description="""
**UUID v4 único para identificar esta requisição**

- **Formato**: UUID versão 4 (ex: `f47ac10b-58cc-4372-a567-0e02b2c3d479`)
- **Obrigatório**: Sim
- **Validação**: Deve ser um UUID v4 válido
- **Uso**: Rastreamento de logs e identificação única da requisição
        """,
        example="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    ),
    user_id: str = Form(
        ..., 
        description="""
**Identificador do usuário solicitante**

- **Formato**: String alfanumérica (ex: `recrutador_tech_01`)
- **Limite**: Máximo 50 caracteres
- **Obrigatório**: Sim
- **Validação**: Não pode ser vazio ou conter apenas espaços
- **Uso**: Identificação do usuário para logs e auditoria
        """,
        example="recrutador_tech_01",
        max_length=MAX_USER_ID_LENGTH
    ),
    files: List[UploadFile] = File(
        ..., 
        description="""
**Lista de currículos para análise**

- **Formatos aceitos**: PDF, PNG, JPG, JPEG
- **Tamanho máximo por arquivo**: 10MB
- **Número máximo**: 20 arquivos por requisição
- **Obrigatório**: Sim (mínimo 1 arquivo)
        """,
    ),
    query: Optional[str] = Form(
        default=None, 
        description="""
**Query opcional para análise direcionada**

- **Formato**: Texto livre descrevendo a vaga/requisitos
- **Limite**: Máximo 2500 caracteres
- **Obrigatório**: Não
- **Comportamento**:
  - **Sem query**: Análise geral identificando senioridade ("Júnior", "Pleno", "Sênior")
  - **Com query**: Ranqueamento por adequação à vaga (score 0.0-10.0, retorna top 5)
- **Exemplo**: Desenvolvedor React Senior: TypeScript, Next.js, microservices, AWS, Docker, testes automatizados, liderança técnica
        """,
        example="Desenvolvedor React Senior: TypeScript, Next.js, microservices, AWS, Docker, testes automatizados, liderança técnica",
        max_length=MAX_QUERY_LENGTH
    ),
    db_available: bool = Depends(get_database_dependency)
):
    print(f"\n🎯 Nova requisição recebida - ID: {request_id}")
    print(f"👤 Usuário: {user_id}")
    print(f"📊 Query: {query if query else 'Nenhuma'}")
    print(f"📁 Arquivos: {len(files)}")
    print(f"🗄️ Status do banco: {'Disponível' if db_available else 'Indisponível'}")
    
    # Validação das entradas
    validate_form_inputs(request_id, user_id, query)
    validate_file_list(files)

    query = query.strip() if query else None
    if query == "":
        query = None

    # Valida a query se fornecida
    if query:
        flag = validate_query(query)
        if not flag:
            raise HTTPException(
                status_code=422, 
                detail="Query inválida. Por favor forneça uma query relevante para uma análise de currículo."
            )

    # Processamento dos arquivos
    all_results = await process_resumes_concurrently(files, query)
    
    # Formatação dos resultados
    successful_results = [res for res in all_results if "error" not in res]
    failed_results = [res for res in all_results if "error" in res]
    
    print(f"📈 Resultados: {len(successful_results)} sucessos, {len(failed_results)} falhas")

    if not successful_results:
        print(f"💥 Falha total - nenhum arquivo processado com sucesso")
        
        # Log da falha no banco de dados
        log_entry = {
            "request_id": request_id, 
            "user_id": user_id,
            "query": query, 
            "resultado": "falha_total"
        }
        await log_request_async(log_entry)
        
        failed_filenames = [res["filename"] for res in failed_results]
        raise HTTPException(
            status_code=422, 
            detail={
                "message": f"Nenhum currículo pôde ser processado com sucesso após {MAX_RETRIES} tentativas.", 
                "failed_files": failed_filenames,
                "request_id": request_id
            }
        )

    if query:
        sorted_results = sorted(successful_results, key=get_score, reverse=True)
        if len(sorted_results) > 5:
            sorted_results = sorted_results[:5]
            
        final_response = {
            "request_id": request_id,
            "results": sorted_results
        }
    else:
        final_response = {
            "request_id": request_id,
            "results": successful_results
        }
    
    # Log no Banco de Dados
    log_entry = {
        "request_id": request_id, 
        "user_id": user_id,
        "query": query, 
        "resultado": final_response["results"]
    }
    
    await log_request_async(log_entry)

    print(f"✅ Requisição {request_id} finalizada com sucesso\n")
    return final_response 