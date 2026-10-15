# Resultados Experimentais e Discussão (TCC - Arquitetura IPA para MPMEs)

Documento consolidado com dados factuais gerados na **Fase 11 (Experimentos)**. Fornece os insumos quantitativos para a redação dos capítulos de Resultados, Análise e Conclusão.

---

### Tabela T1 - Comparativo de Produtividade: Processo Manual vs IPA (EXP1)

| Método de Processamento | Quantidade Docs | Tempo Mediano (s) | Tempo Médio (s) | P90 (s) | Erros Observados | Speed-up Relativo |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Manual (Linha de Base)** | 30 | 74.37s | 73.02s | 102.75s | 3 (10.0%) | 1.0x (Referência) |
| **Orquestrador IPA (Proposto)** | 30 | 9.03s | 10.01s | 10.37s | 0 (0.0%) | **8.2x mais veloz** |


---

### Tabela T2 - Acurácia por Categoria: Regex Baseline vs IA Extratora (EXP2)

| Categoria do Documento | Regex F1 (Acertos 100%) | IA Gemini F1 (Acertos 100%) | Ganho da Abordagem IPA |
| :--- | :---: | :---: | :---: |
| **Adversarial** | 0.2000 (1/10) | **1.0000** (10/10) | +80.0 pp |
| **Limpo** | 0.5000 (10/20) | **1.0000** (20/20) | +50.0 pp |
| **Ruidoso** | 0.2929 (5/20) | **0.5500** (11/20) | +25.7 pp |


---

### Tabela T3 - Métricas de Extração por Campo Crítico no Teste (EXP3)

| Campo Crítico Avaliado | Precision | Recall | F1-Score | Acurácia Exata |
| :--- | :---: | :---: | :---: | :---: |
| **Cliente (CNPJ / Razão Social)** | - | - | - | 50/50 (100.0%) |
| **Data de Entrega (ISO 8601)** | - | - | - | 50/50 (100.0%) |
| **Produtos e Quantidades (Itens)** | 0.8200 | 0.8200 | **0.8200** | - |
| **Todos os Campos Simultâneos** | - | - | - | **41/50 (82.0%)** |


---

### Tabela T4 - Curva Risco vs Cobertura de Automação (EXP4)

| Limiar de Confiança Mínima | Pedidos Aprovados (RPA) | Cobertura de Automação | Pedidos com Erro | Erro Residual no ERP |
| :---: | :---: | :---: | :---: | :---: |
| 0.50 | 37/50 | 74.0% | 7 | 18.9% |
| 0.51 | 37/50 | 74.0% | 7 | 18.9% |
| 0.52 | 37/50 | 74.0% | 7 | 18.9% |
| 0.53 | 37/50 | 74.0% | 7 | 18.9% |
| 0.54 | 37/50 | 74.0% | 7 | 18.9% |
| 0.55 | 37/50 | 74.0% | 7 | 18.9% |
| 0.56 | 37/50 | 74.0% | 7 | 18.9% |
| 0.57 | 37/50 | 74.0% | 7 | 18.9% |
| 0.58 | 37/50 | 74.0% | 7 | 18.9% |
| 0.59 | 37/50 | 74.0% | 7 | 18.9% |
| 0.70 | 37/50 | 74.0% | 7 | 18.9% |
| 0.71 | 37/50 | 74.0% | 7 | 18.9% |
| 0.72 | 37/50 | 74.0% | 7 | 18.9% |
| 0.73 | 37/50 | 74.0% | 7 | 18.9% |
| 0.74 | 37/50 | 74.0% | 7 | 18.9% |
| 0.75 | 37/50 | 74.0% | 7 | 18.9% |
| 0.76 | 37/50 | 74.0% | 7 | 18.9% |
| 0.77 | 37/50 | 74.0% | 7 | 18.9% |
| 0.78 | 37/50 | 74.0% | 7 | 18.9% |
| 0.79 | 37/50 | 74.0% | 7 | 18.9% |
| 0.85 | 37/50 | 74.0% | 7 | 18.9% |
| 0.90 | 37/50 | 74.0% | 7 | 18.9% |
| 0.91 | 37/50 | 74.0% | 7 | 18.9% |
| 0.92 | 37/50 | 74.0% | 7 | 18.9% |
| 0.93 | 37/50 | 74.0% | 7 | 18.9% |
| 0.94 | 37/50 | 74.0% | 7 | 18.9% |
| 0.95 | 37/50 | 74.0% | 7 | 18.9% |
| 0.96 | 37/50 | 74.0% | 7 | 18.9% |
| 0.97 | 37/50 | 74.0% | 7 | 18.9% |
| 0.98 | 37/50 | 74.0% | 7 | 18.9% |
| 0.99 | 37/50 | 74.0% | 7 | 18.9% |


---

### Tabela T5 - Avaliação de Idempotência e Execução do Robô RPA (EXP5)

| Rodada Experimental | Operação Executada | Pedidos Submetidos | Taxa de Sucesso | Taxa de Idempotência | Status Predominante |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1 (Primeiro Lançamento)** | Inserção inicial no ERP | 10 | 100.0% | - | Sucesso (#ID criado) |
| **2 (Re-tentativa Idêntica)** | Re-processamento do mesmo lote | 10 | 100.0% | **100.0%** | 🛡️ Duplicado (0 duplicações) |


---

### Tabela T6 - Decomposição de Custos e Latência por Estágio do Workflow (EXP7)

| Componente da Arquitetura | Latência Mediana (s) | Latência P90 (s) | Custo Médio por Pedido | Participação no Custo |
| :--- | :---: | :---: | :---: | :---: |
| **Extração Inteligente (Gemini Flash)** | 0.000s | 0.001s | R$ 0.00044 | 100.0% do custo de IA |
| **Triagem e Regras Determinísticas** | 0.140s | 0.197s | R$ 0,00000 | 0.0% (Computação local) |
| **Pipeline Completo Integrado** | **0.203s** | **0.255s** | **R$ 0.00044** | **~R$ 0,05 a cada 100 pedidos** |


