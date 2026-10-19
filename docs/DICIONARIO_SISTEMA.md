# Dicionário do Sistema e Glossário Arquitetural (TCC - IPA)

Este documento centraliza a terminologia conceitual, regras de negócio e definições arquiteturais da solução de **Automação Inteligente de Processos (IPA)** desenvolvida para Micro, Pequenas e Médias Empresas (MPMEs).

---

## 1. Visão Geral da Arquitetura IPA

A arquitetura do projeto conecta quatro pilares fundamentais, espelhados no diagrama formal BPMN 2.0:
1. **Inteligência Artificial (IA):** Interpretação semântica e estruturação de documentos multimodais desestruturados (e-mails, mensagens, PDFs e fotos).
2. **Motor de Regras Determinístico:** Filtro rigoroso de segurança, normalização, validação fiscal e roteamento em 3 vias.
3. **Gerenciamento de Processos de Negócio (BPMN):** Controle de fluxo, máquina de estados finita e rastreabilidade total.
4. **Automação Robótica de Processos (RPA):** Agente de execução que opera a interface do usuário do sistema ERP legado.
5. **Supervisão Humana (Human-in-the-Loop):** Fila de exceções para validação e auditoria em casos ambíguos.

```
[Documento Inbox] ──> [Extração IA] ──> [Motor de Regras] ──┬──> [AUTOMÁTICO] ──> [Robô RPA] ──> [ERP]
                                                            ├──> [REVISÃO]   ──> [Operador Humano] ──> [Despacho RPA]
                                                            └──> [REJEIÇÃO]  ──> [Descarte / Auditoria]
```

---

## 2. Camada de Dados e Experimentação (`data/`)

### 2.1. `data/gold/` (Padrão Ouro / Gold Standard)
- **Definição:** Conjunto de 80 arquivos JSON que contêm a "verdade absoluta" de cada pedido sintético.
- **Função:** Serve como gabarito inquestionável para medir a acurácia da IA e do RPA. Se o gabarito prevê 10 unidades do produto `P-001`, qualquer extração diferente é contabilizada como erro.
- **Independência:** O gabarito foi gerado por sorteio determinístico (`verdade.py`), sem uso de LLM, eliminando qualquer viés algorítmico favorável.

### 2.2. `data/inbox/` (Caixa de Entrada Multimodal)
- **Definição:** Repositório que simula os canais de entrada da empresa física.
- **Formatos Suportados:**
  - `.txt`: Mensagens de texto simples (WhatsApp, e-mails diretos).
  - `.pdf`: Ordens de compra formais geradas eletronicamente.
  - `.png`: Fotos de comandas em papel ou prints de tela de celular.

### 2.3. `data/splits.json` (Divisão Experimental Estratificada)
- **Definição:** Arquivo de configuração que divide o dataset de 80 documentos em dois conjuntos disjuntos com seed fixa:
  - **Conjunto DEV (DOC-0001 a DOC-0030):** 30 documentos utilizados para desenvolvimento, calibração de prompts e ajustes de regras.
  - **Conjunto TESTE (DOC-0031 a DOC-0080):** 50 documentos intocados, congelados sob a tag git `freeze-v1`, utilizados estritamente para apuração das métricas científicas.

### 2.4. Categorias de Ruído do Dataset
- **Limpo:** Linguagem formal, estruturada e sem erros de português ou digitação.
- **Ruidoso:** Simulação realista do cotidiano de pequenas empresas: ausência de acentos, abreviações ("cx", "un", "pct"), erros ortográficos e termos informais.
- **Adversarial:** Mensagens deliberadamente projetadas para testar a robustez do sistema, divididas em:
  - *Ruído de Marketing:* Promoções ou comunicados com pedido legítimo no corpo.
  - *Não-Pedido:* Dúvidas de atendimento ou e-mails institucionais sem itens de compra.
  - *Prompt Injection:* Comandos maliciosos embutidos visando manipulação do assistente ou injeção de comandos SQL/Script.

### 2.5. Seed Determinística (`seed=42`)
- **Definição:** Número semente passado aos geradores pseudoaleatórios de Python.
- **Propósito:** Assegura reprodutibilidade científica total. Qualquer pesquisador que clonar o repositório e executar os geradores obterá exatamente os mesmos arquivos, textos e gabaritos.

---

## 3. Camada de Inteligência Artificial (`src/ipa/ai/`)

### 3.1. Gemini 2.5 Flash / Flash-Lite
- **Definição:** Modelo de linguagem e visão multimodal do Google utilizado para extração estruturada de entidades.
- **Modo Inline de Visão:** Envio de imagens e PDFs via bytes em memória (`types.Part.from_bytes`), eliminando a sobrecarga de upload via Google Files API e reduzindo a latência inicial em mais de 90%.

### 3.2. Cache Persistente (`.ai_cache.json`)
- **Definição:** Mecanismo de persistência local em disco baseado no hash MD5 do conteúdo do arquivo de entrada.
- **Função:** Se um documento já foi lido anteriormente pelo Gemini, a resposta estruturada é recuperada em milissegundos sem realizar chamadas de rede. Garante custo zero de API em testes de regressão e benchmarks locais.

### 3.3. Retry com Backoff Exponencial
- **Definição:** Mecanismo resiliente que intercepta erros transientes de servidor (HTTP 503 e 429) e re-executa a requisição após pausas progressivas (2s, 4s), prevenindo falhas em lotes volumosos.

---

## 4. Camada de Regras e Roteamento (`src/ipa/rules/`)

### 4.1. Normalização de Dados (`normalizar.py`)
- Padronização de códigos de produto para o padrão canônico do catálogo (`P-001`).
- Conversão de quantidades brasileiras com vírgula para floats padrão internacional (`3,5` -> `3.5`).
- Higienização e remoção de acentuação gráfica.

### 4.2. Validação Fiscal e Temporal (`validar.py`)
- **Cálculo de Dígitos Verificadores (CPF e CNPJ):** Implementação dos algoritmos matemáticos oficiais da Receita Federal (módulo 11), rejeitando números forjados.
- **Validação de Data ISO 8601:** Verificação de integridade no calendário gregoriano (rejeita datas inexistentes como 30 de fevereiro).
- **Proteção Contra Data Retroativa:** Bloqueia automaticamente pedidos com data limite de entrega anterior à data corrente de processamento.

### 4.3. Casamento Aproximado / Fuzzy Matching (`resolver.py`)
- Implementado via biblioteca de alta performance **RapidFuzz** para correlacionar o termo extraído com o catálogo oficial do ERP:
  - **Score $\ge$ 85% (Alta Certeza):** Match automático sem intervenção humana.
  - **Score entre 70% e 84% (Ambíguo):** Requer validação do operador humano.
  - **Score $<$ 70% (Não Encontrado):** Desvio imediato para fila de exceção.

### 4.4. Triagem Determinística em 3 Vias (`rotear.py`)
- **AUTOMÁTICO (Via Verde):** Cliente validado, data futura, produtos resolvidos com score alto e zero anomalias. Despacho direto ao robô.
- **REVISÃO (Via Amarela):** Pendência cadastral, data retroativa ou dúvida no catálogo. Encaminhado para a fila de revisão humana.
- **REJEIÇÃO (Via Vermelha):** Tentativa detectada de prompt injection, mensagem sem itens ou documento vazio. Descarte imediato e registro de auditoria.

---

## 5. Camada de Processos e Orquestração (`src/ipa/workflow/`)

### 5.1. Máquina de Estados Finita (`estados.py`)
- Modelo matemático computacional que governa o ciclo de vida do documento.
- Estados canônicos: `INICIADO`, `EXTRACAO_IA`, `REGRAS_TRIAGEM`, `EXECUTOR_RPA`, `REVISAO_HUMANA`, `REJEITADO`, `CONCLUIDO`, `FALHA`.
- **Invariante de Segurança:** Transições inválidas disparam exceções imediatamente (ex: proibido transitar de `INICIADO` diretamente para `EXECUTOR_RPA`).

### 5.2. Espelhamento BPMN 2.0
- O código em Python implementa de forma 1:1 o modelo de processos TO-BE desenhado no padrão internacional da OMG ([`docs/diagramas/bpmn_to_be.bpmn`](file:///home/joaoguilherme/Desktop/projetos/tcc-ipa/docs/diagramas/bpmn_to_be.bpmn)).

### 5.3. Telemetria e Cronometragem (`src/ipa/metrics/eventos.py`)
- Uso estrito de `time.perf_counter()` para cronometrar a latência isolada de cada estágio individual (IA, regras, execução RPA e revisão humana), garantindo rigor métrico.

---

## 6. Camada de Revisão Humana / Human-in-the-Loop (`src/ipa/review/`)

### 6.1. Fila de Pendências (`fila.py`)
- Armazena as ocorrências desviadas pelo motor de regras.
- Suporta persistência remota na tabela `ipa_revisoes` do Supabase e resiliência com fallback automático para arquivo local (`data/revisoes_local.json`).

### 6.2. Interface Split View (`/revisoes/{id}`)
- Layout ergonômico dividido em duas colunas no navegador:
  - **Esquerda:** Documento original do fornecedor (PDF, imagem ou texto).
  - **Direita:** Formulário com os dados pré-extraídos, badges de aviso e acesso ao catálogo para correção.
- **Cronômetro Oculto:** Mede a duração da intervenção humana em milissegundos para fins de pesquisa comparativa.

---

## 7. Camada de Execução RPA e Sistema Legado (`rpa/` e `erp_sim/`)

### 7.1. ERP Simulado (`erp_sim/`)
- Aplicação corporativa construída em FastAPI, HTML5 e CSS de alto contraste WCAG.
- Simula o sistema legado fechado da MPME, operando sem APIs públicas de integração para entrada de pedidos.

### 7.2. Contrato de Integração Pydantic (`PedidoExtraido`)
- DTO (Data Transfer Object) estritamente tipado que conecta a saída das regras ao robô de automação.

### 7.3. Robô Playwright Chromium (`rpa/bot.py`)
- Automação de navegador que navega pelas telas do ERP, preenche o formulário de pedido campo a campo e submete a transação.
- Opera em modo *headless* (silencioso em segundo plano) ou visível.

### 7.4. Idempotência Zero
- Mecanismo do robô que verifica se a referência externa (`ref_id`) já foi lançada no ERP antes de tentar preencher o formulário. Se já existir, aborta com status `duplicado` sem gerar faturamento em duplicidade.

### 7.5. Evidências Visuais de Auditoria (`rpa/evidencias/`)
- Captura automática de screenshot de tela inteira ao final de cada transação do robô, salvando comprovante com timestamp para rastreabilidade contábil.

### 7.6. StubExecutor (`src/ipa/executor.py`)
- "Dublê" do robô que simula a resposta do ERP em 50ms, viabilizando execução em lote ultra-rápida sem consumo desnecessário de CPU do navegador.

---

## 8. Camada Experimental e Avaliação Científica (`eval/` e `results/`)

### 8.1. Métricas de Classificação e Extração (`eval/metrics.py`)
- **Precision (Precisão):** Proporção de itens extraídos que de fato pertencem ao gabarito.
- **Recall (Revocação):** Proporção de itens do gabarito que a IA foi capaz de identificar.
- **F1-Score:** Média harmônica entre Precisão e Revocação ($F_1 = 2 \cdot \frac{P \cdot R}{P + R}$).

### 8.2. Mapeamento dos Experimentos (Fase 11)
- **EXP1 (Manual vs IPA):** Avaliação de ganho de produtividade (Speed-Up) e taxa de erro entre operadores humanos digitando no ERP vs orquestrador.
- **EXP2 (Regex vs IA):** Prova científica de superioridade da IA frente a parsers determinísticos em cenários ruidosos.
- **EXP3 (F1 da Extração):** Avaliação detalhada do acerto campo a campo no conjunto de teste.
- **EXP4 (Curva Risco vs Cobertura):** Estudo de varredura de limiar de confiança para provar a hipótese $H_3$ (erro residual $\le 2\%$).
- **EXP5 (Resiliência do RPA):** Comprovação de tolerância a falhas e idempotência do robô Playwright.
- **EXP6 (Defesa contra Injeção):** Auditoria da taxa de bloqueio a tentativas de prompt injection (meta: 100% bloqueado).
- **EXP7 (Custos e Latência):** Decomposição de tempo por estágio e cálculo de custo operacional por pedido em Reais (R$).
