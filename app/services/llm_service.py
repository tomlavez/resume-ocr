import os
import time
from groq import Groq
from pydantic import BaseModel, Field

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
        Você é um Analista de Talentos de IA altamente especializado. Sua função é realizar uma análise técnica e detalhada de um único currículo em relação a uma requisição de vaga ou perfil profissional.
        
        Você deve avaliar o alinhamento de um candidato (representado por seu currículo) com uma requisição específica, gerando uma pontuação (score), uma análise detalhada e observações pertinentes. Sua análise deve ser objetiva e estritamente baseada nos dados fornecidos.
        
        Metodologia de Análise (Passo a Passo):
            1. **Interpretar a Requisição:**
                * **Se a requisição for detalhada (descrição de vaga):** Identifique e liste todos os requisitos-chave: tecnologias, frameworks, linguagens, anos de experiência, certificações e outras competências.
                * **Se a requisição for simples ou genérica (ex: "Backend", "Frontend Pleno", "Analista de Dados"):** Infira os requisitos essenciais para esse perfil.
                    * *Exemplo para "Backend":* Você deve procurar por linguagens (Java, Python, C#, Node.js), bancos de dados (SQL, NoSQL), conhecimento em APIs (REST, GraphQL), arquitetura de sistemas (microsserviços) e cloud (AWS, Azure, GCP).
                    * *Exemplo para "Qual o melhor candidato para a vaga de devops":* Trate isso como uma requisição por um perfil "DevOps" ideal e analise o currículo em relação a esse perfil (ferramentas de CI/CD, IaC como Terraform, contêineres como Docker/Kubernetes, scripting).

            2.  **Analisar o Currículo:** Examine o texto completo do currículo para encontrar evidências diretas e indiretas que correspondam aos requisitos identificados no passo 1. Preste atenção especial aos anos de experiência com cada tecnologia e ao contexto dos projetos descritos.

            3.  **Gerar a Análise:** Com base na comparação, construa o feedback. A pontuação deve refletir o alinhamento geral, e o resumo deve explicar o porquê dessa pontuação, detalhando os pontos fortes e as lacunas do candidato.

        Critérios de Pontuação (Score):
            * **8.0 - 10.0 (Alinhamento Forte):** O candidato atende a todos ou quase todos os requisitos essenciais da requisição. A experiência e as habilidades descritas são altamente relevantes.
            * **6.0 - 7.9 (Alinhamento Bom):** O candidato atende à maioria dos requisitos importantes, mas possui algumas lacunas em tecnologias secundárias ou no tempo de experiência. É um candidato promissor.
            * **4.0 - 5.9 (Alinhamento Razoável):** O candidato possui algumas das habilidades requeridas, mas falta conhecimento em pontos cruciais da requisição. Pode ser considerado para vagas de menor senioridade ou com treinamento.
            * **0.0 - 3.9 (Alinhamento Baixo):** O candidato atende a poucos ou nenhum dos requisitos essenciais. O perfil não é compatível com a requisição.

        Formato da Saída:
        A sua resposta deve seguir extritamente a estrutura abaixo:
        
            Feedback:
                Score: (float, de 0.0 a 10.0). O quanto o candidato está alinhado com a requisição.
                Resumo: (string). Um resumo detalhado sobre a adequação do candidato. Considerar as tecnologias, frameworks, linguagens de programação, etc. da requisição e como o candidato se alinha com elas. Inclua informações sobre anos de experiência, projetos relevantes, habilidades técnicas e outras competências que sejam pertinentes à requisição. Aqui você deve explicar os pontos fortes e fracos do candidato, deixando claro o que faltou para que o candidato fosse considerado ideal para a requisição.
            
            Extra_comments:
                Insira aqui qualquer extra_comment que você quiser adicionar sobre o currículo.

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
            Resumo: (string, um resumo detalhado sobre o perfil profissional, experiências relevantes, competências técnicas e nível de senioridade do candidato)
        
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

            if len(summary) < 10:
                continue  # Resumo muito curto, tentar novamente

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

def validate_query(query: str) -> bool:
    """
    Valida a query para garantir que ela seja adequada para análise.

    Parâmetros:
        query: string a ser validada

    Retorna:
        bool: True se a query for válida, False caso contrário
    """

    system_prompt = f"""
    Você é um Validador de Requisições para um sistema de Recrutamento e Seleção. Sua única função é analisar uma requisição (query) e determinar se ela é apropriada para o contexto de análise e triagem de currículos.

    O sistema receberá esta requisição para buscar, classificar, comparar ou avaliar candidatos com base nas informações exclusivamente contidas em seus currículos. Você é o filtro de entrada que impede que requisições fora de contexto sejam processadas.

    Uma requisição é considerada valida (True) se:
    1.  Busca por Fatos: Pergunta sobre habilidades, tecnologias, experiências, formação ou certificações específicas (ex: "Liste os candidatos com certificação PMP").
    2.  Descrição de Vaga É uma descrição de um perfil profissional desejado, mesmo que complexa (ex: "Procuro desenvolvedor front-end pleno com React e TypeScript").
    3.  Análise Comparativa ou Avaliativa Pede uma classificação, comparação ou avaliação baseada nos dados dos currículos. Isso inclui perguntas com termos como "melhor", "mais qualificado", "mais sênior" ou "mais indicado" pois a resposta exige uma síntese e análise das qualificações profissionais.

    Uma requisição é considerada invalida (False) se:
    1.  Conhecimento Geral: É uma pergunta sobre fatos ou temas não relacionados a um currículo (ex: "Qual a capital da França?", "Quem é o presidente atual?").
    2.  Opinião Pessoal Não Profissional: Faz perguntas subjetivas que não podem ser respondidas com dados de um currículo (ex: "Qual candidato parece mais simpático?", "Qual deles tem o nome mais bonito?").
    3.  Comando Genérico: É uma ordem para a IA executar uma tarefa não relacionada à análise de currículos (ex: "Escreva um e-mail", "Calcule 15*3").

    # Importante:
        - "Quem é o melhor candidato frontend?" -> Esta pergunta exige uma análise profissional dos currículos, comparando anos de experiência, tecnologias dominadas, projetos realizados, etc.
        - "Quem parece ser o candidato mais simpático?" -> Esta pergunta exige uma opinião pessoal, impossível de ser determinada por um currículo.
    A principal diferença é que a primeira busca uma análise a respeito de aspectos do currículo (Frontend) mesmo pedindo o 'melhor' candidato, enquanto a segunda busca uma opinião pessoal (simpático) que não pode ser extraída de um currículo.
        
    Note que você também pode receber apenas uma lista de areas de conhecimento, tecnologias ou habilidades, como "Backend", "Frontend", "DevOps", "Django, Flask, FastAPI", "Java, Python, Go", "AWS, Azure, GCP", "Docker, Kubernetes", "SQL, NoSQL", "Machine Learning, Data Science". Essas listas são válidas pois serão usadas para buscar candidatos com essas habilidades específicas.

    Se a query for válida, retorne True. Se não for válida, retorne False.
    """

    user_prompt = f"""
    Você receberá uma query. Sua função é validar se essa query é adequada para análise de currículos.

    ---
    QUERY:
    "{query}"
    ---

    Se a query for válida, retorne True. Se não for válida, retorne False.
    """

    for i in range(MAX_RETRIES):

        time.sleep(0.5 * (i + 1))  # Atraso exponencial para evitar sobrecarga
        
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

            if "true" in res.lower() and "false" in res.lower():
                continue

            if "true" in res.lower():
                return True
            
            elif "false" in res.lower():
                return False            

        except Exception as e:
            print(f"Erro ao contatar o serviço da Groq: {e}")
            continue

    return False  