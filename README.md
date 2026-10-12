# TCC-IPA

Projeto de automação inteligente para processar pedidos usando um ERP simulado,
um robô RPA e, nas próximas etapas, componentes de IA e orquestração.

Este guia descreve como preparar o ambiente, iniciar o ERP e executar o RPA no
Windows usando PowerShell.

## Pré-requisitos

- Windows 10/11
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado
- Acesso a um projeto Supabase configurado para este repositório

## 1. Preparar o projeto

Abra o PowerShell na raiz do repositório:

```powershell
cd C:\Projetos\tcc-ipa
```

Instale/sincronize as dependências:

```powershell
uv sync
uv run playwright install chromium
```

Configure as credenciais locais. Se ainda não existir `.env`, crie-o a partir
do exemplo:

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` com os valores do projeto
Supabase. Não compartilhe o `.env` nem publique suas chaves. Para executar
apenas o ERP e o RPA, não é necessário configurar as chaves Gemini.

**SOMENTE O ADMIN DO BANCO DE DADOS**
Na primeira configuração do Supabase, execute `supabase/schema.sql` pelo SQL
Editor do painel do Supabase e, depois, cadastre os dados iniciais:

```powershell
uv run python -m erp_sim.seed
```

O seed pode ser executado novamente: ele atualiza os produtos e clientes
usando seus códigos/documentos. O ERP usa o Supabase como banco; sem conexão,
credenciais válidas, schema e dados iniciais, as telas não vão carregar.

## 2. Iniciar o ERP

No primeiro terminal, na raiz do projeto:

```powershell
uv run uvicorn erp_sim.main:app --reload --port 8000
```

Deixe o terminal aberto enquanto estiver usando o sistema. Acesse:

- ERP: <http://localhost:8000>
- Novo pedido: <http://localhost:8000/pedidos/novo>
- Clientes: <http://localhost:8000/clientes>
- Produtos: <http://localhost:8000/produtos>

Para parar o servidor, volte ao primeiro terminal e pressione `Ctrl+C`.

## 3. Executar o robô RPA

Com o ERP ativo, abra **um segundo PowerShell**, também na raiz do projeto. O
bloco abaixo executa um pedido de demonstração. Antes de rodar, confirme na
tela `/clientes` que existe um cliente com ID `2`; ajuste o ID se necessário.
O produto `P-001` deve existir em `/produtos`.

```powershell
@'
from rpa.bot import executar

pedido = {
    "ref_id": "DEMO-20261008-01",
    "cliente": {"id": 2},
    "data_entrega": "2026-10-20",
    "itens": [{"codigo": "P-001", "quantidade": 2}],
}

print(executar(pedido))
'@ | uv run python -
```

O bloco PowerShell `@' ... '@` preserva as aspas do código Python. Isso evita
o problema de quoting que pode ocorrer ao passar o dicionário diretamente em
`python -c`.

O resultado inclui `status`, número do pedido, duração e, quando disponível,
o caminho da captura de tela. As evidências ficam em `rpa/evidencias/` (pasta
ignorada pelo Git).

### Executando com o script de teste

Você também pode executar o teste automatizado diretamente:

```bash
uv run python teste_rpa.py
```

Para ver o navegador em tempo real na tela:

- **Linux / macOS:** `RPA_HEADLESS=false uv run python teste_rpa.py`
- **Windows (PowerShell):** `$env:RPA_HEADLESS = "false"; uv run python teste_rpa.py`

## Problemas comuns

- **Erro de configuração do Supabase:** confira `SUPABASE_URL` e
  `SUPABASE_SERVICE_KEY` no `.env`; confirme que `supabase/schema.sql` foi
  executado e que o seed terminou.
- **Cliente não encontrado:** confira o ID em <http://localhost:8000/clientes>
  e atualize `pedido["cliente"]["id"]`.
- **Produto não encontrado:** confirme o código em
  <http://localhost:8000/produtos> e atualize `pedido["itens"]`.
- **Pedido duplicado:** escolha um `ref_id` ainda não usado.
- **Chromium não instalado:** execute `uv run playwright install chromium`.
- **Erro de sintaxe ao usar `python -c`:** use o bloco multilinha documentado
  acima no PowerShell.

## Mais informações

- Implementação do robô: `rpa/bot.py`
- Guia de desenvolvimento do RPA: `docs/GUIA_RPA.txt`
- Esquema do Supabase: `supabase/schema.sql`
- Progresso das fases: `docs/PROGRESSO.md`