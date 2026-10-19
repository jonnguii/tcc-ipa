# Manual Operacional de Comandos do Sistema (CLI Guide)

Este manual documenta todos os comandos e ferramentas executáveis do projeto **TCC-IPA**, explicando **o que faz**, **quando usar**, **sintaxe** e **exemplos de saída**.

---

## 1. Servidor e Aplicação do ERP Simulado

### 1.1. Iniciar o ERP Simulado
- **O que faz:** Inicia o servidor local FastAPI na porta 8000, servindo as telas de login, pedidos, catálogo e fila de revisão humana.
- **Quando usar:** Obrigatório para que o robô RPA consiga interagir com as telas e para que os operadores realizem o teste manual.
- **Comando:**
  ```bash
  uv run uvicorn erp_sim.main:app --port 8000
  ```
- **Acesso no navegador:**
  - Início / Login: `http://localhost:8000`
  - Criar Pedido Manual: `http://localhost:8000/pedidos/novo`
  - Listagem de Pedidos: `http://localhost:8000/pedidos`
  - Fila de Revisão Humana: `http://localhost:8000/revisoes`

---

## 2. Execução do Orquestrador IPA (`src/ipa/run.py`)

O script [`src/ipa/run.py`](file:///home/joaoguilherme/Desktop/projetos/tcc-ipa/src/ipa/run.py) é o ponto de entrada principal para processar lotes de documentos pela esteira automatizada.

### 2.1. Execução Rápida em Modo Simulado (Stub)
- **O que faz:** Processa documentos utilizando o dublê do robô (50ms por pedido), ideal para validação de lógica e testes rápidos.
- **Comando:**
  ```bash
  uv run python src/ipa/run.py --limite 5 --executor stub
  ```

### 2.2. Execução com o Robô Real (Playwright RPA)
- **O que faz:** Aciona o navegador Chromium real via Playwright para digitar os campos na tela do ERP e salvar comprovantes em `rpa/evidencias/`.
- **Comando:**
  ```bash
  uv run python src/ipa/run.py --limite 5 --executor rpa
  ```

### 2.3. Filtragem por Conjunto Experimental (`--split`)
- **O que faz:** Restringe o processamento aos documentos de desenvolvimento (`dev`, docs 1-30) ou teste (`teste`, docs 31-80) conforme `data/splits.json`.
- **Comandos:**
  ```bash
  # Processar primeiros 10 docs do conjunto DEV
  uv run python src/ipa/run.py --split dev --limite 10

  # Processar lote do conjunto TESTE
  uv run python src/ipa/run.py --split teste --limite 20
  ```

### 2.4. Filtragem por IDs Específicos (`--docs`)
- **O que faz:** Executa apenas documentos pontuais informados por vírgula.
- **Comando:**
  ```bash
  uv run python src/ipa/run.py --docs DOC-0001,DOC-0004,DOC-0013,DOC-0022
  ```

### 2.5. Filtragem por Categoria (`--categoria`)
- **O que faz:** Filtra os documentos da inbox pelo nível de ruído (`limpo`, `ruidoso` ou `adversarial`).
- **Comando:**
  ```bash
  uv run python src/ipa/run.py --categoria ruidoso --limite 5
  ```

---

## 3. Bateria de Experimentos Científicos (Fase 11)

### 3.1. Executar Todos os Experimentos em Sequência (Master)
- **O que faz:** Roda de ponta a ponta todos os experimentos (EXP1 a EXP7), gerando todos os CSVs em `results/raw/` e as tabelas em `results/tables/`.
- **Comando:**
  ```bash
  uv run python eval/rodar_experimentos.py
  ```

### 3.2. EXP1: Coleta de Tempo Manual para Operador (Membro 3)
- **O que faz:** Interface interativa guiada que cronometra no terminal o tempo de digitação de um ser humano no ERP.
- **Comandos:**
  ```bash
  # Operador 1 preenchendo o Lote 1 (docs 1 a 10)
  uv run python eval/exp1_manual.py --participante "Membro 3" --lote 1

  # Modo de simulação sintética de linha de base
  uv run python eval/exp1_manual.py --simular --lote 1
  ```

### 3.3. EXP1: Execução Automatizada do Orquestrador IPA
- **O que faz:** Executa a esteira automática nos mesmos 30 documentos do teste manual para apuração do speed-up relativo.
- **Comando:**
  ```bash
  uv run python eval/exp1_auto.py
  ```

### 3.4. EXP2: Baseline Determinístico por Regex vs IA
- **O que faz:** Avalia a capacidade de extração de um parser tradicional via Regex no conjunto de teste.
- **Comando:**
  ```bash
  uv run python eval/exp2_regex.py
  ```

### 3.5. EXP3: Avaliação de Extração Inteligente com IA
- **O que faz:** Avalia Precision, Recall e F1-Score do Gemini contra o gabarito oficial em todos os documentos de teste.
- **Comando:**
  ```bash
  uv run python eval/exp3_extracao.py
  ```

### 3.6. EXP4: Varredura de Limiares de Confiança
- **O que faz:** Varre limiares de 0.50 a 0.99 calculando cobertura de automação e erro residual.
- **Comando:**
  ```bash
  uv run python eval/exp4_limiares.py
  ```

### 3.7. EXP5: Resiliência e Idempotência do Robô RPA
- **O que faz:** Executa duas rodadas consecutivas de pedidos para comprovar tolerância a falhas e taxa zero de duplicação.
- **Comando:**
  ```bash
  uv run python eval/exp5_rpa.py
  ```

### 3.8. EXP6: Auditoria de Segurança Contra Injeção Adversarial
- **O que faz:** Submete todos os documentos com ataques de injeção ao motor de regras para comprovar descarte e bloqueio.
- **Comando:**
  ```bash
  uv run python eval/exp6_injection.py
  ```

### 3.9. EXP7: Análise de Custos e Latência por Estágio
- **O que faz:** Contabiliza tokens de IA, calcula custo em R$ por pedido e levanta latências mediana e P90.
- **Comando:**
  ```bash
  uv run python eval/exp7_custos.py
  ```

### 3.10. Consolidação de Tabelas Científicas (T1 a T6)
- **O que faz:** Lê os CSVs brutos em `results/raw/`, sintetiza as tabelas em `results/tables/` e atualiza `results/RESULTADOS.md`.
- **Comando:**
  ```bash
  uv run python eval/charts.py
  ```

---

## 4. Geração do Dataset Sintético

### 4.1. Gerar Gabaritos Ouro e Splits (`data/generator/verdade.py`)
- **O que faz:** Gera 80 arquivos `.json` em `data/gold/` e o arquivo `data/splits.json` com seed determinística 42.
- **Comando:**
  ```bash
  uv run python data/generator/verdade.py
  ```

### 4.2. Fabricar Arquivos Físicos da Inbox (`data/generator/gerar_inbox.py`)
- **O que faz:** Constrói os 80 arquivos físicos (.txt, .pdf, .png) em `data/inbox/`, aplicando ruídos tipográficos e diagramações.
- **Comando:**
  ```bash
  uv run python data/generator/gerar_inbox.py
  ```

---

## 5. Manutenção, Limpeza e Reset (`scripts/reset.py`)

### 5.1. Limpeza Completa do Ambiente
- **O que faz:** Apaga todos os pedidos de teste no Supabase, limpa a fila de revisão humana, exclui prints de evidência do robô e zera o cache da IA (`.ai_cache.json`).
- **Comando:**
  ```bash
  uv run python scripts/reset.py --tudo
  ```

### 5.2. Limpeza Apenas de Transações (Preserva Cache de IA)
- **O que faz:** Limpa pedidos, revisões e prints no ERP, mas preserva `.ai_cache.json` para economizar cota de API.
- **Comando:**
  ```bash
  uv run python scripts/reset.py --pedidos
  ```

---

## 6. Qualidade, Testes e Lint

### 6.1. Executar Testes Automatizados (Pytest)
- **O que faz:** Executa a suíte de testes unitários e de integração (regras, schemas, revisão e robô Playwright).
- **Comando:**
  ```bash
  uv run pytest
  ```

### 6.2. Verificação de Código e Estilo (Ruff)
- **O que faz:** Audita o código-fonte em busca de más práticas, imports não utilizados e inconformidades de PEP8.
- **Comando:**
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
