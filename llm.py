import os
import json
from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

MAX_RETRIES = 3

def get_llm_analysis(resume_text: str, query: str = None) -> str:
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
        Analise o currículo fornecido em relação aos requisitos da vaga descrita abaixo.
        Sua resposta deve seguir exatamente a seguinte estrutura:

        feedback:
            score: (float, de 0.0 a 10.0)
            summary: (string, um resumo curto sobre a adequação do candidato. Considerar as competencias obrigatórias e desejáveis da vaga, as competencias ausentes e os pontos fortes e a desenvolver do candidato.)
        
        extra_comments:
            Insira aqui qualquer comentário adicional que você quiser adicionar sobre o currículo.

        Para a 'score', use o seguinte critério:
        - 8.0 a 10.0: Candidato ideal, atende a quase todos os requisitos obrigatórios e a vários desejáveis.
        - 6.0 a 7.9: Bom candidato, atende aos requisitos obrigatórios, mas falta alguns desejáveis.
        - 4.0 a 5.9: Candidato com potencial, atende a alguns, mas não a todos os requisitos obrigatórios.
        - 0.0 a 3.9: Não parece ser um bom candidato para a vaga.

        ---
        DESCRIÇÃO DA VAGA:
        "{query}"
        ---
        TEXTO DO CURRÍCULO:
        "{resume_text}"
        ---
        """

    else:
        # Modo resumo geral do currículo
        user_prompt = f"""
        Faça um resumo analítico do currículo fornecido.
        Sua resposta deve seguir a seguinte estrutura:

        feedback:
            score: (string, senioridade do candidato, pode ser júnior, pleno ou sênior)
            summary: (string, um resumo sobre o perfil profissional, experiências relevantes, competências técnicas e nível de senioridade do candidato)
        
        extra_comments:
            Insira aqui qualquer comentário adicional sobre pontos fortes, áreas de especialização ou observações relevantes do currículo.

        ---
        TEXTO DO CURRÍCULO:
        "{resume_text}"
        ---
        """

    for i in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
            )

            res = response.choices[0].message.content

            # Extrai o texto após análise: e antes de comentarios adicionais:
            analysis_json = res.split("feedback:")[1].split("extra_comments:")[0]

            return analysis_json
        except Exception as e:
            continue

    return "score: 0.0 \nsummary: Erro ao contatar o serviço da Groq."
    