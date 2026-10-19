# Módulo de Avaliação Experimental e Métricas (`eval/`)

Este diretório contém os scripts, métricas e protocolos científicos da **Fase 11 (Experimentos)** do TCC-IPA.

---

## 1. Estrutura do Módulo

```
eval/
├── metrics.py              # Cálculo de Precision, Recall, F1 por campo crítico e estatísticas
├── charts.py               # Consolidador das tabelas científicas (T1 a T6) e relatórios
├── exp1_manual.py          # Coleta guiada e cronometrada do tempo manual (Apêndice G)
├── exp1_auto.py            # Execução automatizada do orquestrador IPA nos mesmos 30 docs
├── exp2_regex.py           # Avaliação do baseline determinístico por regex vs IA
├── exp3_extracao.py        # Avaliação detalhada de extração do Gemini no conjunto de teste
├── exp4_limiares.py        # Varredura de limiares (0.50 a 0.99) para a curva risco vs cobertura
├── exp5_rpa.py             # Auditoria de tolerância a falhas e idempotência do robô Playwright
├── exp6_injection.py       # Auditoria de segurança e bloqueio de prompt injection
├── exp7_custos.py          # Apuração de tokens, custos financeiros em R$ e latências por etapa
└── rodar_experimentos.py   # Script mestre que orquestra a bateria completa em sequência
```

---

## 2. Mapa dos Experimentos (Fase 11)

| Experimento | Tese / Hipótese | Script de Execução | Arquivo de Saída |
| :--- | :--- | :--- | :--- |
| **EXP1** | H1: O IPA reduz o tempo por pedido em relação ao manual | `exp1_manual.py` e `exp1_auto.py` | `results/raw/exp1_*.csv` |
| **EXP2** | H4: A IA supera o parser regex em textos ruidosos | `exp2_regex.py` | `results/raw/exp2_regex.csv` |
| **EXP3** | H2: Extração atinge F1 $\ge$ 0,90 nos campos críticos | `exp3_extracao.py` | `results/raw/exp3_extracao.csv` |
| **EXP4** | H3: Com roteamento por confiança, erro residual $\le$ 2% | `exp4_limiares.py` | `results/raw/exp4_limiares.csv` |
| **EXP5** | Resiliência do RPA e prova de taxa zero de duplicidade | `exp5_rpa.py` | `results/raw/exp5_rpa.csv` |
| **EXP6** | Taxa zero de evasão em ataques de prompt injection | `exp6_injection.py` | `results/raw/exp6_injection.csv` |
| **EXP7** | Viabilidade econômica de MPMEs e decomposição de latência | `exp7_custos.py` | `results/raw/exp7_custos.csv` |

---

## 3. Como Executar

### Bateria Completa Automática:
```bash
uv run python eval/rodar_experimentos.py
```

### Experimento Individual (Exemplo: EXP3 - Extração):
```bash
uv run python eval/exp3_extracao.py
```

### Gerar ou Atualizar as Tabelas T1 a T6:
```bash
uv run python eval/charts.py
```
As tabelas Markdown geradas ficam disponíveis em `results/tables/` e o relatório executivo consolidado em `results/RESULTADOS.md`.
