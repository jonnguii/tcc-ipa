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
