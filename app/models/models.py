from typing import List, Union
from pydantic import BaseModel, Field

class ResumeResult(BaseModel):
    """Resultado da análise de um currículo individual."""
    filename: str = Field(..., description="Nome do arquivo processado", example="joao_silva.pdf")
    score: Union[float, str] = Field(..., description="Pontuação 0-10 (com query) ou nível de senioridade (sem query)", examples=[8.5, "sênior"])
    summary: str = Field(..., description="Resumo detalhado da análise do candidato", example="Desenvolvedor full-stack com 8 anos de experiência em React, Node.js e AWS. Liderança técnica em projetos de grande escala.")


class AnalysisResponse(BaseModel):
    """Resposta completa da análise de currículos."""
    request_id: str = Field(..., description="UUID v4 da requisição", example="f47ac10b-58cc-4372-a567-0e02b2c3d479")
    results: List[ResumeResult] = Field(..., description="Lista de currículos analisados com sucesso")
