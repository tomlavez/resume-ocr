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
- **Validação**: Validação com IA para garantir que arquivos são currículos
- **OCR**: Preprocessamento de imagens para melhor qualidade
- **Sistema de Logging**: Logs estruturados para monitoramento e debugging

## 📁 Estrutura do Repositório

```
resume-ocr/
├── app/                         # Código principal da aplicação
│   ├── config/                  # Configurações da aplicação
│   │  ├── constants.py          # Constantes e configurações gerais
│   │  └── logging_config.py     # Configuração do sistema de logs
│   ├── models/                  # Modelos de dados e schemas
│   │  └── models.py             # Definições Pydantic para validação
│   ├── routers/                 # Rotas e endpoints da API
│   │  └── analysis.py           # Endpoint principal para análise
│   ├── services/                # Serviços principais do sistema
│   │  ├── analyze_service.py    # Orquestração das análises
│   │  ├── database_service.py   # Operações com MongoDB
│   │  ├── llm_service.py        # Integração com modelos de IA
│   │  └── ocr_service.py        # Processamento OCR e extração
│   └── utils/                   # Utilitários e helpers
│      ├── utils.py              # Funções auxiliares gerais
│      └── validation_service.py # Validação de conteúdo com IA
└── logs/                        # Logs da aplicação (gerado em runtime)
├── tests/                       # Arquivos para testes
│   ├── curriculos/              # Currículos de exemplo para testes
│   └── vagas/                   # Descrições de vagas para testes
├── .env.example                 # Exemplo de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
├── docker-compose.yml           # Orquestração de serviços
├── Dockerfile                   # Configuração para containerização
├── main.py                      # Ponto de entrada da aplicação
├── README.md                    # Documentação principal do projeto
├── requirements.txt             # Dependências Python
├── teste back ia.pdf            # Documento de especificação do desafio
```

## 🔍 Processamento OCR

O sistema implementa um pipeline de OCR com preprocessamento automático para maximizar a qualidade da extração de texto:

### 📄 Estratégia por Tipo de Arquivo

#### **PDFs**
1. **Extração Direta**: Primeiro tenta extrair texto nativo do PDF
2. **Validação com IA**: Verifica se o texto extraído é de um currículo válido
3. **Detecção Automática**: Se o texto extraído for < 200 caracteres, identifica como PDF de imagem
4. **OCR com Preprocessamento**: Converte páginas para imagem e aplica preprocessamento
5. **Validação por Página**: Cada página é validada individualmente pela IA

#### **Imagens** (PNG, JPG, JPEG)
1. **Validação Visual com IA**: Análise inteligente para confirmar que é um currículo
2. **Preprocessamento Automático**: Otimizações antes do OCR

### 🔧 Pipeline de Preprocessamento

O preprocessamento é aplicado automaticamente em:
- **Imagens diretas**: PNG, JPG, JPEG
- **PDFs de imagem**: PDFs que contêm imagens escaneadas (com validação por página)

#### Etapas do Preprocessamento:
1. **Conversão para Escala de Cinza**: Melhora contraste e reduz ruído
2. **Redução de Ruído**: Filtro Mediano (3x3) para preservar bordas
3. **Binarização Adaptativa**: Threshold automático para cada região da imagem
4. **Fallback**: Se o preprocessamento falhar, usa a imagem original

## 🤖 Modelo de IA

Este projeto utiliza dois modelos especializados da Groq para diferentes funções:

### 📊 **Análise de Currículos**
- **Modelo**: `llama3-8b-8192`
- **Função**: Análise detalhada e ranqueamento de currículos
- **Uso**: Geração de resumos e pontuação de adequação à vaga

### 🔍 **Validação de Conteúdo**
- **Modelo**: `meta-llama/llama-4-scout-17b-16e-instruct`
- **Função**: Validação se documentos são currículos válidos
- **Uso**: Filtragem inteligente antes do processamento

> ⚠️ **Importante**: A troca dos modelos pode causar variações significativas no desempenho e na qualidade das análises. O sistema foi otimizado especificamente para estes modelos, incluindo os prompts de sistema e a estrutura de resposta esperada.

## 🤖 Validação de Conteúdo com IA

O sistema implementa uma camada de validação usando IA para garantir que apenas currículos válidos sejam processados:

### 🔍 Como Funciona

#### **Para Imagens** (PNG, JPG, JPEG)
1. **Análise Visual**: Modelo de visão analisa a estrutura visual do documento
2. **Identificação de Padrões**: Detecta elementos típicos de currículos (seções, layout, formatação)
3. **Validação de Conteúdo**: Verifica se contém informações relevantes a currículos

#### **Para PDFs**
- **Texto Direto**: Analisa o texto extraído diretamente do PDF
- **PDF de Imagem**: Valida cada página convertida para imagem
- **Validação Granular**: Análise página por página em PDFs multipágina

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

### 🏷️ Níveis de Log Utilizados

#### **DEBUG**
- 🔄 Fallbacks normais de OCR
- 🔝 Limitação de resultados
- 🔄 Início de processamento de arquivos
- 🖼️ Detecção de tipo de arquivo (imagem/PDF)
- 🤖 Validação de conteúdo com IA (imagens e texto)
- ✅ Confirmação de validação bem-sucedida
- 🔧 Etapas detalhadas do preprocessamento OCR
- 📄 Conversão de páginas de PDF para imagem
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
- ⚠️ Arquivos rejeitados pela validação IA (não são currículos)
- ⚠️ Falhas na validação com IA (fallback para processamento normal)
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

## 📄 Licença

MIT License
