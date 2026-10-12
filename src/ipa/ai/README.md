# Camada de Inteligência Artificial (Fase 6)

Este diretório contém a camada de **Inteligência Artificial Multimodal** do TCC-IPA, responsável por transformar documentos desestruturados e bagunçados (mensagens de texto, ordens de compra em PDF e fotos de papel em PNG) em dados digitais perfeitamente estruturados.

---

## 1. O que a IA faz no sistema?
No dia a dia comercial, os pedidos chegam em formatos diversos: um PDF corporativo, uma foto tirada com celular de um bloco de notas ou uma mensagem rápida copiada de um aplicativo. Sistemas tradicionais de automação travam porque não sabem onde ler cada campo.

A nossa camada de IA utiliza o modelo de ponta **Google Gemini 2.5 Flash** para:
1. **Ler múltiplos canais (Multimodal):** Extrai informações de textos digitados, documentos PDF paginados e imagens escaneadas (usando Visão Computacional).
2. **Entender linguagem natural:** Interpreta quantidades, nomes de clientes e prazos mesmo quando o cliente comete erros de digitação, abrevia palavras ou omite detalhes óbvios.
3. **Respeitar o Contrato (Structured Outputs):** A IA não responde como um robô de bate-papo. Ela é configurada com esquemas rígidos do Pydantic (`PedidoExtraido`), forçando-a a devolver exatamente um objeto com campos como `cliente`, `itens` e `data_entrega`.

---

## 2. Estrutura dos Arquivos

| Arquivo | Função | O que ele faz na prática? |
| :--- | :--- | :--- |
| **`extractor.py`** | Extrator Multimodal | Conecta com o Google Gemini. Identifica se o documento é `.txt`, `.pdf` ou `.png` e aplica o pré-processamento correto. Envia as instruções e recebe a ficha técnica do pedido estruturada. |
| **`cache.py`** | Sistema de Cache em Disco | Calcula uma assinatura digital única (hash MD5) do arquivo analisado. Se aquele PDF ou imagem já foi processado antes, ele puxa o resultado instantaneamente do arquivo `.ai_cache.json` sem gastar a cota gratuita da API do Google. |

---

## 3. O Módulo de Cache e Limites da API
Para o experimento acadêmico do TCC, utilizamos o plano gratuito (**Free Tier**) do Google AI Studio, que impõe um limite de 15 requisições por minuto (15 RPM).

Para garantir que a equipe e a banca do TCC possam testar o sistema centenas de vezes sem custos e sem tomar erros de bloqueio (erro 429 ou 503):
- Ao processar `data/inbox/DOC-0001.pdf`, a resposta é gravada no arquivo `.ai_cache.json`.
- Em uma segunda execução, a resposta vem do disco em menos de **0.01 segundo**, sem gastar chamadas de internet.
- Se você quiser forçar a IA a pensar do zero novamente, basta deletar o arquivo `.ai_cache.json` na raiz do projeto.

---

## 4. Como testar a IA contra o Gabarito?
Para avaliar cientificamente a precisão da IA contra os gabaritos da pasta `data/gold/`, execute o script avaliador na raiz do projeto:

```bash
uv run python avaliador.py
```

O script testará os documentos e imprimirá a taxa de acertos e o tempo médio de resposta.
