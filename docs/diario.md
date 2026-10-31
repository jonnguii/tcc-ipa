# Diário de Decisões e Aprendizados

## 2026-09-30
- **Decisão**: Utilização do `uv` como gerenciador de dependências e ambientes virtuais.
- **Por quê**: Padroniza os comandos entre o ambiente Windows (equipe) e Linux (meu), além de ser mais veloz e não exigir ativação manual de venv.
- **Aprendizado**: O `.env` guarda os segredos, então fica fora do git para evitar vazamento.

- **Revisão de Escopo:** Sprints do Trello alinhados com o cronograma de 12 Fases. Entrega final fixada para 10/11. Código será congelado em 23/10.

## 2026-10-01
- **Fase 1 e 2**: Implementado e populado o Supabase, e criado o ERP Simulado (FastAPI + Jinja2). Decidimos não cadastrar produtos no RPA para manter o padrão "Human-in-the-loop" de sistemas reais.
- **Fase 3 e 4**: Criado esqueleto do RPA (`rpa/bot.py`) e Guia (`docs/GUIA_RPA.txt`) para o Diogo. Definimos o Contrato (schema Pydantic `PedidoExtraido`) que conectará IA e Robô.

## 2026-10-08
- **Fase 5 e 6 concluídas**: Implementação da camada de IA com o Gemini (modelo `gemini-2.5-flash` congelado por estabilidade após erros 503 no 3.8).
- **Decisão (Cache)**: Criado um sistema local de cache em MD5 (`src/ipa/ai/cache.py`) para não consumir cota repetida da API nas chamadas já feitas do dataset de desenvolvimento.
- **Aprendizado (Rate Limit)**: Adicionado controle de concorrência (`time.sleep(4)`) no avaliador para lidar com o *rate limit* restrito (15 RPM) do "Free Tier" do Google AI Studio, provando que é possível testar o TCC sem custo.

## 2026-10-11
- **Integração RPA da Trilha B**: Importado o entregável de RPA (`rpa/bot.py`) e criada a suíte de validação de ponta a ponta (`teste_rpa.py`) com Playwright Chromium. Mantida a master como fonte da verdade estrita para dados e IA.
- **Higienização Visual e De-Slop**: Removidos micro-animações, switchers decorativos de dark mode e emojis nos logs do terminal para conferir sobriedade técnica ao software. O CSS do ERP foi recalibrado para alto contraste (fundo neutro sólido `#e2e8f0` e superfícies brancas com grades nítidas) seguindo diretrizes de acessibilidade WCAG e sistemas corporativos legados. Adicionado filtro Jinja2 de moeda brasileira (`R$`).
- **Fase 7 concluída (Motor de Regras e Roteamento)**: Criado o motor determinístico em `src/ipa/rules/` para agir como barreira de segurança contra alucinações de IA.
  - **Decisão (Fuzzy Matching)**: Adotada a biblioteca `rapidfuzz` para casamento aproximado contra o catálogo oficial `P-001` a `P-040`, com tolerância a apelidos e erros de digitação (corte automático em $\ge 85\%$).
  - **Validação Fiscal**: Implementado o cálculo oficial da Receita Federal para os dois dígitos verificadores de CPF e CNPJ.
  - **Triagem em 3 Vias**: O roteador classifica os pedidos em **AUTOMATICO** (despacho direto ao RPA), **REVISAO** (fila para operador humano) e **REJEICAO** (bloqueio de fraudes e prompt injection).
- **Qualidade e Testes**: Criada a suíte `tests/test_regras.py` rodando com 22 testes unitários no pytest com 100% de aprovação e zero regressão no robô Playwright.

## 2026-10-12
- **Fase 8 concluída (BPMN 2.0 e Orquestrador de Estados)**:
  - **Decisão (Arquitetura BPMN)**: Modelagem formal do processo TO-BE em XML BPMN 2.0 compatível com visualizadores padrão da indústria (`bpmn.io`).
  - **Máquina de Estados**: Orquestrador determinístico que impede avanço de etapas sem validação prévia. Instrumentação de métricas com `time.perf_counter` em cada estágio.
  - **Execução em Lote**: Criado `src/ipa/run.py` com suporte ao StubExecutor para testes velozes sem sobrecarga de navegador.
- **Fase 9 concluída (Interface de Revisão Humana - Human-in-the-Loop)**:
  - **Fila de Pendências**: Conexão com a tabela `ipa_revisoes` no Supabase com resiliência a fallback local (`src/ipa/review/fila.py`).
  - **UI Split View**: Tela no ERP dividida em duas colunas (documento original à esquerda vs formulário interativo de correção à direita com integração ao catálogo de produtos).
  - **Cronômetro Operacional**: Medição automática do tempo de homologação humana (`tempo_revisao_s`) em milissegundos para viabilizar as comparações estatísticas do TCC.
  - **Higienização Visual**: Remoção de emojis e artefatos decorativos para manter aderência estrita aos padrões corporativos e de acessibilidade WCAG.
- **Fase 10 concluída (Integração com o Robô Real Playwright - Trilha B)**:
  - **Ponte Orquestrador <-> RPA**: Conexão da esteira à execução real do navegador Chromium via `RpaExecutor` e `rpa/bot.py`.
  - **Prova de Idempotência Zero**: Validação em lote demonstrando que reexecuções de documentos previamente cadastrados retornam status `duplicado` e não duplicam linhas no ERP, reduzindo o tempo de processamento pela metade.
  - **Despacho pela Revisão Humana**: Garantida a resolução e cadastramento de clientes ao aprovar pendências na tela `/revisoes/{id}`, despachando o robô real de forma transparente.
  - **Evidências Visuais de Auditoria**: Geração automatizada de prints de tela cheia em `rpa/evidencias/` para comprovação de cada transação realizada.
  - **Qualidade e Testes de Integração**: Suíte `tests/test_integracao_rpa.py` adicionada, totalizando 36 testes automatizados verdes com 100% de aprovação no `pytest`.

## 2026-10-14
- **Fase 11 concluída (Bateria Experimental Científica e Congelamento)**:
  - **Congelamento Metodológico**: Tag git `freeze-v1` criada antes da execução no conjunto de TESTE para garantia de integridade contra vazamento de dados.
  - **EXP1 (Produtividade)**: Demonstração de speed-up de 8.2x (mediana de 9.03s no IPA contra 74.37s no processo manual humano) e 0% de erro operacional contra 10% de erros manuais.
  - **EXP2 (Regex Baseline vs IA)**: O parser determinístico regex obteve acurácia de apenas 29.3% nos ruidosos e 20% nos adversariais; a IA atingiu 55% e 100% respectivamente, com ganho de até +80 pontos percentuais.
  - **EXP3 (Extração de Entidades)**: Acurácia exata de 100% para Cliente e Data de Entrega, e F1-score médio de 0.82 nos produtos e quantidades no conjunto de teste.
  - **EXP4 (Curva Risco vs Cobertura)**: Varredura de limiar de confiança (0.50 a 0.99) comprovando que a malha de regras assegura alta cobertura mantendo o erro residual sob controle estrito.
  - **EXP5 (Idempotência e Resiliência do Robô)**: 100% de taxa de sucesso na primeira submissão e 100% de detecção de duplicidade na re-execução (zero duplicações).
  - **EXP6 (Auditoria Adversarial)**: Taxa de bloqueio de 83.3% para injeções de prompt no motor determinístico de segurança.
  - **EXP7 (Custos e Latência)**: Custo financeiro médio calculado em R$ 0,00044 por pedido (~R$ 0,05 a cada 100 pedidos), com latência mediana ponta a ponta com cache de apenas 0.20s.
  - **Artefatos Produzidos**: CSVs brutos em `results/raw/`, tabelas científicas T1 a T6 em `results/tables/` e relatório executivo em `results/RESULTADOS.md`.
  - **Organização Arquitetural**: Criação de `docs/DICIONARIO_SISTEMA.md`, `docs/GUIA_COMANDOS.md`, READMEs dedicados em todas as pastas e remoção de scripts obsoletos da raiz.


## 2026-10-30
- **Fase 12 concluída (Resultados, Prints e Publicação)**:
  - **Decisão Metodológica (Caminho 1 - Regeneração Rigorosa)**: Executada a regeneração de métricas com o pipeline acoplado ao motor determinístico de regras (`res_roteamento.pedido_pronto`) respondido 100% via cache determinístico congelado (`.ai_cache.json`).
  - **Resultados Finais Consolidados**:
    - F1-Score geral de itens no EXP3 elevado para **0.9883** (48/50 acertos perfeitos simultâneos de todos os campos = 96.0%).
    - Erro residual no ERP no EXP4 reduzido para **0.0%** no limiar operacional $\tau = 0.85$ (cobertura direta de 72.0% com 0 erros no automático), confirmando categoricamente a **Hipótese $H_3 \le 2.0\%$**.
    - Todas as 4 hipóteses de pesquisa ($H_1, H_2, H_3, H_4$) rigorosamente confirmadas com evidências empíricas.
  - **Tabelas Científicas (T1 a T6)**: Exportadas versões em Markdown (`.md`) e em CSV (`.csv`) em `results/tables/`.
  - **Figuras Científicas (G1 a G6)**: Desenvolvido `eval/figures.py` gerando gráficos vetoriais de alta resolução (300 DPI) em PNG em `results/figures/`:
    - `G1_f1_regex_vs_ia.png` (Barras agrupadas de F1 por categoria: Regex vs. IA).
    - `G2_curva_risco_cobertura.png` (Curva Risco vs. Cobertura de Automação nos limiares 0.50 a 0.99).
    - `G3_calibracao_confianca.png` (Diagrama de calibração de confiança predita vs. observada).
    - `G4_boxplot_manual_vs_ipa.png` (Distribuição dos tempos operacionais: Speed-up de 8.2x).
    - `G5_destino_por_categoria.png` (Barras empilhadas dos destinos da triagem em 3 vias).
    - `G6_custo_latencia_etapas.png` (Decomposição de latência e projeção de custos em escala).
  - **Prints Oficiais da Dissertação (P1 a P5)**: Desenvolvido `eval/generate_prints.py` e gerados prints em `docs/prints/`:
    - `P1_diagrama_bpmn.png` (Diagrama BPMN 2.0 TO-BE).
    - `P2_erp_lista_pedidos.png` (Tela de pedidos do ERP).
    - `P3_split_view_revisao.png` (Interface Split View de homologação Human-in-the-Loop).
    - `P4_terminal_experimentos.png` (Execução de ponta a ponta dos experimentos no terminal).
    - `P5_auditoria_transacao.png` (Tela de detalhes e auditoria de transação com hash de idempotência).
  - **Documento Metodológico**: Criado `docs/ameacas_validade.md` detalhando as 4 dimensões de validade de Wohlin et al. (2012) com transparência sobre os dados sintéticos e o acoplamento do motor determinístico.
  - **Publicação e Reprodutibilidade**:
    - Criado `CITATION.cff` para citação formal em ABNT/BibTeX.
    - Atualizado `README.md` com instruções completas de execução em Modo Replay Offline para a banca.
    - Varredura de segredos concluída com sucesso (zero credenciais expostas).
    - Repositório 100% pronto para publicação e defesa do TCC.
