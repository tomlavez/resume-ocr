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