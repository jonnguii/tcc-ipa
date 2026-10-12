# Dicionário de Dados do TCC

Este arquivo explica o que cada parte da pasta `data/` faz. Ele foi escrito para ser didático, então se você não é da área de programação, conseguirá entender tudo.

## 1. O que é a pasta `gold`?
A pasta `gold` guarda o nosso **Gold Standard** (Padrão Ouro, ou seja, o gabarito inquestionável e perfeito). Dentro dela, temos 80 arquivos **JSON** (um formato de texto que organiza as informações em pares como se fosse uma ficha de cadastro, facilitando a leitura pelo computador). 

Cada JSON aqui representa a verdade absoluta de um pedido. Por exemplo, se o JSON diz que o pedido tem 10 copos, a Inteligência Artificial (IA) será obrigada a encontrar "10 copos" no texto bagunçado mais tarde. Se ela encontrar 9, nós marcaremos como um erro.

## 2. Como esse gabarito foi criado? (O script `verdade.py`)
Nós não usamos IA para criar o gabarito, para evitar que ela seja tendenciosa e acerte sempre de propósito. O gabarito foi criado pelo arquivo de código `verdade.py`. Esse código cruzou os nossos clientes e produtos e fez 80 sorteios.

Para garantir que o sorteio seja sempre o mesmo, nós usamos uma **seed** (semente, que é um número inicial em uma fórmula matemática que obriga o computador a gerar exatamente os mesmos resultados toda vez que alguém rodar o código, em vez de ser puramente aleatório). Usamos a seed 42. Assim, qualquer avaliador da banca do TCC pode rodar o nosso projeto e gerar os exatos mesmos 80 documentos.

## 3. O que são as Categorias do JSON?
Cada JSON no gabarito tem uma "categoria" que define o nível de dificuldade para a IA interpretar:

- **Limpo:** Um texto com português perfeito, sem abreviações ou gírias. Serve para provar que a IA funciona perfeitamente no cenário ideal.
- **Ruidoso:** Um texto que simula o mundo real de uma pequena empresa, com erros de digitação, falta de pontuação e abreviações (como "cx" para caixa). Isso serve para provar que a IA é melhor que um **RPA** tradicional (Automação Robótica de Processos, que é um robô "cego" que apenas clica na tela e preenche formulários rapidamente, mas que trava e dá erro se o texto não for escrito de forma exata).
- **Adversarial:** Textos feitos para enganar o sistema, como e-mails de propaganda ou clientes fazendo exigências absurdas. Serve para testar se o sistema sabe recusar problemas e passar para um humano avaliar.

## 4. O que são os Tipos de Arquivo?
O atributo `tipo_arquivo` diz por qual canal aquele pedido falso supostamente chegou:
- **txt:** Um e-mail comum ou uma mensagem de WhatsApp copiada (texto puro).
- **pdf:** Uma ordem de compra formal enviada em anexo. A IA precisará conseguir ler esse PDF.
- **png:** Uma foto do papel do pedido ou print de tela. Aqui a IA precisará usar Visão Computacional (capacidade de ler informações visuais e converter imagens em texto) para extrair os dados.

## 5. Como rodar a geração de dados localmente?
Para que os JSONs sejam gerados na sua máquina, abra o terminal na pasta raiz do projeto (`tcc-ipa`) e execute o seguinte comando:

```bash
uv run python data/generator/verdade.py
```
Isso fará o código Python ler as informações e cuspir os 80 arquivos `.json` de gabarito dentro da pasta `data/gold/`.

## 6. Como testar a extração da IA? (O script `avaliador.py`)
Agora que criamos a nossa IA (Fase 6), construímos o arquivo `avaliador.py` na raiz do projeto. Ele roda um teste comparando o que a IA extraiu dos arquivos de imagem/pdf/txt (da pasta `inbox`) contra o gabarito absoluto da pasta `gold`.

Para rodar a prova real:
```bash
uv run python avaliador.py
```

**Módulo de Cache:** A API do Gemini bloqueia requisições em massa no plano gratuito. Por isso, construímos o arquivo `src/ipa/ai/cache.py` (salvo no disco como `.ai_cache.json`). Ele salva a resposta de um PDF já analisado. Se o avaliador tentar analisar o mesmo arquivo duas vezes, ele puxa instantaneamente do cache em vez de gastar sua cota do Google.

## 7. O que é o Motor de Regras e Roteamento? (Fase 7)
Depois que a Inteligência Artificial lê o documento e extrai as informações brutas, nós **não** mandamos o pedido direto para o robô cadastrar no ERP. Seria arriscado confiar cegamente na IA, pois ela pode se enganar ou ser induzida ao erro por textos maliciosos.

Por isso, construímos o **Motor de Regras** (`src/ipa/rules/`). Ele funciona como um "filtro de segurança" ou um "gerente rigoroso" antes de qualquer lançamento:

### A. Normalização de Texto
O cliente pode escrever `"p-1"`, `"p01"`, `"P 001"` ou colocar acentos (`Açúcar`), gírias e pontuações estranhas. A normalização limpa o texto, tira os acentos e padroniza tudo para o código exato que o ERP reconhece (`P-001`), além de garantir que números com vírgula (ex: `3,5`) virem decimais corretos.

### B. Validação Fiscal e de Datas
Aqui o sistema checa as regras matemáticas e operacionais básicas:
- **CPF e CNPJ Válidos:** O sistema calcula os dígitos verificadores (a conta matemática oficial da Receita Federal) para garantir que ninguém inventou um número falso.
- **Datas Coerentes:** Bloqueia pedidos com datas no passado ou calendários impossíveis (como 29 de fevereiro em ano não bissexto).
- **Quantidades Reais:** Garante que a quantidade seja um número positivo (ninguém compra `-2` unidades).

### C. Casamento Fuzzy (O que é "Fuzzy Matching"?)
Imagine que o catálogo do ERP só possui cadastrado o nome `"Produto 1"`, mas no WhatsApp o cliente escreveu `"prod 01"` ou com um erro de digitação como `"Prduto 1"`. Um sistema tradicional não acharia nada e travaria.
O **Fuzzy Matching** (casamento aproximado ou "busca difusa", calculado pela biblioteca **RapidFuzz**) compara as palavras letra por letra e calcula uma nota de similaridade de 0 a 100%:
- **Score $\ge$ 85% (Alta Certeza):** O sistema tem certeza de qual produto se trata e faz a correção automática do código para o ERP.
- **Score entre 70% e 84% (Ambíguo):** O sistema desconfia de qual produto seja, mas não tem certeza suficiente para bater o martelo sozinho.
- **Score $<$ 70% (Não Encontrado):** O produto é considerado inexistente no catálogo.

### D. Roteamento (A Decisão Final do Pedido)
O **Roteamento** é a triagem que decide qual destino cada pedido terá, separando em 3 vias:
1. **Automático (Via Verde):** Todos os dados estão 100% corretos, o cliente existe, a data é futura e os produtos foram identificados com certeza ($\ge 85\%$). O pedido vai direto para o robô RPA preencher a tela do ERP sem precisar de ninguém no teclado.
2. **Revisão Humana (Via Amarela):** O cliente é novo mas faltou o e-mail, ou a data de entrega é retroativa, ou o nome do produto é duvidoso (ambíguo). Em vez de cadastrar errado ou travar, o pedido vai para uma fila de pendências para um operador humano analisar.
3. **Rejeição (Via Vermelha):** O documento está em branco, é um e-mail de propaganda sem itens, tem CPF comprovadamente fraudulento ou é uma tentativa de ataque (*Prompt Injection*, quando tentam mandar o sistema apagar o banco de dados). O pedido é cancelado imediatamente com o motivo registrado para auditoria.

### Como testar as regras e o roteamento?
Você pode rodar os 22 testes automatizados pelo terminal:
```bash
uv run pytest -v
```
Todos os cenários (pedidos perfeitos, pedidos com erros de digitação, pedidos para revisão e tentativas de ataque) são validados em frações de segundo.

## 8. A Esteira Completa: Do Documento ao ERP (Visão Geral de Ponta a Ponta)
Para entender como tudo se conecta em um processo contínuo, imagine uma empresa real recebendo pedidos todos os dias:

```
[1. Documento Chega] ──> [2. IA Interpreta] ──> [3. Regras Filtram] ──> [4. Robô Digita no ERP]
(data/inbox/)            (src/ipa/ai/)           (src/ipa/rules/)         (rpa/bot.py -> erp_sim/)
                                                        │
                                                        ├── Se ambíguo: Fila de Revisão Humana
                                                        └── Se fraude: Rejeitado e Arquivado
```

1. **Chegada do Documento (`data/inbox/`):** O cliente envia um pedido por foto de papel (PNG), ordem de compra (PDF) ou mensagem de WhatsApp (TXT).
2. **Leitura Inteligente (`src/ipa/ai/`):** A Inteligência Artificial (Google Gemini) lê o documento com visão computacional e extrai os dados sem inventar conversa, montando uma ficha técnica estruturada.
3. **Filtro de Segurança e Triagem (`src/ipa/rules/`):** O Motor de Regras analisa a ficha:
   - Limpa o texto e padroniza os códigos dos produtos.
   - Faz a conta matemática oficial da Receita Federal para checar se o CNPJ/CPF é verdadeiro.
   - Usa o **RapidFuzz** para tolerar erros de digitação e casar o nome com o catálogo oficial.
   - Decide a rota: **Automático** (vai pro robô), **Revisão** (vai pra um humano olhar) ou **Rejeição** (cancela).
4. **Execução no ERP pelo Robô (`rpa/` -> `erp_sim/`):** Se aprovado no fluxo automático, o robô Playwright abre o navegador, navega até o formulário do ERP, digita tudo com precisão, salva o pedido e tira uma foto da tela como comprovante.
5. **Comprovação Científica (`data/gold/`):** Com o script `avaliador.py`, nós comparamos o que o sistema fez contra o gabarito perfeito (`gold`). Isso gera as notas científicas do TCC (quantos pedidos foram acertados, quantos foram corrigidos e o tempo economizado).

## 9. O que cada pasta do projeto faz? (Mapa Rápido)
Se você estiver navegando pelo projeto pela primeira vez, aqui está o resumo do que cada pasta contém:

- **`data/inbox/`**: A "caixa de entrada" com os 80 pedidos dos clientes (textos, PDFs e fotos).
- **`data/gold/`**: O "gabarito perfeito" com a verdade absoluta de cada pedido para checagem científica.
- **`data/generator/`**: Os códigos que criaram os 80 documentos e o gabarito usando fórmulas matemáticas idênticas (seed 42).
- **`src/ipa/ai/`**: Onde fica o "cérebro" da IA (conexão com a API do Gemini e o sistema de cache de economia).
- **`src/ipa/rules/`**: Onde fica o "gerente de regras" (validação de CPF/CNPJ, datas, RapidFuzz e decisões).
- **`rpa/`**: Onde fica o "robô digitador" (código Playwright que preenche as telas do ERP e salva comprovantes).
- **`src/ipa/workflow/`**: Onde fica o "maestro da fábrica" (a máquina de estados que orquestra a passagem do pedido de uma etapa para a outra).
- **`docs/diagramas/`**: Onde fica o fluxograma visual oficial de processos (BPMN 2.0) que pode ser aberto no site bpmn.io.
- **`tests/`**: Os testes automatizados que comprovam que nada no sistema está quebrado (`uv run pytest`).

## 10. O que é o Orquestrador e o BPMN? (Fase 8)

### O Maestro da Fábrica (O Orquestrador)
Imagine uma linha de produção industrial: não adianta ter o motor mais potente e as melhores peças se não houver uma **esteira rolante** que leve o carro de um setor ao outro na ordem correta. 

O **Orquestrador** (`src/ipa/workflow/`) é o maestro do sistema. Em vez de você ter que rodar a IA na mão, depois rodar o validador na mão e depois ligar o robô na mão, o Orquestrador faz tudo sozinho em sequência:
1. Pega o documento que chegou na pasta `inbox/`.
2. Chama a Inteligência Artificial para ler.
3. Passa o resultado pelo Motor de Regras e RapidFuzz.
4. Despacha para o robô cadastrar ou envia para a fila de revisão humana.
5. Mede no cronômetro quantos segundos cada etapa demorou para gerar as estatísticas do TCC.

### A Máquina de Estados (Proibido Pular Etapas!)
Para evitar falhas e bagunça, o Orquestrador usa um conceito clássico da computação chamado **Máquina de Estados**. 
Pense nisso como um "crachá" que o documento carrega enquanto viaja pela esteira:
- Ele começa com o crachá **`INICIADO`**.
- Passa para **`EXTRACAO_IA`**.
- Depois para **`REGRAS_TRIAGEM`**.
- Se for aprovado, vai para **`EXECUTOR_RPA`**.
- Só quando o robô confirma o cadastro ele ganha o crachá final **`CONCLUIDO`**.

A regra de ouro é: **um documento é proibido de pular etapas**. Ele nunca pode ir direto do início para o robô sem antes passar obrigatoriamente pela validação de regras.

### O que é o Diagrama BPMN?
BPMN (*Business Process Model and Notation*) é a linguagem visual internacional usada por consultores de negócios e engenheiros para desenhar processos com caixinhas e setas. 

Nós desenhamos o fluxo completo da nossa esteira no padrão oficial da OMG:
- O arquivo [`docs/diagramas/bpmn_to_be.bpmn`](file:///home/jonnguii/Desktop/projects/tcc-ipa/docs/diagramas/bpmn_to_be.bpmn) pode ser arrastado e aberto diretamente no site gratuito [bpmn.io](https://bpmn.io).
- O código em Python da máquina de estados foi programado para ser um **espelho exato** desse desenho.

### O que é o "Robô Falso" (Stub)?
Para testar 10 ou 50 pedidos de uma vez, se tivéssemos que abrir o navegador de verdade a cada pedido, o teste demoraria muitos minutos. 
Por isso, construímos o **StubExecutor** (um "dublê" do robô). Ele simula em 0,05 segundo que clicou na tela do ERP e devolve o número do pedido gerado, permitindo que a gente teste a lógica do sistema inteiro em alta velocidade.

### Como testar o Orquestrador em lote?
Para ver a esteira inteira processando documentos da pasta `inbox`:
```bash
uv run python -m src.ipa.run --limite 5 --executor stub
```
Isso mostrará na tela uma tabela com cada documento, a rota que o sistema escolheu e o tempo que ele levou em frações de segundo.

## 11. O que é a Revisão Humana e o Split View? (Fase 9)

### A Cabine de Inspeção (Human-in-the-Loop)
Em uma fábrica de automóveis, a maior parte da montagem é feita por braços robóticos velozes. Mas se um sensor nota que um parafuso ficou torto ou que a cor parece diferente, a esteira desvia aquele chassi para uma **cabine de inspeção manual**, onde um especialista humano olha de perto com calma.

O conceito de **Human-in-the-Loop (Humano no Circuito)** é exatamente isso:
- A Inteligência Artificial faz 90% do trabalho pesado e repetitivo em segundos.
- Mas quando o cliente mandou um texto confuso, uma data no passado ou um nome de produto muito esquisito, a IA **não tenta adivinhar** e nem joga lixo no banco de dados.
- O pedido vai para a **Fila de Revisão Humana** (`/revisoes`).

### O que é a Tela de Split View (Visão Lado a Lado)?
Revisar pedido abrindo dez abas diferentes ou alternando janelas no Windows cansa a visão e causa erros humanos. 

Por isso criamos o **Split View** (`/revisoes/{id}`):
1. **Lado Esquerdo:** O papel ou texto original do fornecedor, do jeitinho que ele mandou.
2. **Lado Direito:** O que a IA entendeu, com os campos já organizados e botões fáceis.
3. **Alertas em Amarelo:** Se o produto teve uma pontuação duvidosa (score menor que 85%), o campo ganha um crachá de aviso para o operador bater o olho imediatamente naquele ponto crítico.
4. **O Cronômetro Invisível:** Enquanto o operador humano analisa e corrige os campos, um cronômetro mede com precisão quantos segundos foram gastos. Isso serve para provar cientificamente no TCC quanto tempo a empresa economizou com a automação.

### O que o operador faz?
- **Aprovar e Despachar ao Robô:** O operador confere, ajusta se necessário e clica em Aprovar. O robô da esteira acorda na hora e cadastra o pedido no ERP.
- **Rejeitar Pedido:** Se for um e-mail falso ou tentativa de golpe, o operador rejeita com justificativa, ficando tudo arquivado para segurança e auditoria.

## 12. O Dublê vs. O Robô de Verdade (Fase 10)

### O Dublê (Stub) vs. O Ator Principal (Playwright)
Imagine a produção de um filme com cenas complexas:
- Nos ensaios técnicos de iluminação e posicionamento de câmera, a equipe usa um **boneco de teste ou dublê** para não cansar o ator principal. No nosso sistema, esse é o **`StubExecutor`**: ele responde em 50 milissegundos, simula a gravação e permite testar todo o fluxo do sistema sem gastar memória nem abrir navegadores.
- No dia da gravação oficial, entra em ação o **ator principal**. No nosso sistema, esse é o **Robô Real (`rpa/bot.py`)**, operado pelo **Playwright Chromium**:
  1. Ele abre uma janela real de navegador (em modo *headless* silencioso ou visível);
  2. Acessa a tela de pedidos do ERP (`http://localhost:8000/pedidos/novo`);
  3. Preenche a Razão Social, a Data de Entrega e a Referência Externa;
  4. Adiciona cada linha de produto e sua respectiva quantidade;
  5. Clica no botão Salvar e aguarda a mensagem verde de confirmação;
  6. Tira uma foto da tela inteira (*screenshot*) e salva na pasta `rpa/evidencias/` como comprovante irrefutável de auditoria.

### O que é Idempotência Zero (Proteção Anti-Duplicidade)?
Se a energia cair no meio do processamento ou o operador clicar no botão duas vezes sem querer, uma empresa comum corre o risco de faturar duas vezes o mesmo pedido e mandar dois caminhões de entrega por engano.

Para impedir isso, o robô possui **Idempotência Garantida**:
- Antes de encostar em qualquer botão de cadastro, o robô abre a consulta do ERP (`/pedidos?ref=DOC-XXXX`).
- Se o pedido já existir no banco, ele aborta a criação imediatamente, anota o status como `duplicado`, reaproveita o número oficial já existente e não gera nenhuma linha a mais no banco.

### Como rodar o lote com o robô de verdade?
No terminal, basta trocar `--executor stub` por `--executor rpa`:
```bash
uv run python -m src.ipa.run --limite 5 --executor rpa
```
Se rodar o mesmo comando pela segunda vez consecutiva, você verá todos os documentos mudando para `duplicado` em frações de segundo, comprovando a proteção patrimonial da empresa.



