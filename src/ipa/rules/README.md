# Motor de Regras e Roteamento Determinístico (Fase 7)

Este diretório contém a camada de **Regras e Roteamento** do TCC-IPA. Ele foi construído para ser o filtro de segurança determinístico do sistema, garantindo que nenhuma alucinação de Inteligência Artificial ou dado inconsistente entre no ERP da empresa.

---

## 1. Por que precisamos de um Motor de Regras?
Uma Inteligência Artificial (como o Gemini ou ChatGPT) é excelente para ler e entender linguagem natural desorganizada, mas ela tem um ponto fraco: **não é determinística**. Ela pode errar um dígito de um documento, alucinar um produto que não existe no estoque ou cair em armadilhas de texto malicioso.

O **Motor de Regras** é 100% código matemático e regras de negócio lógicas (sem IA). Ele atua como um portão de checagem obrigatório: só passa o que estiver rigorosamente validado.

---

## 2. Estrutura dos Módulos

| Arquivo | Função no Sistema | O que ele faz na prática? |
| :--- | :--- | :--- |
| **`normalizar.py`** | Limpeza de Texto e Dados | Remove acentuação (`Açúcar` $\rightarrow$ `Acucar`), tira pontuação excessiva, converte para caixa baixa e padroniza códigos de produtos (`p-1` $\rightarrow$ `P-001`). Converte também valores com vírgula (`3,5` $\rightarrow$ `3.5`). |
| **`validar.py`** | Validação Fiscal e Temporal | Executa o cálculo matemático oficial dos dois dígitos verificadores da Receita Federal para **CPF** e **CNPJ**, impedindo cadastros falsos. Valida se a data de entrega é válida no calendário e se não é no passado. |
| **`resolver.py`** | Casamento de Catálogo (RapidFuzz) | Cruza o nome escrito pelo cliente contra os 40 produtos oficiais do ERP (`P-001` a `P-040`). Usa o algoritmo **RapidFuzz** para tolerar erros de digitação e abreviações com uma nota percentual de confiança. |
| **`rotear.py`** | Decisão Final do Destino | Aplica a árvore de decisão e classifica o pedido em uma das 3 vias operacionais: **AUTOMATICO**, **REVISAO** ou **REJEICAO**. Bloqueia também tentativas de *Prompt Injection*. |

---

## 3. Como funciona o Casamento Fuzzy (RapidFuzz)?
Em situações do mundo real, os clientes raramente digitam o código exato `P-001`. Eles escrevem apelidos, abreviações ou cometem erros de digitação (ex: `"prod 1"`, `"Produto 01"`, `"refri cola"`).

O algoritmo calcula a distância e semelhança entre as palavras e atribui uma nota de 0 a 100%:
- **Score $\ge$ 85% (Alta Certeza):** O sistema substitui o texto pelo código oficial do ERP automaticamente.
- **Score entre 70% e 84% (Ambíguo):** O sistema identifica que é parecido, mas não tem certeza suficiente para cadastrar sozinho. O pedido é enviado para um ser humano revisar.
- **Score $<$ 70% (Não Encontrado):** O produto é considerado inexistente no catálogo.

---

## 4. As Três Vias de Roteamento

1. **AUTOMATICO:** 
   - Cliente cadastrado e validado no ERP (ou novo com dados 100% íntegros).
   - Todos os produtos casados com $\ge 85\%$ de confiança.
   - Quantidades positivas e data futura válida.
   - **Ação:** O pedido é imediatamente despachado para o robô RPA preencher no ERP.

2. **REVISAO:** 
   - Produto com similaridade ambígua ($70\text{--}84\%$) ou não encontrado.
   - Data de entrega retroativa (anterior ao dia de hoje).
   - Cliente novo com e-mail ou nome ausentes.
   - **Ação:** Encaminhado para a fila de pendências para validação por um operador humano (Fase 9).

3. **REJEICAO:** 
   - Pedido vazio (sem nenhum item).
   - CPF/CNPJ com dígitos verificadores matematicamente fraudulentos.
   - Tentativa de injeção adversarial (ex: mensagens mandando ignorar regras ou apagar o banco).
   - **Ação:** O pedido é recusado e arquivado com o motivo da rejeição gravado para auditoria.

---

## 5. Como rodar os Testes Unitários
Para validar que todos os 22 cenários de regras, validações fiscais e casamento fuzzy continuam funcionando perfeitamente:

```bash
uv run pytest -v
```
