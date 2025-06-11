# ocr.py
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import fitz  # PyMuPDF
import io

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extrai texto de arquivos de forma inteligente.
    - Para imagens, usa OCR.
    - Para PDFs, tenta extração direta. Se falhar, usa OCR.
    """
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            image = Image.open(io.BytesIO(file_bytes))
            return pytesseract.image_to_string(image, lang='por+eng')
        except Exception as e:
            return f"Erro ao processar imagem com OCR: {e}"

    elif filename.lower().endswith('.pdf'):
        direct_text = ""
        try:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf_document:
                direct_text += page.get_text()
            pdf_document.close()
        except Exception as e:
            print(f"Extração direta com PyMuPDF falhou: {e}. Tentando OCR.")
            direct_text = ""
        
        if len(direct_text.strip()) > 200:
            return direct_text
            
        else:
            ocr_text = ""
            try:
                pages = convert_from_bytes(file_bytes)
                for i, page_image in enumerate(pages):
                    text = pytesseract.image_to_string(page_image, lang='por+eng')
                    ocr_text += f"\n--- Página {i+1} ---\n{text}"
                
                if not ocr_text.strip():
                     return "Alerta: O PDF parece ser uma imagem, mas o OCR não conseguiu extrair texto."
                return ocr_text
            except Exception as e:
                return f"Erro crítico no fallback de OCR para PDF: {e}"
    
    else:
        return "Erro: Tipo de arquivo não suportado. Use PDF, PNG, JPG ou JPEG."