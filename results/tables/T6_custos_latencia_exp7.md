### Tabela T6 - Decomposição de Custos e Latência por Estágio do Workflow (EXP7)

| Componente da Arquitetura | Latência Mediana (s) | Latência P90 (s) | Custo Médio por Pedido | Participação no Custo |
| :--- | :---: | :---: | :---: | :---: |
| **Extração Inteligente (Gemini Flash)** | 0.000s | 0.001s | R$ 0.00044 | 100.0% do custo de IA |
| **Triagem e Regras Determinísticas** | 0.140s | 0.197s | R$ 0,00000 | 0.0% (Computação local) |
| **Pipeline Completo Integrado** | **0.203s** | **0.255s** | **R$ 0.00044** | **~R$ 0,05 a cada 100 pedidos** |

