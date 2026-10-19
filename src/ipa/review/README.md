# Módulo de Revisão Humana (Fase 9 - Human-in-the-Loop)

Este módulo implementa a governança e o tratamento de exceções da esteira de automação inteligente (IPA). Quando o motor determinístico de regras identifica dados ambíguos ou inconsistentes, o processo não falha nem insere informações erradas no ERP: o documento é retido para **homologação humana**.

---

## 1. Arquitetura do Módulo

| Arquivo | Papel Técnico |
| :--- | :--- |
| **`fila.py`** | Camada de persistência e serviço conectada à tabela `ipa_revisoes` no Supabase (com fallback local para operação offline). |
| **`erp_sim/templates/revisoes_lista.html`** | Tela da fila de trabalho com contadores de status e crachás de motivos de retenção. |
| **`erp_sim/templates/revisoes_detalhe.html`** | Interface de *Split View* (visão lado a lado) com cronômetro de precisão em JavaScript. |
| **`tests/test_revisao.py`** | Suíte de testes automatizados com cobertura para inserção, consulta, resolução e retomada do workflow. |

---

## 2. Como Funciona o Split View

A tela `/revisoes/{id}` divide o espaço de trabalho em duas colunas:
1. **Lado Esquerdo (Origem):** Exibe o documento original recebido pelo fornecedor (texto puro, PDF ou imagem).
2. **Lado Direito (Dados da IA & Correção):**
   - **Campos Cadastrais:** Nome da empresa, CPF/CNPJ e data de entrega com validação em tempo real.
   - **Casamento com Catálogo:** Tabela que mapeia o texto lido pela IA para o catálogo oficial (`P-001` a `P-040`). Itens com similaridade inferior a 85% recebem alerta visual suave para chamar a atenção imediata do operador.
   - **Cronômetro Operacional:** Mede em milissegundos o tempo decorrido desde o carregamento da tela até o clique do operador, persistindo `tempo_revisao_s` na auditoria do TCC.

---

## 3. Retomada da Máquina de Estados

Ao clicar em **Aprovar e Despachar ao Robô**, o sistema executa a transição formal:
$$\text{REVISAO\_HUMANA} \longrightarrow \text{EXECUTOR\_RPA} \longrightarrow \text{CONCLUIDO}$$

Se o operador constatar que o documento é ilegítimo ou fraudulento e clicar em **Rejeitar Pedido**:
$$\text{REVISAO\_HUMANA} \longrightarrow \text{REJEITADO}$$
