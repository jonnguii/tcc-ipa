# Automação Inteligente de Processos (IPA) para MPMEs

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/badge/uv-astral-purple.svg)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![BPMN 2.0](https://img.shields.io/badge/BPMN-2.0%20Standard-orange.svg)](docs/diagramas/bpmn_to_be.bpmn)

Repositório oficial do Trabalho de Conclusão de Curso (TCC) em Sistemas de Informação:  
**"Automação Inteligente de Processos (IPA) no Processamento de Pedidos em Micro, Pequenas e Médias Empresas (MPMEs)"**.

O projeto propõe e avalia experimentalmente uma arquitetura de alta confiabilidade integrando **Inteligência Artificial Multimodal (Google Gemini)**, **Motor de Regras Determinístico**, **BPMN 2.0** e **Automação Robótica de Processos (Playwright RPA)** com supervisão humana (*Human-in-the-Loop*).

---

## 🏛️ Arquitetura do Sistema

```
                        ┌─────────────────────────────────────────────────────────────┐
                        │                 FLUXO ORQUESTRADO (BPMN 2.0)                 │
                        └─────────────────────────────────────────────────────────────┘
                                                       │
1. Entrada Multimodal   [ data/inbox/ (TXT, PDF, PNG) ]
                                                       │
2. Extração Inteligente [ src/ipa/ai/ (Gemini Flash Multimodal + Cache Persistente) ]
                                                       │
3. Filtro e Segurança   [ src/ipa/rules/ (Validação Fiscal, RapidFuzz, Anti-Injeção) ]
                                                       │
                                  ┌────────────────────┴────────────────────┐
                                  ▼                                         ▼
4. Gateway BPMN            [ VIA VERDE: AUTOMÁTICO ]              [ VIA AMARELA: REVISÃO ]
                                  │                                         │
5. Execução / Supervisão   [ rpa/ (Playwright RPA) ]              [ erp_sim/ (Split View) ]
                                  │                                         │
6. Sistema Legado          [ erp_sim/ (ERP Simulado) ]            [ Operador Humano ]
                                  │                                         │
                                  └────────────────────┬────────────────────┘
                                                       ▼
7. Métricas & Auditoria    [ eval/ & results/ (Precision, Recall, F1, Latência, Custos) ]
```

---

## 📂 Estrutura do Repositório

```
tcc-ipa/
├── data/               # Camada de dados sintéticos (gold standard, inbox, splits e gerador)
├── docs/               # Documentação técnica, dicionário do sistema, comandos e BPMN
│   ├── DICIONARIO_SISTEMA.md  # Dicionário conceitual completo e arquitetural
│   ├── GUIA_COMANDOS.md       # Manual operacional com todos os comandos da CLI
│   ├── PROGRESSO.md           # Rastreamento de marcos e fases (0 a 12)
│   └── diagramas/             # Modelo visual de processos (bpmn_to_be.bpmn)
├── erp_sim/            # ERP Corporativo simulado (FastAPI + Jinja2 + Supabase)
├── eval/               # Bateria experimental (EXP1 a EXP7), métricas F1 e relatórios
├── results/            # Resultados brutos (results/raw/) e tabelas científicas (results/tables/)
├── rpa/                # Robô de automação de tela em Playwright Chromium
├── scripts/            # Utilitários de manutenção e reset de ambiente
├── src/ipa/            # Núcleo da esteira IPA (AI, regras, workflow e contratos)
└── tests/              # Suíte de testes unitários e de integração (Pytest)
```

---

## ⚡ Guia Rápido de Instalação e Execução

### 1. Pré-requisitos
- Python 3.12+
- Gerenciador [`uv`](https://docs.astral.sh/uv/) instalado
- Projeto no [Supabase](https://supabase.com) configurado com as credenciais no arquivo `.env`

### 2. Clonar e Instalar Dependências
```bash
git clone https://github.com/jonnguii/tcc-ipa.git
cd tcc-ipa
uv sync
uv run playwright install chromium
```

### 3. Configuração de Variáveis de Ambiente (`.env`)
Copie o exemplo e insira suas credenciais:
```bash
cp .env.example .env
```
Campos requeridos:
- `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`: Conexão do banco de dados do ERP.
- `GEMINI_API_KEY`: Chave da API do Google AI Studio para a camada de visão/extração.

### 4. Iniciar o ERP Simulado
Em um terminal dedicado:
```bash
uv run uvicorn erp_sim.main:app --port 8000
```
Acesse no navegador:
- ERP: <http://localhost:8000>
- Fila de Revisão Humana: <http://localhost:8000/revisoes>

### 5. Executar o Orquestrador IPA
Em outro terminal:
```bash
# Execução de lote no modo simulado (Stub):
uv run python src/ipa/run.py --limite 5 --executor stub

# Execução com o Robô Real (Playwright):
uv run python src/ipa/run.py --limite 5 --executor rpa
```

---

## 🔬 Bateria Experimental (Fase 11)

Para reproduzir todos os experimentos científicos de uma só vez (EXP1 a EXP7):
```bash
uv run python eval/rodar_experimentos.py
```

Os resultados detalhados e tabelas comparativas são consolidados em:
- **Tabelas Científicas (T1 a T6):** [`results/tables/`](results/tables/)
- **Relatório Analítico:** [`results/RESULTADOS.md`](results/RESULTADOS.md)

---

## 📚 Documentação Complementar

- 📖 [Dicionário do Sistema e Glossário Arquitetural](docs/DICIONARIO_SISTEMA.md)
- ⌨️ [Manual Operacional de Comandos da CLI](docs/GUIA_COMANDOS.md)
- 📊 [Diário de Bordo e Decisões Técnicas](docs/diario.md)
- 🔄 [Controle de Progresso por Fase](docs/PROGRESSO.md)
- 🤖 [Manual do Robô RPA](rpa/README.md)
- 📦 [Camada de Dados e Splits](data/README.md)

---

## 🛡️ Licença e Ética
- **Licença:** MIT License.
- **Privacidade:** Todos os dados contidos neste repositório são 100% sintéticos e foram gerados por algoritmos pseudoaleatórios determinísticos. Nenhum dado de clientes ou empresas reais foi utilizado.