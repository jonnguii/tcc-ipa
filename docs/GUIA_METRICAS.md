# Guia Prático: Experimento Manual e Redação do TCC



1. **Operadora do Experimento 1 (Linha de Base do "Antes"):** Digitar 30 pedidos de compra na tela do ERP corporativo com cronômetro para medir o tempo manual real gasto por um ser humano.
2. **Redação dos Capítulos de Resultados e Discussão:** Utilizar os dados e tabelas geradas em `results/RESULTADOS.md` para escrever o texto da monografia.

---

## 2. Passo a Passo de Instalação (5 minutos)

### Passo 0: Instalar o gerenciador `uv`
O projeto utiliza o gerenciador ultrarrápido `uv` (não usamos pip tradicional).
- **No Windows (PowerShell como Administrador ou usuário normal):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **No Linux / macOS (Terminal):**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
*(Feche e abra novamente o seu terminal após a instalação).*

### Passo 1: Clonar o Repositório e Sincronizar
Abra o terminal na sua pasta de projetos:
```bash
git clone git@github.com:jonnguii/tcc-ipa.git
cd tcc-ipa
uv sync
```

### Passo 2: Configurar o `.env`
Copie o arquivo de exemplo para criar seu arquivo de configuração:
- **No Windows (PowerShell):** `copy .env.example .env`
- **No Linux / macOS:** `cp .env.example .env`

Abra o arquivo `.env` e confirme se os dados de `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` fornecidos pelo João estão preenchidos.

---

## 3. Executando a Coleta Empírica de Tempo (EXP1)

Para o TCC ter validade científica e provar que a automação economiza tempo de verdade, você vai simular uma atendente de distribuidora cadastrando pedidos que chegam por mensagem.

### Passo A: Ligar o ERP Corporativo (Terminal 1)
Deixe este terminal aberto e rodando durante toda a coleta:
```bash
uv run uvicorn erp_sim.main:app --reload --port 8000
```
Abra o seu navegador de internet no endereço: **<http://localhost:8000/pedidos/novo>**

---

### Passo B: Rodar a Coleta no Cronômetro (Terminal 2)

Abra um **segundo terminal** na pasta do projeto e execute os 3 lotes de 10 pedidos cada.

> 💡 **Dica:** O script possui **retomada automática**. Se você precisar pausar ou der `Ctrl+C` no meio, ao rodar de novo ele pula os pedidos que você já terminou e continua exatamente de onde parou!

#### Lote 1 (Pedidos 1 a 10):
```bash
uv run python eval/exp1_manual.py --participante "Seu Nome" --lote 1
```

**Como funciona a dinâmica a cada pedido:**
1. O terminal vai imprimir o texto do pedido dentro de uma caixa formatada (ex: cliente, produtos solicitados e data de entrega).
2. Aperte `<ENTER>` no terminal -> **o cronômetro começa a contar!**
3. Vá para a janela do navegador em `http://localhost:8000/pedidos/novo`, selecione o cliente no menu, adicione os produtos e quantidades, coloque a data e clique no botão verde **"Salvar Pedido"**.
4. Assim que a tela confirmar que o pedido foi criado, volte para o terminal e aperte `<ENTER>` -> **o cronômetro para e salva os segundos exatos!**
5. O terminal vai perguntar se houve dúvida/erro de digitação (`0` = Não, `1` = Sim). Responda com sinceridade (dúvidas em abreviações são normais e esperadas!).
6. Isso se repete para os 10 pedidos do lote (leva cerca de 10 a 12 minutos).

#### Lote 2 (Pedidos 11 a 20):
De uma pausa, pois o cansaço pode influenciar no desempenho e rode o segundo lote:
```bash
uv run python eval/exp1_manual.py --participante "Seu Nome" --lote 2
```

#### Lote 3 (Pedidos 21 a 30):
Finalize os últimos 10 pedidos:
```bash
uv run python eval/exp1_manual.py --participante "Seu Nome" --lote 3
```

---

## 4. Gerando as Tabelas Finais do TCC

Assim que você terminar os 3 lotes, execute este comando no terminal:
```bash
uv run python eval/charts.py
```

Pronto! Todas as tabelas estatísticas do TCC serão recalculadas instantaneamente com os seus tempos reais.

---

## 5. Onde encontrar o material para escrever a Monografia?

Abra o arquivo consolidado em:
👉 **`results/RESULTADOS.md`**

Lá você encontrará todas as tabelas prontas em formato Markdown para copiar e colar no seu documento:
- **Tabela T1 (Produtividade):** Compara o seu tempo médio e mediano contra os 9 segundos do robô IPA (demonstrando um speed-up de 7x a 9x mais rápido).
- **Tabela T2 (Regex vs IA):** Mostra como regras antigas de Regex falham em mensagens com gírias (F1 de 0.29), enquanto a IA generativa alcança F1 superior a 0.85.
- **Tabela T3 (Métricas de Extração):** Precisão, Revocação e F1-Score por campo (cliente, data, produtos).
- **Tabela T4 (Curva de Limiares):** Explica a escolha da confiança de 85% para balancear automação sem erros.
- **Tabela T5 (Resiliência RPA):** Demonstra como o robô tolera lentidão de servidor sem quebrar.
- **Tabela T6 (Custos):** Demonstra que cada pedido custa frações de centavos de real via IA.

Qualquer dúvida durante a operação, o João (Líder Técnico) e a equipe de desenvolvimento estão à disposição! Bom trabalho! 🚀
