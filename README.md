# Automação Inteligente de Processos (IPA) para MPMEs

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/badge/uv-astral-purple.svg)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![BPMN 2.0](https://img.shields.io/badge/BPMN-2.0%20Standard-orange.svg)](docs/diagramas/bpmn_to_be.bpmn)

Pipeline de Automação Inteligente de Processos (IPA) para ingestão, validação e lançamento de pedidos recebidos em formatos não estruturados (PDF, PNG e TXT) em sistema ERP legado.

Desenvolvido como projeto de Trabalho de Conclusão de Curso (TCC) em Sistemas de Informação, o sistema combina:
- **Extração multimodal**: LLM (Google Gemini Flash) com cache local de requisições.
- **Validação determinística**: correspondência difusa de entidades (RapidFuzz), validações fiscais e filtro de *prompt injection*.
- **Orquestração de processos**: máquina de estados inspirada na modelagem BPMN 2.0, roteando pedidos para execução direta ou para fila de revisão humana (*human-in-the-loop*).
- **Execução RPA**: robô em Playwright Chromium para digitação e lançamento de pedidos no ERP web.

---

## Fluxo da Esteira

```text
[ Documento de Entrada ] (TXT, PDF, PNG em data/inbox/)
          │
          ▼
[ Extração Multimodal ] (Gemini Flash + .ai_cache.json)
          │
          ▼
[ Validação e Regras ] (RapidFuzz, cálculo fiscal, detecção de injeção)
          │
   ┌──────┴──────┐
   ▼             ▼
[ Via Verde ]   [ Via Amarela ]
Confiança >= 0.85   Confiança < 0.85 ou
Sem violações       Inconsistência cadastral / fiscal
   │             │
   ▼             ▼
[ Robô RPA ]    [ Fila de Revisão Humana ]
(Playwright)    (Interface web split-view)
   │             │
   └──────┬──────┘
          ▼
[ ERP Simulado ] (FastAPI + Supabase)
```

---

## Estrutura do Repositório

```text
tcc-ipa/
├── config/       # Regras de negócio em YAML (limiares, catálogo, validações)
├── data/         # Ingestão (inbox/), gabarito (gold/), geradores e splits
├── docs/         # Dicionário do sistema, guia de comandos, diário e BPMN
├── erp_sim/      # ERP web simulado (FastAPI + Jinja2 + Supabase)
├── eval/         # Bateria de experimentos científicos (EXP1 a EXP7) e métricas
├── results/      # Resultados brutos (raw/) e tabelas consolidadas (tables/)
├── rpa/          # Automação de tela com Playwright Chromium
├── scripts/      # Scripts utilitários (reset de banco e filas)
├── src/ipa/      # Motor da esteira IPA (AI, regras, workflow e contratos)
└── tests/        # Testes automatizados (pytest)
```

---

## Instalação e Configuração

### Pré-requisitos
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (gerenciador de dependências e ambiente)
- Projeto configurado no [Supabase](https://supabase.com)
- Chave de API do Google Gemini ([Google AI Studio](https://aistudio.google.com/))

### 1. Clonar e instalar dependências
```bash
git clone https://github.com/jonnguii/tcc-ipa.git
cd tcc-ipa
uv sync
uv run playwright install chromium
```

### 2. Variáveis de ambiente
Crie o arquivo `.env` a partir do modelo:
```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:
```dotenv
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-chave-service-role
GEMINI_API_KEY=sua-chave-gemini
GEMINI_MODEL=gemini-2.5-flash
AI_MODE=record
EXECUTOR=stub
ERP_BASE_URL=http://localhost:8000
ERP_SABOTAGE=none
RPA_HEADLESS=true
```

---

## Execução

### 1. Iniciar o ERP Simulado
O ERP precisa estar rodando para a interface de revisão e para as execuções com RPA:
```bash
uv run uvicorn erp_sim.main:app --port 8000
```
- Acesso ao ERP: `http://localhost:8000`
- Fila de Revisão Humana: `http://localhost:8000/revisoes`

### 2. Rodar a Esteira IPA (`src/ipa/run.py`)

**Modo Simulado (Stub)** — executa a esteira completa sem abrir o navegador (ideal para validação rápida):
```bash
uv run python src/ipa/run.py --limite 5 --executor stub
```

**Modo Robô Real (RPA)** — executa o lançamento real no ERP via Playwright:
```bash
uv run python src/ipa/run.py --limite 5 --executor rpa
```

**Filtros de execução:**
```bash
# Executar apenas documentos de teste (docs 31 a 80)
uv run python src/ipa/run.py --split teste --limite 10

# Executar documentos específicos
uv run python src/ipa/run.py --docs DOC-0001,DOC-0012,DOC-0039

# Filtrar por categoria do dataset
uv run python src/ipa/run.py --categoria ruidoso --limite 5
```

---

## Testes e Avaliação Experimental

### Executar suíte de testes
```bash
uv run pytest
```

### Reproduzir experimentos do TCC (EXP1 a EXP7)
Para executar a bateria de experimentos e gerar as tabelas comparativas:
```bash
uv run python eval/rodar_experimentos.py
```

Os resultados são consolidados em:
- [Relatório analítico de resultados](results/RESULTADOS.md)
- [Tabelas comparativas em Markdown](results/tables/)

---

## Documentação

- [Dicionário do Sistema e Decisões Técnicas](docs/DICIONARIO_SISTEMA.md)
- [Manual Operacional de Comandos (CLI)](docs/GUIA_COMANDOS.md)
- [Diagrama de Processo BPMN 2.0](docs/diagramas/bpmn_to_be.bpmn)
- [Diário de Bordo](docs/diario.md)
- [Rastreamento de Progresso](docs/PROGRESSO.md)

---

## Dados e Privacidade

Todos os 80 documentos da pasta `data/inbox/`, bem como os registros de clientes, produtos e pedidos cadastrados no ERP, são 100% sintéticos e gerados por scripts deterministicos. Nenhum dado pessoal real foi utilizado.

---

## Licença

Este projeto é distribuído sob a licença [MIT](LICENSE).