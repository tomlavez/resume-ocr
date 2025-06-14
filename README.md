# TechMatch AI Resume Analyzer

Sistema assíncrono para análise automatizada de currículos usando IA e OCR.

## 💡 Motivação do Projeto

Este projeto foi desenvolvido como resposta ao desafio técnico descrito no documento **teste_back_ia.pdf**, que propõe a criação de um sistema inteligente para análise automatizada de currículos. O objetivo é demonstrar competências em:

- **Desenvolvimento Backend**: APIs REST com FastAPI
- **Inteligência Artificial**: Integração com modelos de linguagem (LLM)
- **Processamento de Documentos**: OCR e análise de texto
- **Containerização**: Deploy com Docker e orquestração de serviços

A solução implementa todos os requisitos técnicos solicitados, oferecendo uma API robusta para análise e ranqueamento de currículos com base em descrições de vagas.

## 🚀 Funcionalidades

- **Análise com Query**: Ranqueia currículos por adequação à vaga (0-10)
- **Análise sem Query**: Gera resumos identificando senioridade
- **Processamento Assíncrono**: Múltiplos arquivos simultaneamente
- **Formatos Suportados**: PDF, PNG, JPG, JPEG

## 📋 Pré-requisitos

- Docker
- Docker Compose
- Groq API Key

## 🛠️ Instalação e Execução

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

### 4. Acesse a aplicação
- **API**: http://127.0.0.1:8000
- **Documentação**: http://127.0.0.1:8000/docs

## 📡 Como Usar

### Endpoint Principal
```http
POST /analyze/
Content-Type: multipart/form-data
```

### Parâmetros Obrigatórios
- `request_id`: UUID v4 único
- `user_id`: Identificador do usuário (máx. 50 chars)
- `files`: Arquivos de currículo (PDF/PNG/JPG/JPEG)

### Parâmetro Opcional
- `query`: Descrição da vaga para ranqueamento (máx. 2500 chars)

### Exemplo Básico
```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -F "request_id=f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -F "user_id=rh_empresa" \
  -F "files=@/caminho/para/seu/arquivo.pdf"
```

### Exemplo com Query (Múltiplos Arquivos)
```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -F "request_id=550e8400-e29b-41d4-a716-446655440001" \
  -F "user_id=seu_usuario" \
  -F "query=Desenvolvedor Python com experiência em APIs" \
  -F "files=@/caminho/para/seu/arquivo1.pdf" \
  -F "files=@/caminho/para/seu/arquivo2.pdf" \
  -F "files=@/caminho/para/seu/arquivo3.pdf"
```

### Dicas para Arquivos
- **Símbolo @**: Obrigatório antes do caminho do arquivo
- **Caminhos absolutos**: `@/caminho/completo/arquivo.pdf`
- **Espaços no nome**: Use aspas: `@"./Meus Documentos/currículo.pdf"`
- **Múltiplos arquivos**: Repita `-F "files=@caminho"` para cada arquivo

## ⚙️ Limites do Sistema

- **Arquivos**: Máximo 20 por requisição
- **Tamanho**: Máximo 10MB por arquivo
- **Processamento**: 5 arquivos simultâneos
- **Formatos**: PDF, PNG, JPG, JPEG apenas

## 🔧 Comandos Úteis

```bash
# Verificar status dos serviços
docker-compose ps

# Ver logs da aplicação
docker-compose logs api

# Parar os serviços
docker-compose down

# Reiniciar com rebuild
sudo docker-compose up --build
```

## 📄 Licença

MIT License