# Orquestrador e Máquina de Estados (Fase 8)

Este diretório contém o **Orquestrador de Processos Inteligentes (IPA)** e a **Máquina de Estados**, atuando como a espinha dorsal que conecta a entrada de documentos, a camada de Inteligência Artificial, o motor de regras e a execução robótica.

---

## 1. Por que precisamos de um Orquestrador?
Em um sistema de automação empresarial, cada componente é especialista em uma tarefa:
- A IA lê documentos não estruturados.
- O Motor de Regras aplica conformidade e tolerância fuzzy.
- O Robô Playwright preenche telas.

Se não houver um componente central coordenando tudo, o sistema fica caótico e suscetível a falhas silenciosas. O **Orquestrador** garante que:
1. Os documentos sejam processados em ordem cronológica estrita.
2. Nenhuma etapa seja pulada.
3. Cada milissegundo de latência seja registrado para comprovação científica.
4. Falhas em um pedido não travem o restante do lote.

---

## 2. Estrutura dos Arquivos

| Arquivo | Função no Sistema | O que ele faz na prática? |
| :--- | :--- | :--- |
| **`estados.py`** | Definição da Máquina de Estados | Define os estados formais do ciclo de vida (`INICIADO`, `EXTRACAO_IA`, `REGRAS_TRIAGEM`, `EXECUTOR_RPA`, `REVISAO_HUMANA`, `REJEITADO`, `CONCLUIDO`, `FALHA`) e a matriz de transições permitidas. |
| **`handlers.py`** | Manipuladores de Cada Estágio | As funções isoladas que executam a chamada da IA, a execução das regras, o despacho ao robô ou o registro da pendência para revisão humana. |
| **`engine.py`** | Motor de Execução (`OrquestradorIPA`) | A classe principal que recebe um documento, inicializa a máquina de estados, transita entre as etapas, cronometra com `time.perf_counter()` e devolve o relatório final. |

---

## 3. Relação com o Diagrama BPMN 2.0
A máquina de estados em Python é um **espelho fiel** do fluxograma desenhado em [`docs/diagramas/bpmn_to_be.bpmn`](file:///home/jonnguii/Desktop/projects/tcc-ipa/docs/diagramas/bpmn_to_be.bpmn) (que pode ser aberto no site [bpmn.io](https://bpmn.io)). As raias do diagrama BPMN correspondem exatamente aos handlers deste módulo.

---

## 4. O Robô Falso (StubExecutor) e o Robô Real (RPA)
O orquestrador aceita qualquer executor que siga o contrato [`ExecutorPedido`](file:///home/jonnguii/Desktop/projects/tcc-ipa/src/ipa/contracts.py):
- **Modo STUB (Robô Simulado):** Simula em 0,05s a digitação no ERP em memória, permitindo testar a lógica do orquestrador e processar 50 pedidos em segundos sem abrir telas.
- **Modo RPA (Robô Real):** Dispara o robô Playwright real ([`rpa/bot.py`](file:///home/jonnguii/Desktop/projects/tcc-ipa/rpa/bot.py)) que abre o navegador Chromium e clica nas telas do ERP Simulado.

---

## 5. Como Executar e Testar?

### Rodar um lote no terminal:
```bash
uv run python -m src.ipa.run --limite 5 --executor stub
```

### Rodar os testes automatizados da máquina de estados:
```bash
uv run pytest tests/test_workflow.py -v
```
