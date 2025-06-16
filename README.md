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
- **Sistema de Logging**: Logs estruturados para monitoramento e debugging

## 🤖 Modelo de IA

Este projeto utiliza o modelo **llama3-8b-8192** da Groq para análise de currículos. 

> ⚠️ **Importante**: A troca do modelo pode causar variações significativas no desempenho e na qualidade das análises. O sistema foi otimizado especificamente para este modelo, incluindo os prompts de sistema e a estrutura de resposta esperada.

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

> **💡 Dica para Windows**: Não é necessário usar `sudo` no Windows.

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

### 💡 Dicas para o Parâmetro Query

O parâmetro `query` deve ser utilizado especificamente para análise de currículos e vagas. Para obter melhores resultados:

#### ✅ Boas Práticas
- **Seja específico sobre a posição**: Descreva claramente o cargo e requisitos
- **Foque no contexto profissional**: Mantenha a query relacionada a currículos e competências
- **Use a palavra "vaga"**: A inclusão da palavra "vaga" na sua query pode ajudar o modelo entender melhor o contexto

#### 📝 Exemplos

**❌ Evite queries genéricas:**
- "Qual o melhor candidato para devops?"
- "Quem tem mais experiência?"
- "Ranking de candidatos"

**✅ Use queries específicas e contextualizadas:**
- "Qual o melhor candidato para a vaga de devops com experiência em AWS?"
- "Ranking de candidatos para a vaga de desenvolvedor Python sênior"
- "Candidatos mais adequados para a vaga de analista de dados com conhecimento em SQL"

#### ⚠️ Evite
- Perguntas fora do contexto profissional
- Queries muito genéricas sem especificar a vaga
- Contextos que não sejam relacionados a análise de currículos

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
- **Processamento**: 3 arquivos simultâneos
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

## 📊 Sistema de Logging

O projeto implementa um sistema de logging para monitoramento, debugging e auditoria de operações.

### 🔧 Configuração

O sistema de logging está configurado no arquivo `app/config/logging_config.py` com as seguintes características:

- **Nível de Arquivo**: `DEBUG` (apenas para nossa aplicação)
- **Nível de Console**: `INFO` (informações importantes e acima)
- **Bibliotecas Externas**: `INFO+` (sem logs DEBUG de bibliotecas)
- **Rotação**: 10MB por arquivo, 5 backups automáticos
- **Formato**: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- **Encoding**: UTF-8


### 📁 Estrutura de Logs

```
projeto/
├── logs/
│   ├── app.log                  # Arquivo principal (até 10MB)
│   ├── app.log.1               # Backup 1
│   ├── app.log.2               # Backup 2
│   └── ...                     # Até 5 backups
├── app/
│   ├── config/
│   │   └── logging_config.py    # Configuração centralizada
│   ├── routers/
│   │   └── analysis.py          # Logs consolidados de requisições
│   └── services/
│       ├── ocr_service.py       # Logs de fallback OCR
│       ├── llm_service.py       # Logs de retry com contexto
│       └── database_service.py  # Logs críticos de conexão
├── main.py                      # Logs de lifecycle da aplicação
└── .gitignore                   # Exclui logs/ do versionamento
```

### 🏷️ Níveis de Log Utilizados

#### **DEBUG**
- 🔄 Fallbacks normais de OCR
- 🔝 Limitação de resultados
- 🔄 Início de processamento de arquivos
- 🔍 Informações detalhadas para debugging
- ❌ **Não inclui**: Logs DEBUG de bibliotecas externas

#### **INFO**
- 🚀 Lifecycle da aplicação (startup/shutdown com timing)
- 🎯 Requisições consolidadas (entrada única por request)
- 📊 Resultados com métricas de performance
- ✅ Finalizações bem-sucedidas com timing
- 📚 Informações importantes de bibliotecas externas

#### **WARNING**
- ⚠️ Validações rejeitadas
- ⚠️ Queries inválidas
- ⚠️ Arquivos com falha (consolidado)
- ⚠️ Tentativas de retry (com contexto)
- ⚠️ Timeouts de conexão

#### **ERROR**
- ❌ Falhas críticas de conexão
- ❌ Falha total no processamento
- ❌ APIs indisponíveis após retries
- ❌ Erros inesperados de banco

#### **CRITICAL**
- 💥 Configurações obrigatórias ausentes
- 💥 Falhas na inicialização da aplicação

### 🔍 Exemplos de Logs

#### Inicialização com Performance
```
2024-01-15 10:30:25 | __main__ | INFO | 🚀 Iniciando TechMatch Resume Analyzer v1.0.0
2024-01-15 10:30:25 | app.config.logging_config | INFO | 🔧 Sistema de logging configurado
2024-01-15 10:30:28 | __main__ | INFO | ✅ Aplicação inicializada com sucesso | Tempo: 3.24s
```

#### Requisição Consolidada
```
2024-01-15 10:35:10 | app.routers.analysis | INFO | 🎯 Nova requisição - ID: f47ac10b | User: rh_empresa | Arquivos: 3 | Query: Sim | DB: OK
2024-01-15 10:35:25 | app.routers.analysis | INFO | 📊 Processamento concluído - f47ac10b | Sucessos: 2 | Falhas: 1 | Tempo: 15.23s
2024-01-15 10:35:25 | app.routers.analysis | WARNING | ⚠️ Arquivos com falha - f47ac10b: curriculo_corrompido.pdf
2024-01-15 10:35:25 | app.routers.analysis | INFO | ✅ Requisição finalizada com sucesso - f47ac10b | Total: 15.45s
```

#### Retry com Contexto
```
2024-01-15 10:35:15 | app.services.llm_service | WARNING | ⚠️ Tentativa 1/3 falhou para análise de currículo: Connection timeout after 30s...
2024-01-15 10:35:20 | app.services.llm_service | WARNING | ⚠️ Tentativa 2/3 falhou para análise de currículo: Rate limit exceeded for current quota...
2024-01-15 10:35:25 | app.services.llm_service | ERROR | ❌ Todas as tentativas falharam para análise de currículo após 3 tentativas
```

#### Conexão de Banco Crítica
```
2024-01-15 10:30:20 | app.services.database_service | CRITICAL | 💥 MONGO_URI não encontrado nas variáveis de ambiente
2024-01-15 10:30:25 | app.services.database_service | WARNING | ⚠️ Timeout na conexão com MongoDB (5s)
2024-01-15 10:30:30 | app.services.database_service | ERROR | ❌ Banco de dados indisponível - aplicação funcionará sem persistência
```

### 📊 Métricas Incluídas

- **Tempo de Inicialização**: Startup completo da aplicação
- **Tempo de Processamento**: Por requisição completa
- **Tempo de Uptime**: Na finalização da aplicação
- **Contadores**: Sucessos/falhas por requisição
- **Retry Tracking**: Tentativas e contexto de falhas

### 🚀 Benefícios do Sistema

1. **Visibilidade Completa**: DEBUG no arquivo, INFO+ no console
2. **Performance Tracking**: Métricas de tempo para otimização
3. **Contexto Estruturado**: Cada log possui informações essenciais
4. **Rotação Automática**: Prevenção de logs gigantes
5. **Debugging Eficiente**: Informações precisas para troubleshooting
6. **Monitoramento Ready**: Logs estruturados para análise

### 📊 Monitoramento de Logs

#### Visualização em Tempo Real
```bash
# Logs completos
tail -f logs/app.log

# Apenas erros e warnings
tail -f logs/app.log | grep -E "(ERROR|WARNING|CRITICAL)"

# Performance de requisições
tail -f logs/app.log | grep "📊 Processamento concluído"

# Logs de DEBUG (apenas no arquivo)
tail -f logs/app.log | grep "DEBUG"
```

## 📄 Licença

MIT License