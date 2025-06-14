import os
import json
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

MAX_RETRIES = 3

class AnalysisResponse(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0, description="Pontuação de 0.0 a 10.0")
    summary: str = Field(..., min_length=10, max_length=2000, description="Resumo da análise")

class AnalysisResponseNoQuery(BaseModel):
    score: str = Field(..., description="Senioridade do candidato")
    summary: str = Field(..., description="Resumo da análise")

class AnalysisError(BaseModel):
    error: str = Field(..., description="Mensagem de erro")

def get_llm_analysis(resume_text: str, query: str = None) -> AnalysisResponse | AnalysisError:
    """
    Envia o texto de um currículo para o LLM da Groq para obter uma análise detalhada e uma pontuação.
    Se query for fornecida, analisa em relação à vaga. Caso contrário, faz um resumo geral.

    Parâmetros:
        resume_text: texto do currículo
        query: texto da vaga (opcional)

    Retorna:
        feedback: dicionário com score e summary
    """
    
    system_prompt = "Você é um recrutador técnico sênior e especialista em análise de currículos."
    
    if query:
        # Modo análise com vaga específica
        user_prompt = f"""
        Você receberá uma requisição a respeito de um currículo. Essa requisição conterá informações sobre tecnologias, frameworks, linguagens de programação, etc.
        A sua função é analisar o currículo em relação a requisição e fornecer um score e um resumo sobre o alinhamento do currículo com a requisição.
        
        Feedback:
            Score: (float, de 0.0 a 10.0). O quanto o candidato está alinhado com a requisição.
            Resumo: (string). Um resumo curto sobre a adequação do candidato. Considerar as tecnologias, frameworks, linguagens de programação, etc. da requisição e como o candidato se alinha com elas.
        
        Extra_comments:
            Insira aqui qualquer extra_comment que você quiser adicionar sobre o currículo.

        Para a 'score', use o seguinte critério:
        - 8.0 a 10.0: Alinhamento ideal, atende a quase todas as tecnologias, frameworks, linguagens de programação, etc. da requisição.
        - 6.0 a 7.9: Bom alinhamento, atende a uma quantidade significativa das tecnologias, frameworks, linguagens de programação, etc. da requisição, mas falta algumas.
        - 4.0 a 5.9: Alinhamento razoável, atende a algumas, mas não a todas as tecnologias, frameworks, linguagens de programação, etc. da requisição.
        - 0.0 a 3.9: Não está alinhado com a requisição. Atende a poucas ou nenhuma tecnologia, framework, linguagem de programação, etc. da requisição.

        ---
        DESCRIÇÃO DA REQUISIÇÃO:
        "{query}"
        ---
        TEXTO DO CURRÍCULO:
        "{resume_text}"
        ---

        Lembre-se, siga a estrutura de feedback, com score e resumo, e extra_comments. Tenha em mente que caso mude essa estrutura iremos encontrar erros e o resumo não será aceito.
        """

    else:
        # Modo resumo geral do currículo
        user_prompt = f"""
        Faça um resumo analítico do currículo fornecido.
        Sua resposta deve seguir a seguinte estrutura:

        Feedback:
            Score: (string, senioridade do candidato, pode ser júnior, pleno ou sênior)
            Resumo: (string, um resumo sobre o perfil profissional, experiências relevantes, competências técnicas e nível de senioridade do candidato)
        
        Extra comments:
            Insira aqui qualquer extra_comment sobre pontos fortes, áreas de especialização ou observações relevantes do currículo.

        ---
        TEXTO DO CURRÍCULO:
        "{resume_text}"
        ---

        Lembre-se, siga a estrutura de feedback, com score e resumo, e extra_comments. Tenha em mente que caso mude essa estrutura iremos encontrar erros e o resumo não será aceito.
        """

    for i in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
            )

            res = response.choices[0].message.content
            
            # Normalização da resposta
            res = res.replace("*", "")
            extra_comments = "Extra_comments" if "Extra_comments" in res else "Extra comments"
            feedback = "Feedback" if "Feedback" in res else "feedback"
            score = "Score" if "Score" in res else "score"
            resumo = "Resumo" if "Resumo" in res else "resumo"

            analysis_json = res.split(feedback)[1].split(extra_comments)[0].strip()
            score = analysis_json.split(score)[1].split("\n")[0].strip()
            summary = analysis_json.split(resumo)[1].split("\n")[0].strip()

            if "/" in score:
                score = score.split("/")[0].strip()

            # Se começar com : remove
            if score.startswith(":"):
                score = score[1:].strip()
            if summary.startswith(":"):
                summary = summary[1:].strip()

            # Converte score para float
            if query:
                data = AnalysisResponse(score=float(score), summary=summary)
            else:
                data = AnalysisResponseNoQuery(score=score, summary=summary)

            return data
        except Exception as e:
            print(f"Erro ao contatar o serviço da Groq: {e}")
            continue
