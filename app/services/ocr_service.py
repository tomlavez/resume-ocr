import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import fitz
import io
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class OcrError(BaseModel):
    error: str = Field(..., description="Mensagem de erro")

class OcrResponse(BaseModel):
    text: str = Field(..., description="Texto extraído do arquivo")

def extract_text_from_file(file_bytes: bytes, filename: str) -> OcrResponse | OcrError:

    # Se o arquivo for uma imagem, usa OCR.
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            image = Image.open(io.BytesIO(file_bytes))
            return OcrResponse(text=pytesseract.image_to_string(image, lang='por+eng'))
        except Exception as e:
            return OcrError(error=f"Erro ao processar imagem com OCR: {e}")

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
            return OcrResponse(text=direct_text)
        
        # Se o texto direto for menor que 200 caracteres, consideramos que é um PDF de imagens.
        else:
            ocr_text = ""
            try:
                pages = convert_from_bytes(file_bytes)
                for i, page_image in enumerate(pages):
                    text = pytesseract.image_to_string(page_image, lang='por+eng')
                    ocr_text += f"\n--- Página {i+1} ---\n{text}"
                
                if not ocr_text.strip():
                    return OcrError(error="Alerta: O PDF parece ser uma imagem, mas o OCR não conseguiu extrair texto.")
                return OcrResponse(text=ocr_text)
            except Exception as e:
                return OcrError(error=f"Erro crítico no fallback de OCR para PDF: {e}")
    
    else:
        return OcrError(error="Erro: Tipo de arquivo não suportado. Use PDF, PNG, JPG ou JPEG.")
    