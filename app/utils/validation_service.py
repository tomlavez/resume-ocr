import os
import base64
import logging
from groq import Groq
from pydantic import BaseModel, Field
from PIL import Image
import io

logger = logging.getLogger(__name__)

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

MAX_RETRIES = 3

class ValidationError(BaseModel):
    error: str = Field(..., description="Mensagem de erro na validação")

def validate_image_content(image_bytes: bytes, filename: str) -> bool | ValidationError:
    """
    Usa o modelo de visão da Groq para validar se a imagem contém um currículo.
    
    Args:
        image_bytes: Bytes da imagem
        
    Returns:
        bool ou ValidationError
    """
    try:
        # Converte bytes para PIL Image e depois para base64
        image = Image.open(io.BytesIO(image_bytes))
        
        # Converte para RGB se necessário (remove canal alpha)
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Converte para base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        system_prompt = """
        Você é um especialista em análise de documentos e identificação de currículos.
        Sua tarefa é analisar um texto e determinar se ele é um currículo/CV ou não.

        Avalie a estrutura do texto e as informações contidas nele.
        Certifique-se de que o texto é de fato um currículo/CV e não outro tipo de documento mascarado como currículo.

        Responda APENAS com:
        - True se o texto for de um currículo/CV
        - False caso o texto não seja de um currículo/CV
        """

        user_prompt = """
        Analise este texto e determine se é de um currículo/CV
        Certifique-se de que o texto é de fato um currículo/CV e não outro tipo de documento mascarado como currículo.
        O texto deve conter informações do tipo informações pessoais, experiência profissional, formação acadêmica, habilidades, competências e etc.
        Note que é possível encontrar outros tipos de documentos que possuam uma estrutura similar a um currículo/CV, mas que não sejam currículos/CVs.
        """

        for i in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.2,
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                )

                res = response.choices[0].message.content

                if "true" in res.lower() and "false" in res.lower():
                    continue

                if res.lower() == "false":
                    return False

                if "true" in res.lower():
                    return True

            except Exception as e:
                logger.warning(f"⚠️ Tentativa {i+1}/{MAX_RETRIES} falhou para validação de imagem {filename}")
                continue

        return False

    except Exception as e:
        logger.error(f"❌ Erro crítico na validação de imagem {filename}: {e}")
        return ValidationError(error=f"Erro ao processar imagem: {str(e)}")

def validate_text_content(text: str, filename: str) -> bool | ValidationError:
    """
    Usa o modelo de texto da Groq para validar se o texto é de um currículo.
    
    Args:
        text: Texto extraído do documento
        filename: Nome do arquivo
        
    Returns:
        ValidationResponse ou ValidationError
    """
    try:
        logger.debug(f"🔍 Iniciando validação de texto com IA: {filename}")
        
        system_prompt = """
        Você é um especialista em análise de documentos e identificação de currículos.
        Sua tarefa é analisar um texto e determinar se ele é um currículo/CV ou não.

        Avalie a estrutura do texto e as informações contidas nele.
        Certifique-se de que o texto é de fato um currículo/CV e não outro tipo de documento mascarado como currículo.

        Responda APENAS com:
        - True se o texto for de um currículo/CV
        - False caso o texto não seja de um currículo/CV
        """

        user_prompt = f"""
        Analise este texto e determine se é de um currículo/CV
        Certifique-se de que o texto é de fato um currículo/CV e não outro tipo de documento mascarado como currículo.
        O texto deve conter informações do tipo informações pessoais, experiência profissional, formação acadêmica, habilidades, competências e etc.
        Note que é possível encontrar outros tipos de documentos que possuam uma estrutura similar a um currículo/CV, mas que não sejam currículos/CVs.

        ---
        TEXTO:
        {text[:3000]}
        ---

        Responda APENAS com True ou False.
        True se o texto for de um currículo/CV
        False se o texto não for de um currículo/CV
        """

        for i in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                )

                res = response.choices[0].message.content

                if "true" in res.lower() and "false" in res.lower():
                    continue

                if res.lower() == "false":
                    return False

                if "true" in res.lower():
                    return True

            except Exception as e:
                logger.warning(f"⚠️ Tentativa {i+1}/{MAX_RETRIES} falhou para validação do PDF {filename}")
                continue

        return False

    except Exception as e:
        logger.error(f"❌ Erro crítico na validação de texto {filename}: {e}")
        return ValidationError(error=f"Erro ao processar texto: {str(e)}") 
