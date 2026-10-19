# Diagramas de Processo do TCC: Arquitetura TO-BE

Este diretório contém a modelagem dos processos de negócio e automação inteligente do TCC.

## Diagrama Oficial BPMN 2.0 (Arquitetura TO-BE)

[![Diagrama de Processo BPMN 2.0 - Arquitetura TO-BE](bpmn_to_be.png)](bpmn_to_be.svg)

### Formatos Disponíveis
- **Modelo Oficial BPMN 2.0**: [`bpmn_to_be.bpmn`](bpmn_to_be.bpmn) — segue a especificação internacional BPMN 2.0 da OMG e pode ser aberto e editado diretamente no [bpmn.io](https://demo.bpmn.io).
- **Vetor SVG**: [`bpmn_to_be.svg`](bpmn_to_be.svg) — gráfico vetorial escalável com fundo otimizado para visualização em temas claro e escuro.
- **Imagem PNG (Alta Resolução)**: [`bpmn_to_be.png`](bpmn_to_be.png) — renderização 2x (Retina) para visualização rápida no GitHub, documentações e relatórios.

---

## Fluxograma Visual do Processo TO-BE

```mermaid
flowchart TD
    subgraph Entrada["1. Canal de Entrada (Inbox)"]
        A([Documento Recebido: TXT / PDF / PNG])
    end

    subgraph IA["2. Camada de IA Multimodal (Gemini Flash)"]
        B[Extração de Dados Estruturados\nCache MD5 em Disco]
    end

    subgraph Regras["3. Motor de Regras Determinístico (Fase 7)"]
        C[Normalização de Texto e Códigos\nValidação de CPF/CNPJ e Datas]
        D[Casamento Fuzzy de Produtos\nRapidFuzz >= 85%]
        E{Qual a rota da triagem?}
    end

    subgraph Execucao["4. Robô RPA (Playwright)"]
        F[Preencher Telas do ERP Simulado\nChecagem de Idempotência e Screenshot]
        G([Pedido Cadastrado com Sucesso no ERP])
    end

    subgraph Revisao["5. Revisão Humana (Fase 9)"]
        H[Fila de Pendências do Supabase\nSplit View: Original vs Extraído\nCronômetro de Tempo Humano]
        I{Decisão do Operador?}
    end

    subgraph Descarte["6. Auditoria & Descarte"]
        J([Pedido Rejeitado e Arquivado])
    end

    A --> B
    B --> C
    C --> D
    D --> E

    E -->|AUTOMÁTICO: Confiança >= 85%| F
    E -->|REVISÃO: Ambíguo / Pendência| H
    E -->|REJEIÇÃO: Fraude / Ataque| J

    F --> G

    H --> I
    I -->|Corrigido / Aprovado| F
    I -->|Rejeitado| J
```
