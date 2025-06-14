# Use uma imagem base oficial do Python.
FROM python:3.10-slim

# Instala dependências do sistema operacional, como o Tesseract OCR e o poppler (para PDFs).
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expõe a porta 8000, que é a porta que o Uvicorn usará.
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
