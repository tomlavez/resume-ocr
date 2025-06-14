# Use uma imagem base oficial do Python.
FROM python:3.10-slim

# Instala dependências do sistema operacional, como o Tesseract OCR e o poppler (para PDFs).
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container.
WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker.
COPY requirements.txt .

# Instala as dependências Python.
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código da sua aplicação para o diretório de trabalho.
COPY . .

# Expõe a porta 8000, que é a porta que o Uvicorn usará.
EXPOSE 8000

# O comando que será executado quando o container iniciar.
# O --host 0.0.0.0 é crucial para que a API seja acessível de fora do container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
