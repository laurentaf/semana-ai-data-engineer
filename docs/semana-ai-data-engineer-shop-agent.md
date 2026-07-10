**SEMANA AI DATA ENGINEER**  
De Zero a Agente Autônomo

13 a 17 de Abril de 2026  |  20h – 23h

**Projeto: ShopAgent**

Multi-Agent de IA para E-Commerce com CrewAI \+ Supabase \+ Qdrant

**100% Docker Local (Fases 1-3)  |  Serviços Gerenciados (Fase 4\)**

AIDE Brasil  |  Formação AI Data Engineer 2026  
Luan Moreno

# **1\. Visão Geral**

A Semana AI Data Engineer é um evento gratuito de 5 fases (13–17 Abril 2026, 20h–23h) que funciona como porta de entrada para a Formação AI Data Engineer. Em 4 fases práticas, os participantes constroem do zero o ShopAgent: um sistema multi-agent de IA conectado a dados reais de e-commerce, com interface conversacional.

## **Pergunta Central**

*O que eu consigo fazer agora que não conseguia antes?*

## **O Projeto: ShopAgent**

Um sistema multi-agent que analisa dados de e-commerce em tempo real, consulta tanto dados estruturados (SQL) quanto semânticos (vetores), e interage via chat. Construído incrementalmente ao longo de 4 fases.

## **Filosofia: Docker-First**

Fases 1 a 3 rodam 100% em Docker local. Na Fase 4, migramos para serviços gerenciados (Supabase \+ Qdrant Cloud), mostrando que a arquitetura é a mesma – só muda o endpoint. Isso ensina portabilidade real.

\# docker-compose.yml da Semanaservices:  shadowtraffic:   \# Gera dados e-commerce  postgres:        \# The Ledger (dados estruturados)  qdrant:          \# The Memory (dados semânticos)  fastapi-mock:    \# API de estoque (fonte externa)

# **2\. Stack Técnica Completa**

Cada ferramenta tem um papel claro e aparece no dia certo, criando uma progressão natural de complexidade.

| Camada | Ferramenta | Função | Fase |
| ----- | ----- | ----- | ----- |
| Data Generation | ShadowTraffic | Gerar dados e-commerce (JSONL, Postgres) | 1 – 4 |
| Fontes Externas | CSV \+ FastAPI Mock | Catálogo de produtos \+ API de estoque | 1 |
| AI Coding | Claude Code \+ Cursor | Escrever código com IA, explorar dados | 1 – 4 |
| Tipagem/Schema | Pydantic | Validação e structured outputs | 1 – 2 |
| LLM | Claude (Anthropic) | Motor de IA principal | 1 – 4 |
| RAG Framework | LlamaIndex | Indexação, embeddings, query engine | 2 – 3 |
| Vector DB | Qdrant | The Memory – busca semântica | 2 – 4 |
| Structured DB | Supabase (Postgres) | The Ledger – queries determinísticas | 3 – 4 |
| AI x Tools | MCP Protocol | MCPs oficiais do Supabase \+ Qdrant | 3 – 4 |
| Multi-Agent | CrewAI | Orquestração de agentes especializados | 4 |
| Interface | Chainlit | Chat conversacional com streaming | 4 |
| Observabilidade | LangFuse | LLMOps / AgentOps – traces do agente | 4 |
| Evals | DeepEval | Testar qualidade das respostas do agente | 3 – 4 |
| Spec-Driven | PRD.md, CLAUDE.md | Contexto persistente para AI Coding | 1 |
| Infra | Docker Compose | Tudo local nas Fases 1-3 | 1 – 3 |
| Cloud (Fase 4\) | Supabase \+ Qdrant Cloud | Migração para serviços gerenciados | 4 |

# **3\. Arco Narrativo da Semana**

| Fase | Tema | Emoção | Entrega | Stack Nova |
| ----- | ----- | ----- | ----- | ----- |
| 1 Seg | INGERIR | Curiosidade | Pipeline de ingestão rodando | ShadowTraffic, Pydantic, Claude Code |
| 2 Ter | CONTEXTUALIZAR | Confiança | IA respondendo sobre seus dados | LlamaIndex, Qdrant |
| 3 Qua | AGENTE | Empolgação | Agente autônomo \+ AgentSpec modo Deus | LangChain, Chainlit, AgentSpec |
| 4 Qui | MULTI-AGENT | Orgulho | Time de agentes \+ Frontend \+ Cloud | CrewAI, DeepEval, LangFuse |
| 5 Sex | REFLETIR | Inspiração | Visão de futuro | Podcast |

# **4\. Modelo de Dados E-Commerce**

## **Geração: ShadowTraffic**

Serviço containerizado (Docker) que gera dados declarativamente via JSON. Zero dependência externa, volume controlável, dados realistas com Faker integrado e lookups relacionais.

**4 Entidades \+ 2 Fontes Externas**

| Entidade | Campos Principais | Fonte | Destino | Fase |
| ----- | ----- | ----- | ----- | ----- |
| customers | customer\_id, name, email, city, state, segment | ShadowTraffic | Postgres \+ JSONL | 1 |
| products | product\_id, name, category, price, brand, stock | CSV estático | Postgres | 1 |
| stock\_api | product\_id, available\_qty, warehouse, updated\_at | FastAPI Mock | API REST | 1 |
| orders | order\_id, customer\_id, product\_id, qty, total, status, payment, date | ShadowTraffic | JSONL (streaming) | 1–4 |
| reviews | review\_id, order\_id, rating, comment, sentiment | ShadowTraffic \+ ai() | JSONL → Qdrant | 2–4 |

O ShadowTraffic usa lookup entre geradores para manter relacionamentos (ex: orders referência customer\_id real). Reviews usam a função ai() para gerar comentários realistas via LLM.

**3 Fontes, 3 Tipos – Por quê?**

* JSONL via ShadowTraffic: simula streaming de eventos (orders chegando em tempo real)

* CSV estático: simula catálogo de produtos (muda pouco, carga batch)

* REST API mock: simula integração com sistema externo (estoque do warehouse)

Isso mostra pro aluno que pipelines reais nunca têm uma fonte só.

# **5\. Conceito Core: The Ledger \+ The Memory**

*Um agente inteligente precisa de duas pernas: uma para fatos exatos (SQL) e outra para significado (vetores).*

## **Por que duas camadas de dados?**

Quando alguém pergunta “Qual o faturamento de março?”, a resposta é um número exato: SELECT SUM(total) FROM orders WHERE month \= 3\. Vector search não serve aqui – ele retornaria documentos “parecidos com faturamento”, não o número. Isso é uma query DETERMINÍSTICA.

Quando alguém pergunta “Quais clientes estão reclamando de entrega?”, SQL não resolve – porque “entrega atrasada” pode aparecer como “demorou demais”, “ainda não chegou”, “faz 10 dias”. Aqui o vector search brilha, porque entende SEMÂNTICA.

| Camada | Store | Tipo de Query | Exemplo | Comportamento |
| ----- | ----- | ----- | ----- | ----- |
| The Ledger | Supabase (Postgres) | SQL – determinística, exata | Total vendas por região | Sempre o mesmo resultado |
| The Memory | Qdrant (Vector) | Similaridade – semântica, aproximada | Clientes insatisfeitos | Entende significado |

O agente decide qual perna usar baseado na pergunta. O MCP Protocol habilita isso: cada store vira uma “ferramenta” que o agente pode chamar. MCPs oficiais do Supabase e Qdrant são usados (não construímos do zero).

**🔵 DIA 1**

**INGERIR: Dados Reais \+ Fundamentos**

*De “o que é isso?” para “tenho 3 fontes de dados fluindo no meu pipeline”*

**Objetivo da Noite**

O aluno sai com um pipeline de ingestão funcionando: ShadowTraffic gerando orders, CSV de produtos carregado, API mock respondendo. Entende o que muda com IA no Data Engineering e tem o ambiente Docker rodando.

**Bloco 1: Abertura (20h – 20h30) – O Novo Data Engineer**

* O que é AI Data Engineering? Como IA muda o dia a dia do DE

* Os 4 AI Coding Agents: Cursor (IDE), Claude Code (Terminal), Codex (Cloud), OpenClaw (Chat)

* Demo ao vivo: pedir ao Claude Code para explicar um schema de dados

* Apresentação do ShopAgent – o que vamos construir na semana

**Bloco 2: Ambiente Docker \+ ShadowTraffic (20h30 – 21h30)**

* docker-compose up: subindo ShadowTraffic \+ Postgres \+ Qdrant

* Config JSON do ShadowTraffic:

  * Generator 1: customers (uuid, name, email, city, segment) → JSONL

  * Generator 2: orders com lookup para customers → JSONL streaming

  * Connection: filesystem com formato JSONL

* Fonte 2: carregar products.csv no Postgres (catálogo estático)

* Fonte 3: FastAPI mock retornando estoque por produto (5 min setup)

* Claude Code explorando e validando os dados gerados

**Bloco 3: Pydantic \+ Structured Outputs (21h30 – 22h30)**

* Por que tipar dados? De JSON bruto a modelos validados

* Exemplo prático com Pydantic:

class Order(BaseModel):    order\_id: str    customer\_id: str    product: str    quantity: int \= Field(ge=1, le=100)    total: float \= Field(ge=0)    payment: Literal\['credit\_card', 'pix', 'boleto'\]order \= Order(\*\*raw\_json)  \# Validado\!

* Structured Outputs com Claude: pedir análise dos dados e receber JSON tipado

* Spec-Driven Development: criar PRD.md do ShopAgent com Claude Code

* Contexto persistente: CLAUDE.md e AGENTS.md

**Bloco 4: Encerramento (22h30 – 23h)**

* Recapitulação: “Vocês têm 3 fontes de dados reais e IA entendendo o schema”

* Desafio: gerar 10.000 orders e identificar padrões com Claude

*Entrega: Docker rodando \+ ShadowTraffic \+ CSV \+ API Mock \+ Pydantic \+ PRD.md*

**🟢 DIA 2**

**CONTEXTUALIZAR: Context Engineering \+ RAG**

*De “a IA responde qualquer coisa” para “a IA responde CERTO sobre MEUS dados”*

**Objetivo da Noite**

O aluno sai sabendo construir contexto rico para IA e implementando RAG com LlamaIndex \+ Qdrant. A IA deixa de inventar e passa a responder com base nos dados reais de e-commerce.

**Bloco 1: Abertura (20h – 20h30) – Além do Prompt**

* A evolução: Prompt Engineering → Context Engineering (Karpathy, 2026\)

* Context \= instruções \+ dados \+ schema \+ exemplos \+ restrições

* Framework: System Prompt \+ Few-Shot \+ Schema \+ Fresh Data

**Bloco 2: Construindo Contexto Rico (20h30 – 21h15)**

* System Prompts efetivos: persona do ShopAgent

* Few-Shot com dados reais de e-commerce (orders da Fase 1\)

* Schema como contexto: passar Pydantic models para IA entender estrutura

* Restrições e guardrails: limitar respostas ao domínio

* Exercício: contexto que faz Claude responder “Qual ticket médio por região?”

**Bloco 3: RAG com LlamaIndex \+ Qdrant (21h15 – 22h30)**

* O que é RAG e por que o Data Engineer precisa entender

* LlamaIndex: SimpleDirectoryReader carrega JSONLs da Fase 1

* Embeddings → Qdrant (rodando local no Docker)

* Fluxo completo:

  * JSONLs de orders/reviews → LlamaIndex Reader → Chunks

  * Chunks → Embeddings → Qdrant (Docker local)

  * Query: “clientes reclamando de entrega” → Vector Search → Claude responde

* Structured Outputs avançado: respostas em JSON para alimentar dashboards

* Demo: ShopAgent respondendo perguntas com dados reais via RAG

**Bloco 4: Encerramento (22h30 – 23h)**

* Recapitulação: “Sua IA agora busca nos seus dados antes de responder”

* Desafio: criar 5 perguntas de negócio e testar precisão das respostas

*Entrega: LlamaIndex \+ Qdrant indexando dados \+ RAG respondendo com contexto real*

**🟠 DIA 3**

**CONECTAR: MCP \+ The Ledger \+ The Memory**

*De “IA que lê arquivos” para “IA com duas pernas: SQL exato \+ busca semântica”*

**Objetivo da Noite**

O aluno sai com o ShopAgent conectado via MCP a duas fontes complementares: Supabase (The Ledger) para queries SQL determinísticas e Qdrant (The Memory) para busca semântica. O agente decide qual usar.

**Bloco 1: Abertura (20h – 20h30) – MCP e As Duas Pernas**

* MCP: Model Context Protocol – o “USB-C” da IA para ferramentas

* Conceito The Ledger vs The Memory (explicado na seção 5\)

* Por que o agente precisa de AMBOS: números exatos \+ compreensão semântica

**Bloco 2: The Ledger – Supabase via MCP (20h30 – 21h30)**

* Migrando dados da Fase 1 para Postgres estruturado:

  * customers \+ products \+ orders em tabelas com schemas definidos

  * ShadowTraffic agora gerando direto no Postgres (novo destino)

* Conectar MCP oficial do Supabase

* Demo: Claude Code consultando “faturamento total por região” via MCP → SQL exato

* Tool Use: definir ferramentas (query\_sales, get\_customer, top\_products)

* Exercício: perguntas que só SQL resolve (agregações, JOINs, filtros)

**Bloco 3: The Memory – Qdrant via MCP (21h30 – 22h15)**

* Reviews da Fase 2 já no Qdrant – agora conectando via MCP oficial do Qdrant

* Demo: “Quais clientes reclamam de frete?” → busca semântica → resposta contextual

* Multi-tool: agente combina Supabase \+ Qdrant numa resposta só

  * Pergunta: “Clientes do Sul que reclamam de entrega: qual o ticket médio?”

  * Agente: Qdrant (acha os clientes) → Supabase (calcula ticket) → Resposta

* Intro a Evals com DeepEval: o agente está chamando a ferramenta certa?

**Bloco 4: Encerramento (22h15 – 23h)**

* Recapitulação: “Seu agente agora tem duas pernas: fatos exatos e compreensão”

* Desafio: criar uma pergunta que exija AMBAS as pernas

*Entrega: MCP Supabase \+ MCP Qdrant \+ Agent decidindo qual store consultar*

**🟣 DIA 4**

**ORQUESTRAR: Multi-Agent \+ Deploy \+ Pitch**

*De “um agente” para “um time de agentes com interface e cloud”*

**Objetivo da Noite**

O aluno sai com o ShopAgent completo: multi-agent com CrewAI, interface conversacional com Chainlit, rodando em serviços gerenciados. Na segunda metade, pitch natural para a Formação.

**Bloco 1: Abertura (20h – 20h20) – De Agente a Time**

* A diferença: agente único vs multi-agent (especialização)

* CrewAI: orquestração de agentes com roles, goals e tools

* Os 3 agentes do ShopAgent:

  * AnalystAgent: consulta Supabase (SQL determinístico)

  * ResearchAgent: busca semântica no Qdrant (reviews, contexto)

  * ReporterAgent: combina resultados e gera resposta final

**Bloco 2: Multi-Agent \+ Cloud \+ Interface (20h20 – 21h30)**

* Migração Docker → Serviços Gerenciados:

  * Postgres local → Supabase (trocar endpoint, mesma config)

  * Qdrant local → Qdrant Cloud free tier (mesmo client, novo URL)

  * Mensagem: “A arquitetura é a mesma, só o endpoint muda”

* Implementando CrewAI com os 3 agentes \+ tools da Fase 3

* Conectando Chainlit como interface conversacional:

  * Chat bonito com streaming de respostas

  * Steps visíveis: aluno vê qual agente está pensando

  * \~20 linhas de código para conectar CrewAI ao Chainlit

* Observabilidade: LangFuse para ver cada trace do agente

* Demo final: ShopAgent rodando end-to-end com chat bonito

**Bloco 3: Encerramento \+ Pitch (21h30 – 23h)**

**21h30 – 22h00:** Recapitulação da Jornada Completa

* Fase 1: Vocês geraram dados reais e tiparam com Pydantic

* Fase 2: Vocês fizeram IA responder com precisão (Context Engineering \+ RAG)

* Fase 3: Vocês deram duas pernas ao agente: SQL exato \+ semântica (MCP)

* Fase 4: Vocês construíram um time de agentes com interface profissional

*“Nesta semana vocês provaram que conseguem. A Formação é onde vocês dominam.”*

**22h00 – 22h30:** Pitch – Formação AI Data Engineer

* Transição: “Vocês viram o que é possível em 4 fases. Imaginem 70 horas.”

* A Formação: 4 Camadas (MindSet, Foundation, Workshops, Bootcamps)

* 16 módulos \+ 6 workshops \+ 4 bootcamps hands-on

* Os 4 AI Coding Agents em profundidade

* Membros Fundadores: R$ 2.997 (vs R$ 3.997) – vagas limitadas

**22h30 – 23h00:** Q\&A \+ Fechamento

* Perguntas sobre a Formação e carreira

* Link de inscrição \+ bônus para quem se inscrever na live

*Entrega: ShopAgent multi-agent \+ Chainlit \+ cloud \+ decisão sobre a Formação*

**🔴 DIA 5**

**REFLETIR: Podcast – O Futuro do AI Data Engineer**

*Conversa aberta sobre carreira, mercado e o que vem pela frente*

**Formato**

Podcast ao vivo (1–2h) com convidados. Tom descontraído e inspirador.

**Temas**

* O que muda na carreira de Data Engineer com IA?

* Context Engineering vs Prompt Engineering – a evolução real

* MCP como padrão: The Ledger \+ The Memory – para onde vai?

* Multi-Agent Systems: hype ou realidade?

* AI Coding Agents: próximos 12 meses

* Retrospectiva: o que os participantes construíram na Semana

* Último lembrete sobre a Formação (natural, sem pressão)

*Entrega: Inspiração \+ clareza sobre o caminho \+ comunidade*

# **6\. Conexão Semana ↔ Formação**

| Fase | Semana (Intro – 20%) | Formação (Domínio – 100%) |
| ----- | ----- | ----- |
| 1 | ShadowTraffic \+ Pydantic \+ Claude Code | Foundation: 16 módulos \+ 4 AI Coding Agents completos |
| 2 | Context Engineering \+ RAG básico \+ Qdrant | Workshops: Context Eng avançado \+ RAG production-ready |
| 3 | MCP \+ Supabase \+ Qdrant \+ Tool Use | Workshops: MCP avançado \+ Evals \+ Multi-tool patterns |
| 4 | CrewAI básico \+ Chainlit \+ LangFuse intro | Bootcamps: Multi-Agent completo \+ LLMOps \+ Deploy prod |

## **Estratégia do Pitch**

* A semana inteira é prova de conceito. Cada noite mostra 20% do que a Formação cobre.

* Fase 4: o aluno já sabe o que quer. O pitch só confirma o caminho.

* Frase-chave: “Em 4 fases vocês construíram o ShopAgent. Em 70 horas vocês dominam.”

**Oferta**

* Membros Fundadores: R$ 2.997 (desconto de R$ 1.000 sobre R$ 3.997)

* Bônus exclusivo para inscritos durante a Semana

* Acesso imediato ao MindSet \+ primeiros módulos

* Comunidade de 1.000+ pré-inscritos

# **7\. Métricas de Sucesso**

| Métrica | Meta | Como Medir |
| ----- | ----- | ----- |
| Audiência Fase 1 | 1.000+ ao vivo | Plataforma de live |
| Retenção Fase 1→4 | \> 40% | Audiência Fase 4 / Fase 1 |
| Engajamento Chat | \> 300 msgs/noite | Chat da live |
| ShopAgent Completo | \> 30% constroem | Formulário pós-evento |
| Conversão Formação | \> 5% audiência | Vendas durante/após |

# **8\. Timeline de Preparação**

| Quando | Ação |
| ----- | ----- |
| 4 sem antes | docker-compose.yml pronto \+ configs ShadowTraffic \+ CSV \+ API mock \+ repo ShopAgent |
| 3 sem antes | Dry run Fase 1–2 \+ LlamaIndex pipeline testado \+ Qdrant indexado |
| 2 sem antes | Dry run Fase 3–4 \+ CrewAI \+ Chainlit \+ pitch pronto \+ página vendas |
| 1 sem antes | Divulgação pesada \+ teste end-to-end \+ convidar podcast \+ Supabase/Qdrant Cloud setup |
| Semana evento | Executar\! \+ métricas \+ ajustar pitch baseado no engajamento |

