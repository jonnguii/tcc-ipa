# ERP Simulado (Fase 2)

Este diretório contém o **ERP Simulado (Enterprise Resource Planning)** do TCC-IPA, construído especificamente para servir como o ambiente empresarial de teste e validação onde o robô RPA opera e onde os pedidos são cadastrados.

---

## 1. Por que construir um ERP Simulado próprio?
Em um projeto de pesquisa acadêmica e engenharia, utilizar um sistema comercial fechado e de grande porte (como SAP, Protheus ou Oracle) traria três grandes problemas:
1. **Custo e Licenciamento:** Exigiria servidores pesados e licenças comerciais inviáveis para avaliação aberta.
2. **Falta de Controle Experimental:** Não permitiria reiniciar o banco de dados do zero com dados conhecidos a qualquer momento para garantir a reprodutibilidade dos testes.
3. **Impossibilidade de Simular Falhas:** Em sistemas fechados, não conseguiríamos simular lentidão de rede e sabotagens propositais para testar a resiliência do robô.

O nosso ERP foi feito em **FastAPI** (Python) com **Jinja2** e banco de dados **Supabase (PostgreSQL)**, fornecendo uma aplicação corporativa leve, rápida e com fidelidade ao mundo real.

---

## 2. Telas e Funcionalidades

- **`/pedidos`**: Listagem completa de todos os pedidos já faturados, com número sequencial (`#1`, `#2`), cliente, data de entrega, total em Reais (`R$`) e referência externa única.
- **`/pedidos/novo`**: Formulário de digitação de novo pedido, onde o robô RPA clica e insere produtos e quantidades.
- **`/pedidos/{id}`**: Tela de detalhamento de um pedido específico, listando todos os itens, quantidades, preços unitários e subtotais.
- **`/clientes` e `/clientes/novo`**: Cadastro e listagem de clientes (com validação de nome, e-mail e CNPJ/CPF).
- **`/produtos` e `/produtos/novo`**: Catálogo de 40 produtos cadastrados (`P-001` até `P-040`) com unidades e preços em Reais.

---

## 3. Design Clássico de ERP e Acessibilidade (WCAG)
Em vez de seguir modismos visuais de páginas modernas (muitas vezes cheias de animações desnecessárias ou cores desbotadas), o ERP foi estilizado em [`erp_sim/static/style.css`](file:///home/jonnguii/Desktop/projects/tcc-ipa/erp_sim/static/style.css) com foco rigoroso em ergonomia e acessibilidade de sistemas legados:
- **Plano de Fundo Neutro Sólido (`#e2e8f0`):** Garante que todas as janelas, tabelas e formulários brancos (`#ffffff`) saltem aos olhos com contorno firme e legibilidade imediata.
- **Linhas de Grade Estruturadas:** Tabelas com bordas visíveis em todas as células, estilo planilha corporativa clássica.
- **Formatação Monetária com Cifrão:** Todos os valores e totais são formatados no padrão brasileiro (`R$ 15,00`, `R$ 1.387,50`).
- **Seletores RPA Estáveis:** Todos os botões e campos possuem atributos `data-testid` que nunca se alteram, garantindo que o robô Playwright nunca quebre por mudanças visuais.

---

## 4. O Middleware de Sabotagem (Teste de Resiliência)
Para o experimento científico do TCC, o arquivo `main.py` possui uma trava configurável:
- Se a variável `ERP_SABOTAGE="slow"` for ativada no `.env`, o ERP propositalmente congela por 3 segundos a cada envio de formulário.
- Isso serve para testar se o robô Playwright sabe esperar pacientemente a resposta do servidor ou se ele trava por *timeout*.

---

## 5. Como iniciar o ERP localmente?

Na raiz do projeto:
```bash
uv run uvicorn erp_sim.main:app --reload --port 8000
```
Acesse no seu navegador: <http://localhost:8000>
