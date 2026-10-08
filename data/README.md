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
