# Diário de Decisões e Aprendizados

## 2026-09-30
- **Decisão**: Utilização do `uv` como gerenciador de dependências e ambientes virtuais.
- **Por quê**: Padroniza os comandos entre o ambiente Windows (equipe) e Linux (meu), além de ser mais veloz e não exigir ativação manual de venv.
- **Aprendizado**: O `.env` guarda os segredos, então fica fora do git para evitar vazamento.

- **Revisão de Escopo:** Sprints do Trello alinhados com o cronograma de 12 Fases. Entrega final fixada para 10/11. Código será congelado em 23/10.

## 2026-10-01
- **Fase 1 e 2**: Implementado e populado o Supabase, e criado o ERP Simulado (FastAPI + Jinja2). Decidimos não cadastrar produtos no RPA para manter o padrão "Human-in-the-loop" de sistemas reais.
- **Fase 3 e 4**: Criado esqueleto do RPA (`rpa/bot.py`) e Guia (`docs/GUIA_RPA.txt`) para o Diogo. Definimos o Contrato (schema Pydantic `PedidoExtraido`) que conectará IA e Robô.

## 2026-10-08
- **Fase 5 e 6 concluídas**: Implementação da camada de IA com o Gemini (modelo `gemini-2.5-flash` congelado por estabilidade após erros 503 no 3.8).
- **Decisão (Cache)**: Criado um sistema local de cache em MD5 (`src/ipa/ai/cache.py`) para não consumir cota repetida da API nas chamadas já feitas do dataset de desenvolvimento.
- **Aprendizado (Rate Limit)**: Adicionado controle de concorrência (`time.sleep(4)`) no avaliador para lidar com o *rate limit* restrito (15 RPM) do "Free Tier" do Google AI Studio, provando que é possível testar o TCC sem custo.

## 2026-10-11
- **Integração RPA da Trilha B**: Importado o entregável de RPA (`rpa/bot.py`) e criada a suíte de validação de ponta a ponta (`teste_rpa.py`) com Playwright Chromium. Mantida a master como fonte da verdade estrita para dados e IA.
- **Higienização Visual e De-Slop**: Removidos micro-animações, switchers decorativos de dark mode e emojis nos logs do terminal para conferir sobriedade técnica ao software. O CSS do ERP foi recalibrado para alto contraste (fundo neutro sólido `#e2e8f0` e superfícies brancas com grades nítidas) seguindo diretrizes de acessibilidade WCAG e sistemas corporativos legados. Adicionado filtro Jinja2 de moeda brasileira (`R$`).
- **Fase 7 concluída (Motor de Regras e Roteamento)**: Criado o motor determinístico em `src/ipa/rules/` para agir como barreira de segurança contra alucinações de IA.
  - **Decisão (Fuzzy Matching)**: Adotada a biblioteca `rapidfuzz` para casamento aproximado contra o catálogo oficial `P-001` a `P-040`, com tolerância a apelidos e erros de digitação (corte automático em $\ge 85\%$).
  - **Validação Fiscal**: Implementado o cálculo oficial da Receita Federal para os dois dígitos verificadores de CPF e CNPJ.
  - **Triagem em 3 Vias**: O roteador classifica os pedidos em **AUTOMATICO** (despacho direto ao RPA), **REVISAO** (fila para operador humano) e **REJEICAO** (bloqueio de fraudes e prompt injection).
- **Qualidade e Testes**: Criada a suíte `tests/test_regras.py` rodando com 22 testes unitários no pytest com 100% de aprovação e zero regressão no robô Playwright.
