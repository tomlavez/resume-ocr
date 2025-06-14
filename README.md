# TechMatch AI Resume Analyzer

Sistema assíncrono para análise automatizada de currículos usando IA e OCR.

## 🚀 Funcionalidades

- **Análise com Query**: Ranqueia currículos por adequação à vaga (0-10)
- **Análise sem Query**: Gera resumos identificando senioridade
- **Processamento Assíncrono**: Múltiplos arquivos simultaneamente
- **Formatos**: PDF, PNG, JPG, JPEG

## 📋 Pré-requisitos

- Docker
- Docker Compose
- Groq API Key

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/tomlavez/resume-ocr
cd resume-ocr
```

### 2. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
GROQ_API_KEY=your_groq_api_key_here
MONGO_URI=mongodb://mongo:27017/
```

### 3. Execute o sistema
```bash
sudo docker-compose up --build
```

O sistema estará disponível em: `http://127.0.0.1:8000`

Acesse: `http://127.0.0.1:8000/docs` para ver a documentação interativa.

## 🐳 Arquitetura Docker

O projeto utiliza dois serviços:

- **api**: Aplicação FastAPI (Python 3.10 + Tesseract OCR + Poppler)
- **mongo**: Banco de dados MongoDB para logs e auditoria

### Portas Expostas
- **8000**: API FastAPI
- **27017**: MongoDB (opcional para acesso externo)

### Volumes
- **Código**: Montado em `/app` para desenvolvimento
- **mongo-data**: Persistência dos dados do MongoDB

## 📡 API

### Endpoint Principal

```http
POST /analyze/
Host: 127.0.0.1:8000
Content-Type: multipart/form-data
```

### Parâmetros

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `request_id` | string | ✅ | UUID v4 único para identificar a requisição |
| `user_id` | string | ✅ | Identificador do usuário (máx. 50 caracteres) |
| `files` | file[ ] | ✅ | Lista de arquivos (PDF/PNG/JPG/JPEG) |
| `query` | string | ❌ | Descrição da vaga para ranqueamento (máx. 2500 chars) |

### Limites
- **Arquivos**: Máximo 20 por requisição
- **Tamanho**: Máximo 10MB por arquivo
- **Processamento**: 5 arquivos simultâneos (configurável)

## 🎯 Exemplos de Uso

### 1. 📄 Análise Individual (Sem Query)
**Cenário**: Gerar resumo geral identificando senioridade

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -F "request_id=f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -F "user_id=rh_empresa" \
  -F "files=@curriculo_desenvolvedor.pdf"
```

<details>
<summary>📋 Ver resposta esperada</summary>

```json
{
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "results": [
    {
      "filename": "curriculo_desenvolvedor.pdf",
      "score": "sênior",
      "summary": "Desenvolvedor full-stack com 8 anos de experiência em React, Node.js e AWS. Liderança técnica em projetos de grande escala."
    }
  ]
}
```
</details>

### 2. 🎯 Ranqueamento por Vaga (Com Query)
**Cenário**: Comparar múltiplos candidatos para vaga específica

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -F "request_id=f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -F "user_id=tech_recruiter" \
  -F "query=Desenvolvedor React Senior: TypeScript, Next.js, microservices, AWS, Docker, testes automatizados" \
  -F "files=@joao_silva.pdf" \
  -F "files=@maria_santos.pdf" \
  -F "files=@pedro_costa.pdf"
```

<details>
<summary>📋 Ver resposta esperada</summary>

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "results": [
    {
      "filename": "joao_silva.pdf",
      "score": 8.5,
      "summary": "Candidato ideal - 6 anos React, 4 anos TypeScript, experiência sólida em Next.js e AWS. Arquitetura de microservices."
    },
    {
      "filename": "maria_santos.pdf",
      "score": 7.2,
      "summary": "Boa adequação - 5 anos React, TypeScript intermediário, conhecimento em Docker e testes."
    },
    {
      "filename": "pedro_costa.pdf",
      "score": 6.2,
      "summary": "Alinhamento parcial - 3 anos React, conhecimento básico TypeScript, sem experiência AWS."
    }
  ]
}
```
</details>

### 3. 📁 Múltiplos Formatos
**Cenário**: Processar diferentes tipos de arquivo

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -F "request_id=f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -F "user_id=analista_rh" \
  -F "query=Desenvolvedor Python Django" \
  -F "files=@curriculo_digital.pdf" \
  -F "files=@curriculo_escaneado.jpg" \
  -F "files=@curriculo_foto.png"
```

## ⚙️ Configuração

### 🔧 Ajustar Performance

```python
# Máximo de arquivos processados simultaneamentes
MAX_CONCURRENT_PROCESSES = 5

# Máximo de retries para o OCR
MAX_RETRIES = 3

# Tamanho máximo de arquivo
MAX_FILE_SIZE = 10 * 1024 * 1024
```

## 🧪 Teste Rápido

```bash
# Documentação interativa
http://127.0.0.1:8000/docs

# Verificar se os serviços estão rodando
docker-compose ps

# Logs da aplicação
docker-compose logs api

# Logs do MongoDB
docker-compose logs mongo

# Teste básico
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -F "request_id=f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -F "user_id=teste" \
  -F "files=@exemplo.pdf"
```

## 🔧 Comandos Úteis

### 🐳 Gerenciamento de Containers

```bash
# Iniciar sistema
sudo docker-compose up --build

# Parar serviços
sudo docker-compose down
```

## 🚨 Limites

- **Arquivos**: Máx. 20 por requisição
- **Tamanho**: Máx. 10MB por arquivo
- **Formatos**: PDF, PNG, JPG, JPEG
- **Processamento**: 5 arquivos simultâneos (configurável)

## 📄 Licença

MIT License