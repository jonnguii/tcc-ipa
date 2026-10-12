# Robô RPA de Automação de Interface (Fase 3)

Este diretório contém o robô **RPA (Robotic Process Automation)** do TCC-IPA, desenvolvido com **Playwright**, responsável por abrir o navegador web e preencher os pedidos aprovados diretamente na tela do ERP corporativo, simulando um funcionário humano ultrarrápido.

---

## 1. O que é um Robô RPA e por que ele é "Cego"?
No contexto corporativo, sistemas legados ou ERPs tradicionais muitas vezes não possuem APIs modernas para integração direta. A automação via RPA resolve isso interagindo com a interface gráfica do sistema (clicando em botões, preenchendo campos de texto e submetendo formulários).

O robô é intencionalmente **"cego"**:
- Ele não toma decisões de negócio complexas.
- Ele não tenta adivinhar o que o cliente quis dizer.
- Ele recebe a ficha técnica já 100% higienizada e aprovada pelo Motor de Regras (Fase 7) e apenas executa o preenchimento na tela.

---

## 2. Como o Robô funciona no ERP?

Quando a função `executar(pedido)` do arquivo `bot.py` é chamada:
1. **Checagem Anti-Duplicidade:** O robô entra na tela de listagem `/pedidos` e busca se a referência externa (`ref_id`) já foi cadastrada anteriormente. Se já existir, ele bloqueia o cadastro e retorna `status: duplicado` imediatamente, impedindo compras repetidas.
2. **Identificação ou Cadastro de Cliente:** Ele acessa a tela `/clientes`. Se for um cliente novo, ele navega até `/clientes/novo`, digita o nome, CNPJ/CPF e e-mail e salva o cadastro antes de prosseguir.
3. **Preenchimento do Formulário de Pedido:** Ele entra em `/pedidos/novo`, seleciona o cliente no menu suspenso, informa a data de entrega, preenche as linhas de produtos e quantidades, e clica em **"Salvar Pedido"**.
4. **Captura de Evidência (Screenshot):** Logo após o envio, o robô captura uma foto completa da tela do ERP e salva em `rpa/evidencias/` com o nome da referência do pedido (ex: `rpa/evidencias/TESTE-RPA-123.png`). Essa foto serve como comprovante de auditoria para o TCC e para a empresa.

---

## 3. Como executar e testar o Robô?

### Pré-requisito: O ERP precisa estar ligado
Em um terminal, certifique-se de que o ERP está em execução:
```bash
uv run uvicorn erp_sim.main:app --port 8000
```

### Executando o teste automatizado (Modo Invisível / Padrão):
Abra outro terminal e execute:
```bash
uv run python teste_rpa.py
```
O robô executará em segundo plano (headless) em cerca de 4 segundos e exibirá o comprovante e o número do pedido gerado no terminal.

### Assistindo o robô trabalhar ao vivo na sua tela (Modo Visível):
Para demonstrar para a banca examinadora do TCC ou para ver o navegador abrindo e digitando em tempo real:

- **Linux / macOS:**
  ```bash
  RPA_HEADLESS=false uv run python teste_rpa.py
  ```
- **Windows (PowerShell):**
  ```powershell
  $env:RPA_HEADLESS = "false"; uv run python teste_rpa.py
  ```
