import pytesseract
import cv2
import numpy as np
import fitz
import io
import logging
from pdf2image import convert_from_bytes
from PIL import Image
from pydantic import BaseModel, Field
from ..utils import validation_service

logger = logging.getLogger(__name__)

class OcrError(BaseModel):
    error: str = Field(..., description="Mensagem de erro")

class OcrResponse(BaseModel):
    text: str = Field(..., description="Texto extraído do arquivo")

def extract_text_from_file(file_bytes: bytes, filename: str) -> OcrResponse | OcrError:

    # Se o arquivo for uma imagem, usa OCR.
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            logger.debug(f"🖼️ Iniciando preprocessamento de imagem: {filename}")
            
            # Validação de imagem com IA ANTES do OCR
            logger.debug(f"🤖 Iniciando validação de imagem com IA: {filename}")
            validation_result = validation_service.validate_image_content(file_bytes, filename)
            
            if isinstance(validation_result, validation_service.ValidationError):
                logger.warning(f"⚠️ Erro na validação da imagem {filename}: {validation_result.error}")
                # Continue com o processamento normal se a validação falhar
            elif not validation_result:
                logger.warning(f"⚠️ Imagem {filename} não é um currículo")
                return OcrError(error=f"Arquivo {filename} rejeitado, não é um currículo.")
            else:
                logger.debug(f"✅ Imagem validada pela IA - {filename}")
            
            # Pre processamento da imagem
            image = preprocess_image(file_bytes)
            text = pytesseract.image_to_string(image, lang='por+eng')
            
            return OcrResponse(text=text)
        except Exception as e:
            return OcrError(error=f"Erro ao processar imagem {filename} com OCR: {e}")

    # Se o arquivo for um PDF, tenta extrair texto diretamente.
    elif filename.lower().endswith('.pdf'):
        direct_text = ""
        try:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf_document:
                direct_text += page.get_text()
            pdf_document.close()
        except Exception as e:
            logger.debug(f"🔄 Extração direta de PDF falhou, usando OCR como fallback: {str(e)[:50]}...")
            direct_text = ""
        
        # Se o texto direto for maior que 200 caracteres, consideramos que é um PDF de texto.
        if len(direct_text.strip()) > 200:
            logger.debug(f"📄 PDF com texto extraído diretamente: {filename} ({len(direct_text)} chars)")
            
            # Validação de texto com IA
            logger.debug(f"🤖 Iniciando validação de texto com IA: {filename}")
            validation_result = validation_service.validate_text_content(direct_text, filename)
            
            if isinstance(validation_result, validation_service.ValidationError):
                logger.warning(f"⚠️ Arquivo {filename} rejeitado, não é um currículo: {validation_result.error}")
                return OcrError(error=f"Arquivo {filename} rejeitado, não é um currículo: {validation_result.error}")
            elif not validation_result:
                logger.warning(f"⚠️ Arquivo {filename} rejeitado, não é um currículo")
                return OcrError(error=f"Arquivo {filename} rejeitado, não é um currículo")
            else:
                logger.debug(f"✅ Currículo validado pela IA - {filename}")
            
            return OcrResponse(text=direct_text)
        
        # Se o texto direto for menor que 200 caracteres, consideramos que é um PDF de imagens.
        else:
            logger.debug(f"🖼️ PDF identificado como imagem, aplicando OCR com preprocessamento: {filename}")
            ocr_text = ""
            try:
                pages = convert_from_bytes(file_bytes)
                logger.debug(f"📄 Convertendo {len(pages)} páginas do PDF para imagens")
                
                # Validação da primeira página como imagem
                if len(pages) > 0:
                    first_page = pages[0]
                    img_buffer = io.BytesIO()
                    first_page.save(img_buffer, format='PNG')
                    img_bytes = img_buffer.getvalue()
                    
                for i, page_image in enumerate(pages):
                    # Converte a PIL Image para bytes para usar o preprocessamento
                    img_buffer = io.BytesIO()
                    page_image.save(img_buffer, format='PNG')
                    img_bytes = img_buffer.getvalue()
                    
                    # Validação da página com IA
                    logger.debug(f"🤖 Iniciando validação da página {i+1}/{len(pages)} com IA: {filename}")
                    validation_result = validation_service.validate_image_content(img_bytes, filename)
                    
                    # Se a página não for um currículo, para o loop
                    if isinstance(validation_result, validation_service.ValidationError):
                        logger.warning(f"⚠️ Erro na validação da página {i+1}/{len(pages)} - {filename}: {validation_result.error}")
                        return OcrError(error=f"Erro na validação da página {i+1}/{len(pages)} - {filename}: {validation_result.error}")
                    elif not validation_result:
                        logger.warning(f"⚠️ PDF {filename} não é um currículo")
                        return OcrError(error=f"Arquivo {filename} rejeitado, não é um currículo")
                    
                    # Aplica o mesmo preprocessamento usado para imagens diretas
                    logger.debug(f"🔧 Aplicando preprocessamento na página {i+1}/{len(pages)}")
                    processed_image = preprocess_image(img_bytes)

                    text = pytesseract.image_to_string(processed_image, lang='por+eng')
                    ocr_text += f"\n--- Página {i+1} ---\n{text}"
                
                if not ocr_text.strip():
                    return OcrError(error="Alerta: O PDF parece ser uma imagem, mas o OCR não conseguiu extrair texto.")
                logger.debug(f"✅ OCR concluído para PDF: {filename} ({len(pages)} páginas processadas)")
                return OcrResponse(text=ocr_text)
            except Exception as e:
                return OcrError(error=f"Erro crítico no fallback de OCR para PDF: {e}")
    
    else:
        return OcrError(error="Erro: Tipo de arquivo não suportado. Use PDF, PNG, JPG ou JPEG.")
    
def preprocess_image(image_bytes: bytes) -> Image:
    """Pre processa a imagem para otimização do OCR."""

    try:
        logger.debug("🔧 Iniciando preprocessamento: carregamento da imagem")
        # Carrega a imagem
        imagem = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(imagem, cv2.IMREAD_COLOR)

        # Converte para escala de cinza
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        logger.debug("🔧 Preprocessamento: conversão para escala de cinza")
        
        # Redução de ruído
        denoised_image = cv2.medianBlur(gray_image, 3)
        logger.debug("🔧 Preprocessamento: redução de ruído aplicada")

        # Binarização
        processed_image = cv2.adaptiveThreshold(denoised_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        logger.debug("🔧 Preprocessamento: binarização adaptativa aplicada")

        success, buffer = cv2.imencode('.png', processed_image)
        if not success:
            raise OcrError(error="Erro ao processar a imagem.")
        
        final_image = Image.open(io.BytesIO(buffer))
        logger.debug("✅ Preprocessamento concluído com sucesso")

        return final_image
    
    except Exception as e:
        logger.warning(f"⚠️ Falha no preprocessamento, usando imagem original")
        return Image.open(io.BytesIO(image_bytes))
    