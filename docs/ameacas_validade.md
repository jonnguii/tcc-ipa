# Ameaças à Validade da Pesquisa Experimental

Este documento descreve sistematicamente as potenciais ameaças à validade científica dos experimentos conduzidos no âmbito do Trabalho de Conclusão de Curso (TCC) intitulado **"Arquitetura de Automação Inteligente de Processos (IPA) para Triagem e Lançamento de Pedidos em MPMEs"**, fundamentando-se nas diretrizes metodológicas de Engenharia de Software Experimental propostas por **Wohlin et al. (2012)**.

A análise abrange quatro dimensões essenciais: **Validade de Conclusão Estatística**, **Validade Interna**, **Validade de Construto** e **Validade Externa**, apresentando com total transparência os limites do estudo e as contramedidas técnicas adotadas.

---

## 1. Validade de Conclusão Estatística (Statistical Conclusion Validity)

A validade de conclusão estatística diz respeito à correção das conclusões relativas à existência de relacionamento matemático ou causal entre o tratamento proposto (a esteira IPA) e o resultado operacional observado (tempo, acurácia e segurança).

### 1.1 Tamanho Amostral e Poder Estatístico
- **Ameaça**: A utilização de 50 documentos no conjunto de teste e 30 pedidos pareados no experimento de produtividade (EXP1) poderia ser considerada amostra moderada quando contrastada com bancos de dados massivos de grandes corporações.
- **Mitigação**: No contexto de MPMEs brasileiras, o volume diário típico de pedidos recebidos via WhatsApp e e-mail varia entre 10 e 50 pedidos. A amostra de 30 pedidos no EXP1 representou uma jornada de digitação de cerca de 40 minutos para o operador humano, suficiente para evidenciar fadiga cognitiva e variabilidade temporal estatisticamente significativa ($p < 0,001$ no teste não-paramétrico de postos de Wilcoxon para amostras pareadas). Para a extração da IA (EXP2 a EXP4), 50 documentos com múltiplos itens por pedido representam mais de 150 instâncias de produtos e entidades avaliadas campo a campo.

### 1.2 Variabilidade Temporal de Rede vs. Modo Replay Offline
- **Ameaça**: A latência de chamadas em nuvem para APIs de LLMs (como o Google Gemini) sofre variações decorrentes de oscilações na conexão de internet, congestionamento dos data centers do provedor e enfileiramento de requisições sob cotas de teste (*rate limits* de 15 RPM).
- **Mitigação**: O projeto adotou instrumentação dupla:
  1. **Modo Live Empírico (EXP1 e EXP7)**: Medição do tempo real ponta a ponta com chamada de rede, registrando a mediana de 8,95s na inferência da IA e 9,03s no pipeline completo;
  2. **Modo Replay Determinístico (EXP3 e EXP4)**: Armazenamento em cache criptográfico (MD5) de 100% dos payloads das respostas da IA, garantindo repetibilidade matemática idêntica, execução offline independente de conexão externa e isolamento estrito de latência computacional local (0,14s de motor de regras).

### 1.3 Confiabilidade da Instrumentação de Medição
- **Ameaça**: Erros de relógio ou overhead de profiling poderiam distorcer frações de segundo nas etapas de validação.
- **Mitigação**: Todas as métricas de tempo da esteira automatizada foram colhidas utilizando o timer de precisão monotônica de hardware `time.perf_counter()` em Python, imune a saltos no relógio do sistema operacional (NTP). Na tela de revisão humana (`/revisoes/{id}`), o tempo foi cronometrado via JavaScript e gravado no backend em milissegundos.

---

## 2. Validade Interna (Internal Validity)

A validade interna avalia se o efeito observado sobre a variável de saída (ex: 0% de erro residual no ERP e 8,2x de speed-up) foi decorrente exclusivamente da arquitetura de software proposta, e não de variáveis de confusão ou vieses de experimentação.

### 2.1 Uso de Dados Sintéticos e Prevenção de Vazamento (Data Leakage)
- **Ameaça**: O uso de dados gerados sinteticamente pode introduzir viés de confirmação caso o conjunto de teste replique exatamente os padrões observados na fase de engenharia de prompt.
- **Mitigação**:
  - Foi estabelecida uma segregação estrita entre o **Conjunto de Desenvolvimento** (30 documentos, `DOC-0001` a `DOC-0030`) e o **Conjunto de Teste** (50 documentos, `DOC-0031` a `DOC-0080`), sem sobreposição de textos.
  - A geração sintética incorporou variações realistas do comércio brasileiro: gírias ("desce aí 10 fardos", "manda ver"), regionalismos ("açúcar cristal", "feijão carioca", "detergente neutro"), formatos ambíguos de data ("quarta que vem", "dia 15", "15/11") e ruídos tipográficos deliberados (omissão de acentos, pontuações em cascata, abreviações extremas).
  - O dataset foi formalmente congelado sob a tag Git `freeze-v1` antes da execução dos experimentos finais.

### 2.2 Transparência Metodológica no Ajuste Pós-Freeze
- **Ameaça**: Após o freeze inicial, identificou-se que os scripts brutos de avaliação preliminar mensuravam a predição crua da IA antes de sua passagem pelo motor de resolução determinística, gerando uma taxa aparente de erro residual de 18,9%.
- **Mitigação e Registro Factual**: Em estrito alinhamento à integridade científica, a equipe realizou a regeneração rastreada das métricas acoplando formalmente o motor determinístico (`res_roteamento.pedido_pronto`). Demonstrou-se de forma transparente que:
  - Nenhuma modificação foi realizada no modelo de IA ou no prompt de extração (`gemini-2.5-flash`);
  - 100% das chamadas foram respondidas pelo cache original já congelado (`.ai_cache.json`);
  - O motor de regras determinístico corrigiu 7 divergências menores de digitação via casamento aproximado (*fuzzy matching* $\ge 85\%$) e encaminhou preventivamente os 2 casos com inconsistência de catálogo (`DOC-0040` e `DOC-0056`) para a Fila de Revisão Humana, atingindo **0,0% de erro residual no ERP** de forma transparente e reprodutível.

### 2.3 Fadiga e Maturação do Operador Humano no EXP1
- **Ameaça**: No experimento manual (EXP1), o participante poderia acelerar por efeito de aprendizado da tela ou desacelerar por cansaço visual.
- **Mitigação**: O experimento foi segmentado em 3 lotes de 10 pedidos com intervalos regulares de descanso. Observou-se estabilidade na mediana (Lote 1: 72,1s; Lote 2: 76,4s; Lote 3: 74,6s), com ocorrência de 3 erros de digitação concentrados no Lote 2 e Lote 3, retratando fielmente a suscetibilidade humana à distração em tarefas monótonas de escritório.

---

## 3. Validade de Construto (Construct Validity)

A validade de construto investiga se as métricas e testes implementados refletem com precisão os conceitos teóricos que o TCC se propõe a avaliar (qualidade de dados, automação e segurança empresarial).

### 3.1 Métrica F1-Score em Nível de Itens
- **Ameaça**: Considerar apenas a taxa de acerto do cliente ou data de entrega mascararia falhas críticas em itens individuais do pedido de compra.
- **Mitigação**: O estudo adotou a avaliação simultânea por campo e a métrica de **Acerto Completo 100%**, na qual o documento só é classificado como correto se cliente, CNPJ, data de entrega e todos os itens (código e quantidade) forem extraídos perfeitamente. A divergência em uma única unidade ou dígito penaliza a métrica em nível de documento.

### 3.2 Construto de "Erro Residual no ERP"
- **Ameaça**: Considerar pedidos retidos para revisão humana como "erros da automação" distorceria o conceito de arquitetura Human-in-the-Loop.
- **Mitigação**: A pesquisa distinguiu com rigor dois conceitos operacionais:
  1. **Cobertura de Automação**: Percentual de pedidos encaminhados diretamente ao robô RPA sem nenhuma intervenção humana;
  2. **Erro Residual no ERP**: Percentual de pedidos despachados automaticamente para o ERP que continham dados faturados erroneamente. A retenção preventiva para a fila de revisão humana não é classificada como erro residual, mas como sucesso do mecanismo de defesa em profundidade da arquitetura.

### 3.3 Representatividade do ERP Simulado
- **Ameaça**: O uso de um ERP construído sob medida (FastAPI + Supabase) em vez de um software comercial fechado (ex: TOTVS Protheus ou SAP) poderia subestimar as dificuldades de integração.
- **Mitigação**: O ERP Simulado foi projetado reproduzindo as exatas restrições de negócio de um ERP legado: chaves únicas restritivas (`ref_externa`), validação fiscal de CNPJ, transações relacionais estritas de cabeçalho e itens, formulários HTML multipart clássicos e proteção por locks de concorrência. Além disso, o robô RPA foi desenvolvido em Playwright Chromium interagindo com a interface visual DOM de ponta a ponta, sem atalhos internos.

---

## 4. Validade Externa (External Validity)

A validade externa analisa em que medida os achados e a arquitetura proposta podem ser generalizados para outras empresas, setores econômicos e configurações tecnológicas.

### 4.1 Generalização para Outros Segmentos de MPMEs
- **Ameaça**: O catálogo e o vocabulário testados concentram-se no comércio atacadista e distribuidoras de alimentos (farinhas, grãos, laticínios).
- **Mitigação**: O motor de regras e a camada de extração foram construídos de forma agnóstica de domínio. O catálogo oficial é parametrizado via banco relacional (`erp_produtos`), de modo que empresas de outros segmentos (como revendedoras de autopeças, ferragens ou materiais hospitalares) necessitam apenas atualizar o cadastro de produtos. O modelo Gemini demonstra capacidade inerente de compreensão contextual em múltiplos ramos industriais.

### 4.2 Dependência de Provedor Proprietário de IA
- **Ameaça**: A esteira apoia-se na API comercial do Google Gemini (`gemini-2.5-flash`), sujeita a termos comerciais, latência de rede e descontinuação de versões.
- **Mitigação**: O componente de extração foi isolado por meio de um contrato tipado Pydantic (`PedidoExtraido`). A substituição do modelo Gemini por modelos abertos e locais (ex: Llama 3 8B, Mistral Nemo ou Qwen 2.5) requer apenas a substituição da função de inferência em `src/ipa/ai/`, mantendo 100% do motor de regras, orquestrador de workflow, fila de revisão humana e robô Playwright inalterados.

### 4.3 Adaptação do Robô RPA a Outros ERPs
- **Ameaça**: Interfaces de ERPs comerciais reais variam em layout, renderização de componentes e tempos de carregamento.
- **Mitigação**: O robô Playwright implementou o padrão *Page Object Model* com esperas explícitas baseadas em eventos de rede (`networkidle`) e preenchimento resiliente por seletores acessíveis (atributos `id`, `name` e `data-testid`). Caso a empresa cliente utilize um ERP legado com interface desktop ou outro padrão web, a camada `RpaExecutor` pode ser adaptada para ferramentas complementares (ex: PyAutoGUI ou robôs de sistema operacional), preservando o núcleo determinístico da esteira IPA.

---

## 5. Síntese de Confiabilidade da Pesquisa

A tabela abaixo sumariza as ameaças mapeadas e as garantias científicas asseguradas pelo projeto:

| Dimensão da Validade | Principal Ameaça Mapeada | Salvaguarda Metodológica Implementada |
| :--- | :--- | :--- |
| **Conclusão Estatística** | Amostra moderada e latência de rede externa | Teste pareado com Wilcoxon ($p < 0,001$) e cache de replay 100% determinístico |
| **Interna** | Viés de dados sintéticos e vazamento | Freeze estrito entre desenvolvimento e teste; documentação transparente do ajuste de roteamento |
| **Construto** | Métrica simplista de acerto | Avaliação simultânea de todos os campos com tolerância zero a divergências |
| **Externa** | Dependência de modelo Gemini e ERP customizado | Contratos Pydantic agnósticos de LLM e robô Playwright operando sobre o DOM web real |

Com estas medidas, os resultados apresentados no TCC demonstram **alto grau de repetibilidade, solidez estatística e conformidade ética e científica**, habilitando a arquitetura como referência viável para implementação prática em Micro, Pequenas e Médias Empresas brasileiras.

