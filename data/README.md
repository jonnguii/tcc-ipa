# Camada de Dados Sintéticos e Gabaritos (`data/`)

Este diretório contém os conjuntos de dados utilizados para treinamento, calibração e avaliação científica da arquitetura IPA.

---

## Estrutura de Pastas e Arquivos

```
data/
├── generator/          # Scripts determinísticos de geração de dados
│   ├── verdade.py      # Gera o gabarito ouro (data/gold/) e data/splits.json
│   ├── gerar_inbox.py  # Fabrica os 80 arquivos físicos (data/inbox/)
│   ├── templates.py    # Templates de mensagens com flags de negócio
│   └── ruido.py        # Algoritmos de ruído tipográfico e fonético
├── gold/               # Gold Standard (gabaritos oficiais DOC-0001 a DOC-0080 em JSON)
├── inbox/              # Documentos físicos de entrada (.txt, .pdf, .png)
├── splits.json         # Divisão estratificada fixa: 30 DEV / 50 TESTE
└── revisoes_local.json # Fallback local de persistência da fila de revisão humana
```

---

## 1. Padrão Ouro (`data/gold/`)
Contém 80 arquivos `.json` com a verdade absoluta de cada transação esperada.
Cada gabarito especifica:
- `id`: Identificador canônico (`DOC-0001` a `DOC-0080`).
- `categoria`: `limpo`, `ruidoso` ou `adversarial`.
- `tipo_arquivo`: `txt`, `pdf` ou `png`.
- `pedido_verdade`: Dados estruturados perfeitos (cliente, data de entrega, itens e quantidades).
- `rota_esperada`: `AUTOMATICO`, `REVISAO` ou `REJEICAO`.
- `flags`: Ocorrências de negócio específicas (`data_retroativa`, `item_fora_catalogo`, `cliente_incompleto`, `prompt_injection`, `nao_pedido`, `ruido_marketing`).

---

## 2. Caixa de Entrada (`data/inbox/`)
Armazena os 80 documentos físicos que alimentam a esteira do orquestrador.
- **Multimodalidade:** Distribuídos equilibradamente entre texto puro (.txt), documentos em PDF (.pdf) e imagens (.png).
- **Sem Gabarito Embutido:** Simulam o que chega por e-mail ou WhatsApp da empresa. O orquestrador precisa extrair, validar e rotear sem acesso prévio ao JSON de gabarito.

---

## 3. Divisão Experimental (`data/splits.json`)
O dataset foi estratificado deterministicamente para assegurar rigor acadêmico:
- **DEV (`DOC-0001` a `DOC-0030` - 30 docs):** Utilizado para desenvolvimento, calibração de prompts e testes unitários.
  - Distribuição: 24 Automático, 4 Revisão, 2 Rejeição (12 limpos, 12 ruidosos, 6 adversariais).
- **TESTE (`DOC-0031` a `DOC-0080` - 50 docs):** Congelado sob a tag `freeze-v1`, utilizado para os experimentos da Fase 11 (EXP1 a EXP7).
  - Distribuição: 38 Automático, 6 Revisão, 6 Rejeição (20 limpos, 20 ruidosos, 10 adversariais).

---

## 4. Reprodutibilidade e Regeneração
Para regenerar todo o dataset do zero mantendo perfeita fidelidade (Seed 42):

```bash
# 1. Gerar gabaritos e splits
uv run python data/generator/verdade.py

# 2. Fabricar os arquivos físicos da inbox
uv run python data/generator/gerar_inbox.py
```
