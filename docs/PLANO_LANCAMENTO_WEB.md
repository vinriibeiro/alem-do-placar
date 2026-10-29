# Plano de Lançamento Web — Além do Placar

**Autor do plano:** Claude (papel: arquiteto / líder de ciência de dados do projeto)
**Data:** 29/10/2026
**Branch de referência:** `develop` (commit `1bb01d8`)
**Público deste documento:** o próprio Vinícius e as sessões de Claude Code (Opus / Sonnet) que executarão cada fase. Cada fase traz um **prompt pronto para colar**.

---

## 1. Diagnóstico — onde o projeto está hoje

### 1.1 O que já existe e funciona

| Camada | Estado | Evidência |
|---|---|---|
| Dados (T002–T003) | 3.040 partidas reais 2018–2025, OpenFootball CC0, Parquet em `data/processed` | `docs/sources_audit.md`, `data/processed/*.parquet` |
| EDA (T004) | Notebook e funções prontos | `notebooks/01_exploratoria.ipynb` |
| Atributos (T005) | 12 atributos sem vazamento temporal | `src/features/temporais.py` |
| Modelagem (T006) | Ridge selecionado; MAE holdout 0,478 vs baseline 0,567; cobertura 91,2% | `data/predictions/modelagem/metadados.json` |
| Explicabilidade (T007) | Relatório científico, importância por permutação, resíduos | `data/predictions/cientifica/` |
| Power BI (T008) | Projeto `.pbip` com 7 páginas e 41 visuais | `dashboard/powerbi/AlemDoPlacar/` |
| Assistente (T009) | API FastAPI local, 6 intenções por palavra-chave, sem LLM | `src/api/` |
| Testes | 17 arquivos de teste unitário, CI definida (nunca disparada) | `tests/unit/`, `.github/workflows/ci.yml` |

### 1.2 O que falta para "clicar no link e ir direto"

**Bloqueadores de lançamento (ordem de gravidade):**

1. **Nada está publicado.** A API só aceita `127.0.0.1`/`localhost` (`TrustedHostMiddleware` e verificação de `Origin` em `src/api/app.py`). Não há Dockerfile, configuração por ambiente, nem hospedagem.
2. **Os dados não vão junto com o código.** `.gitignore` exclui `data/processed/*`, `data/predictions/*` e `*.parquet`. Um deploy a partir do Git sobe uma API sem dados.
3. **O Power BI aponta para caminhos absolutos do seu PC** (`C:\Users\Vinícius Ribeiro\...` dentro de `model.bim`). Publicar no Serviço funciona uma vez (modo Import carrega os dados), mas qualquer atualização agendada falha sem gateway.
4. **A página "Assistente" do Power BI são 3 caixas de texto apontando para `http://127.0.0.1:8765`.** Para quem abrir o link público, isso é um beco sem saída.
5. **O assistente não é a "central que responde tudo".** Ele responde 6 intenções fixas (erro, previsão, importância, evolução, consistência, explicação). Perguntas de negócio básicas — classificação de uma temporada, confronto direto, mando de campo, gols, sequência de resultados, comparação entre clubes — devolvem "não é possível calcular". O PRD (seção 4.1) prevê "API de modelo de linguagem" e o `.env.example` já reserva `LLM_API_KEY`, mas a integração nunca foi feita.
6. **Design** (confirmado na leitura do código):
   - **Web app:** um único `index.html` de 211 linhas, formulário cru, três cartões, sem identidade visual, sem navegação, sem estados de carregamento decentes, sem modo chat.
   - **Power BI:** tema base Fluent2 sem customização; 13 dos 41 visuais são caixas de texto; apenas card, barra, linha, tabela e segmentação; sem navegação entre páginas, sem grade de layout consistente, sem tooltips, sem hierarquia tipográfica.
7. **Higiene do repositório:**
   - `docs/TASKS.md` ainda diz "Tarefa atual: T001 — PENDENTE" (nunca foi atualizado); README diz "Status atual: T004"; `docs/model_card.md` diz que a T007 está pendente, mas os resultados já existem em `data/predictions/cientifica/`.
   - A pasta `docs/qa/TXXX/` exigida pelo TASKS.md não existe.
   - O remoto `origin` é `vinriibeiro/Template-Projetos-IA.git` — nome de template, não do produto. `main` está 135 arquivos atrás de `develop`.
   - Nesta máquina **não há `.venv`** e as dependências não estão instaladas (`fastapi`, `pytest` ausentes). Os testes não puderam ser executados aqui. O atalho "Além do Placar — Assistente" do Desktop aponta para um `.cmd` numa pasta de saída do Codex, fora do repositório.

---

## 2. Arquitetura alvo (o que o visitante vai ver)

```
https://alemdoplacar.<host>            <- UM link público
|
|-- /            Página inicial: proposta, 4 KPIs, chamadas para Dashboard e Assistente
|-- /dashboard   Power BI incorporado (Publish to web, iframe) + navegação por página
|-- /assistente  Chat em português: pergunta -> Claude escolhe consulta autorizada -> resposta
|                com números, tabela, fonte, período e limitações
|-- /metodologia Fontes, modelo, métricas, limitações, model card
`-- /api/...     FastAPI (contexto, pergunta, saúde) — mesma origem, sem CORS aberto
```

**Decisões já tomadas (não reabrir nas sessões de execução):**

| Tema | Decisão | Motivo |
|---|---|---|
| Hospedagem da API/web | **Render (Web Service, Docker)**, plano Starter (~US$ 7/mês) para não hibernar. Alternativa gratuita: Hugging Face Spaces (Docker), que hiberna após inatividade. | Deploy por Git, HTTPS automático, variáveis de ambiente seguras, domínio próprio opcional. O plano gratuito do Render hiberna e demora ~50 s para acordar: ruim para "clicar e ir direto". |
| Power BI público | **Publish to web** (embed público) a partir do Power BI Service com sua licença Pro. | Único modo que abre sem login. Dados são CC0 e agregados: sem risco. Requer que o administrador do tenant permita "Publicar na web"; se o tenant for corporativo e bloquear, usar um tenant próprio (conta pessoal / Microsoft 365 Developer). |
| Dados no deploy | Versionar os Parquet/JSON/CSV finais (≈3 MB) por lista de exceção no `.gitignore`. `modelo.joblib` continua fora do Git. | A API só lê Parquet/JSON/CSV. Dados CC0, pequenos e reproduzíveis pelo pipeline. |
| Fonte do Power BI | Trocar `File.Contents(caminho local)` por `Web.Contents(URL raw do GitHub)` nas partições do `model.bim`. | Permite atualizar no Serviço sem gateway e desacopla do seu PC. |
| LLM do assistente | **Claude API, SDK oficial `anthropic`, modelo `claude-opus-5-5`**, `output_config.effort = "low"` (rota de chat), ferramentas = catálogo fechado de consultas. Pode-se avaliar `claude-sonnet-5-5` depois, medindo qualidade; a troca é decisão sua. | Cumpre PRD 9.4: a IA **nunca** gera SQL; ela só escolhe uma consulta parametrizada e redige a resposta com os números devolvidos. |
| Fallback sem LLM | Manter o classificador determinístico atual como fallback quando a chave não existir ou a API falhar. | Testes continuam offline; a demo não quebra se a cota acabar. |
| Identidade visual | Tema claro (PRD 8.8), uma cor primária escura + uma cor de destaque, tipografia única (Inter), mesmos tokens no web app e no tema JSON do Power BI. | Consistência entre as duas superfícies, que hoje não existe. |

**Custo recorrente estimado:** Render Starter ~US$ 7/mês + Claude API (ordem de US$ 0,01–0,03 por pergunta com `effort=low` e cache de prompt; definir teto diário em variável de ambiente) + Power BI Pro (já possui).

---

## 3. Fases, ordem, modelo recomendado e tempo

| Fase | Entrega | Modelo | Sessões | Depende de |
|---|---|---|---|---|
| **F0** | Ambiente local, testes verdes, sincronizar docs, higiene do repo | **Sonnet** | 1 | — |
| **F1** | Assistente v2: catálogo amplo de consultas + camada Claude (tool use) + segurança para internet | **Opus** | 2 | F0 |
| **F2** | Redesign completo do web app (design system, 4 páginas, chat) | **Opus** | 2 | F1 (contrato da API) |
| **F3** | Redesign do Power BI (tema, layout, navegação, página Assistente, fonte Web) | **Opus** | 2 + validação sua no Desktop | F0 |
| **F4** | Deploy: Dockerfile, config por ambiente, Render, repositório público, CI, Publish to web | **Sonnet** | 1 + passos manuais seus | F1, F2, F3 |
| **F5** | QA final (T010), README de portfólio, material LinkedIn | **Sonnet** | 1 | F4 |

**Por que Opus nas F1–F3:** são as fases de arquitetura (contrato de ferramentas da IA, design system do zero, refatoração do gerador PBIR com dezenas de arquivos JSON interdependentes). Sonnet entrega bem as fases de execução mecânica e verificação (F0, F4, F5) e as correções pontuais apontadas por Codex/Gemini em qualquer fase.

**Calendário sugerido:** F0 hoje; F1 nos dois dias seguintes; F2 e F3 na semana seguinte (F3 pode andar em paralelo com F2, pois tocam arquivos diferentes); F4 e F5 na semana 3. **Lançamento alvo: ~3 semanas**, com revisão Codex e QA Gemini entre fases, como manda o `AGENTS.md`.

**Ramos Git:** `feature/t010-higiene` (F0), `feature/t009-assistente-v2` (F1), `feature/t009-webapp-redesign` (F2), `feature/t008-powerbi-redesign` (F3), `feature/t010-deploy` (F4), `feature/t010-publicacao` (F5). Merge em `develop` após revisão; `main` só com sua autorização.

---

## 4. Passos manuais que só você pode fazer

Faça-os **antes** da fase indicada; nenhuma sessão de IA deve fazê-los por você.

| Quando | O quê | Como |
|---|---|---|
| Antes da F1 | Criar chave da Claude API | console.anthropic.com → API Keys. Guardar em `.env` local como `LLM_API_KEY`. Nunca commitar. Definir limite de gasto mensal no console. |
| Antes da F4 | Criar repositório público `alem-do-placar` no GitHub | Vazio, sem README. A sessão F4 troca o `origin` e você autoriza o push. |
| Antes da F4 | Conta no Render | render.com, login com GitHub. Não criar o serviço ainda; a sessão F4 gera `render.yaml` e você aprova. |
| Durante a F3 | Validar o `.pbip` no Power BI Desktop | Abrir, conferir carga das 8 tabelas e 7 relacionamentos, comparar cards com Python, tirar prints para `docs/qa/T008/`. |
| Durante a F4 | Publicar o relatório e gerar link público | Power BI Desktop → Publicar → workspace → no Serviço: Arquivo → Inserir relatório → **Publicar na web (público)** → copiar URL do iframe. Se a opção estiver cinza: Portal de administração → Configurações de locatário → "Publicar na web" → habilitar. |
| Durante a F4 | Autorizar push, deploy e domínio | A sessão prepara tudo; você aprova `git push`, cria o serviço no Render a partir do `render.yaml` e cola as variáveis de ambiente (`LLM_API_KEY`, `POWERBI_EMBED_URL`, `ALLOWED_HOSTS`). |

---

## 5. Prompts prontos por fase

Instruções para colar: abra uma nova sessão de Claude Code **na pasta do projeto**, escolha o modelo indicado (`/model`), e cole o bloco inteiro. Cada prompt já manda ler este plano e os documentos do projeto; não é preciso explicar o contexto de novo.

### F0 — Higiene e base (Sonnet)

```text
Projeto: Além do Placar (pasta atual). Leia docs/PLANO_LANCAMENTO_WEB.md (seções 1, 2 e a fase F0), AGENTS.md e docs/TASKS.md antes de qualquer alteração. Você está executando a FASE F0 do plano. Não avance para outras fases.

Objetivo: deixar o repositório honesto, reproduzível e pronto para as fases seguintes.

Tarefas, nesta ordem:
1. Verifique git status. Crie a branch feature/t010-higiene a partir de develop.
2. Ambiente: crie .venv na raiz, instale `python -m pip install -e ".[test,lint]"`, rode `python -B -m pytest` e `python -m ruff check .` / `ruff format --check .`. Corrija apenas falhas de lint/formatação triviais. Se algum teste falhar, relate com a saída; não "conserte" alterando a asserção.
3. Crie scripts/run_local.ps1 (ativa .venv e sobe `python -m api.server --raiz . --port 8765`) e scripts/run_tests.ps1. Documente no README. Isso substitui o atalho do Desktop que aponta para uma pasta fora do repositório.
4. Sincronize a documentação com a realidade:
   - docs/TASKS.md: tabela de backlog com T001–T009 em "AGUARDANDO APROVAÇÃO" (código entregue, revisão/QA formais não registrados) e T010 "EM DESENVOLVIMENTO"; histórico de entregas preenchido com os commits reais de `git log`; seção 12 apontando para T010 e para o plano de lançamento.
   - README.md: status atual real, seção "Como executar" com os scripts, link para docs/PLANO_LANCAMENTO_WEB.md.
   - docs/model_card.md: substituir "Pendente" da seção T007 pelos números reais de data/predictions/cientifica/relatorio_cientifico.md (copiar tabelas, citar o arquivo).
5. Crie docs/qa/T001 a docs/qa/T009 com um implementation.md cada (tarefa, commit, arquivos, testes executados, status "aguardando revisão Codex e QA Gemini"). Não invente relatórios de Codex/Gemini.
6. Dados no Git: altere o .gitignore para permitir, por lista de exceção, os arquivos que a API e o Power BI consomem: data/processed/*.parquet, data/predictions/modelagem/{previsoes.parquet,metricas.json,metadados.json,metricas_equipe.json}, data/predictions/cientifica/{importancias.csv,relatorio_cientifico.json,relatorio_cientifico.md}. Mantenha modelo.joblib, mlruns/ e data/raw fora. Confirme com `git status` que só esses arquivos entraram e que o total é inferior a 5 MB.
7. Rode a suíte de novo. Sugira commits pequenos (docs, chore, test) e NÃO faça push nem merge.

Ao terminar, entregue o relatório do AGENTS.md seção 9 (o que foi feito, arquivos, testes executados com saída, problemas, próxima etapa = F1).
```

### F1 — Assistente v2: central de respostas com Claude (Opus)

```text
Projeto: Além do Placar (pasta atual). Leia docs/PLANO_LANCAMENTO_WEB.md (seções 1, 2 e a fase F1), AGENTS.md, docs/PRD.md seções 9 e 10, src/api/assistant.py, src/api/app.py, src/processing/consultas.py e tests/unit/test_assistant.py. Você está executando a FASE F1. Antes de codar, apresente um plano de implementação curto e aguarde minha aprovação.

Objetivo: transformar o assistente em uma central que responde às perguntas de negócio sobre a operação, mantendo as regras do PRD 9.4 (a IA nunca gera SQL; nenhuma informação inventada; previsões nunca como certezas; fonte, período e limitações em toda resposta).

Arquitetura obrigatória:
1. Catálogo de consultas (src/api/catalogo.py): funções Python puras, parametrizadas e testáveis, cada uma com SQL fixo em DuckDB (como src/processing/consultas.py já faz) ou pandas sobre os Parquet. Mínimo a cobrir, além das 6 intenções atuais:
   - classificação de uma temporada (posição, pontos, V/E/D, gols pró/contra/saldo, aproveitamento);
   - resumo de uma equipe em uma temporada e em todo o histórico;
   - comparação entre duas equipes (mesmas métricas lado a lado);
   - confronto direto entre duas equipes no período;
   - desempenho como mandante versus visitante (por equipe e geral);
   - estatísticas de gols (média por partida por temporada, maiores goleadas, distribuição de placares, % de vitórias do mandante);
   - sequências (maior série invicta, de vitórias e de derrotas por equipe e temporada);
   - rankings por métrica (quem mais pontuou, melhor ataque, melhor defesa, mais consistente) com filtros de temporada;
   - evolução/tendência por janela móvel (já existe; expor por parâmetro);
   - previsões, erro do modelo, importância de variáveis, metodologia (já existem; manter).
   Cada função devolve um dict padronizado: texto_base, dados (lista de linhas), fonte, periodo, limitacoes. Documente o catálogo em docs/assistente_catalogo.md.
2. Camada LLM (src/api/llm.py) usando o SDK oficial `anthropic` (adicionar ao pyproject). Modelo `claude-opus-5-5`, `output_config={"effort": "low"}`, `max_tokens` adequado, system prompt estável com cache_control (prompt caching), tool use com uma ferramenta por consulta do catálogo (schemas JSON com `strict: true`, `additionalProperties: false`), `tool_choice` auto. Loop manual ou tool runner do SDK; entradas de ferramentas sempre validadas antes de executar. O modelo recebe apenas os números devolvidos pelo catálogo e redige a resposta em português; proíba no system prompt qualquer número que não venha das ferramentas e exija que perguntas fora do escopo recebam a frase do PRD 9.5. Trate `stop_reason == "refusal"` e erros do SDK por classe (RateLimitError, APIStatusError, APIConnectionError) com mensagem amigável.
3. Fallback: sem LLM_API_KEY ou em falha da API, usar o classificador determinístico atual sobre o catálogo ampliado. Os testes não podem depender de rede: mockar o cliente Anthropic.
4. Contrato da API (documente em docs/api_contrato.md, a fase F2 depende dele):
   - POST /api/pergunta -> {texto, dados, fonte, periodo, limitacoes, modo: "llm"|"deterministico", consultas_usadas: [...], status}
   - GET /api/contexto -> acrescentar: lista de temas suportados com exemplos de perguntas, por categoria.
   - GET /api/sugestoes -> 8 perguntas de exemplo rotativas.
5. Preparação para internet (sem publicar nada agora): hosts permitidos e origens permitidas lidos de variáveis de ambiente (ALLOWED_HOSTS, ALLOWED_ORIGINS) com padrão local; limite de taxa por IP em memória (ex.: 20 perguntas/min) e teto diário global de chamadas ao LLM (LLM_DAILY_LIMIT) com resposta 429 clara; limite de tamanho do corpo; log sem conteúdo da pergunta. Chave nunca sai do servidor.
6. Testes: unitários para cada consulta do catálogo (com dados sintéticos como os testes atuais), para o roteamento LLM com cliente mockado, para o fallback, para rate limit e para origem/host. Rode a suíte completa, ruff check e format.

Restrições: não alterar pipeline, features, modelos ou Power BI. Preservar as respostas atuais do assistente (os testes existentes devem continuar passando). Não fazer push. Entregar relatório conforme AGENTS.md seção 9, com próxima etapa = revisão Codex e depois F2.
```

### F2 — Redesign do web app (Opus)

```text
Projeto: Além do Placar (pasta atual). Leia docs/PLANO_LANCAMENTO_WEB.md (seções 1.2 item 6, 2 e a fase F2), docs/api_contrato.md, docs/PRD.md seção 8.8 e src/api/static/index.html. Você está executando a FASE F2. Apresente primeiro: (a) o design system proposto (tokens de cor, tipografia, espaçamento, componentes) e (b) wireframe em texto das 4 páginas. Aguarde minha aprovação antes de implementar.

Contexto honesto: o front-end atual é um index.html de 211 linhas com visual amador. O objetivo é um produto de portfólio com aparência profissional, comparável a um produto SaaS de analytics, mantendo tema claro e paleta limitada (PRD 8.8).

Requisitos:
1. Design system em src/api/static/css/tokens.css: paleta com 1 cor primária escura, 1 cor de destaque, neutros e cores semânticas (sucesso/alerta/erro) com contraste AA; escala tipográfica (Inter via Google Fonts, com fallback de sistema); espaçamento em múltiplos de 4; raios, sombras e estados de foco. Exportar os mesmos tokens em dashboard/assets/tema_tokens.json para a fase F3 usar no tema do Power BI.
2. Páginas (SPA leve, sem framework pesado; HTML + CSS + JS modular, sem build step; se usar biblioteca, apenas via CDN com versão fixada):
   - Início: cabeçalho com navegação, proposta em uma frase, 4 KPIs vindos de /api/contexto (partidas, temporadas, MAE do modelo vs baseline, cobertura do intervalo), dois cartões de chamada (Explorar dashboard / Perguntar ao assistente), rodapé com fonte CC0, licença e links do repositório.
   - Dashboard: iframe do Power BI (URL vinda de /api/config -> POWERBI_EMBED_URL; quando vazia, mostrar estado "dashboard em publicação" com capturas de tela estáticas em dashboard/assets/), altura responsiva, botão "abrir em tela cheia".
   - Assistente: interface de chat (histórico da sessão em memória, balões, indicador de digitação, sugestões clicáveis de /api/sugestoes, filtros de equipe e temporada recolhíveis). Cada resposta mostra texto, tabela com cabeçalhos legíveis (traduzir nomes de colunas), selo do modo (IA / determinístico), fonte, período e limitações em um bloco recolhível. Erros 429/503 com mensagens humanas.
   - Metodologia: conteúdo de docs/model_card.md e docs/methodology.md renderizado em seções navegáveis (gerar HTML estático na inicialização do servidor ou converter no carregamento), com as tabelas de métricas e as figuras de data/predictions/cientifica/*.png servidas estaticamente.
3. Qualidade: responsivo de 360 px a 1440 px; navegação por teclado; aria nos componentes dinâmicos; skeletons de carregamento; nenhum número hardcoded (tudo vem da API); favicon e Open Graph (título, descrição, imagem em dashboard/assets/og.png gerada por você a partir de SVG).
4. Servidor: montar /static com cache adequado; rota GET /api/config com valores não sensíveis (URL de embed, versão, ano dos dados). Não expor segredos.
5. Testes: testes de API para /api/config e para o serviço dos arquivos estáticos; um teste que valida que index.html referencia apenas arquivos existentes. Rode a suíte, ruff check e format. Suba o servidor local e verifique as 4 páginas (use o skill /run ou o navegador disponível) e registre capturas em docs/qa/T009/.

Restrições: não alterar o catálogo ou a camada LLM (F1) além do estritamente necessário; não fazer push. Relatório conforme AGENTS.md seção 9; próxima etapa = QA Gemini e F3.
```

### F3 — Redesign do Power BI (Opus)

```text
Projeto: Além do Placar (pasta atual). Leia docs/PLANO_LANCAMENTO_WEB.md (seções 1.2 itens 3, 4 e 6, 2 e a fase F3), docs/dashboard_setup.md, docs/PRD.md seção 8, src/evaluation/powerbi.py, tests/unit/test_powerbi.py, dashboard/assets/tema_tokens.json (da F2) e a estrutura PBIR em dashboard/powerbi/AlemDoPlacar/. Você está executando a FASE F3. Apresente primeiro o plano de layout por página (grade, visuais, medidas DAX novas) e aguarde aprovação.

Contexto honesto: o relatório atual usa o tema Fluent2 padrão, 13 de 41 visuais são caixas de texto, não há navegação entre páginas e a página Assistente aponta para localhost. Precisa ficar com cara de produto.

Requisitos:
1. Tema: gerar dashboard/powerbi/AlemDoPlacar/AlemDoPlacar.Report/StaticResources/RegisteredResources/AlemDoPlacarTheme.json a partir dos tokens da F2 (cores de dados, fundo, texto, cards, títulos de visual, bordas, fonte Segoe UI como fallback de Inter) e registrar em report.json. Atualizar o gerador src/evaluation/powerbi.py para copiar e referenciar o tema; manter os testes passando e criar testes para o tema.
2. Layout: canvas 1280x720 em todas as páginas, grade de 12 colunas com margens de 24 px, cabeçalho padronizado (título, subtítulo com fonte/período, barra de navegação com botões para as 7 páginas usando ações de navegação de página; botão ativo destacado), rodapé com versão do modelo e data de corte.
3. Conteúdo por página, substituindo caixas de texto por visuais onde houver dado:
   - Visão Geral: 5 KPIs (partidas, temporadas, média de gols, % vitórias do mandante, MAE do modelo) + ranking de pontos por temporada (barra) + evolução de gols por temporada (linha) + tabela de classificação com formatação condicional.
   - Tendências: seleção de equipe e temporada; linha de média móvel de pontos (3/5/10) com linha de referência; matriz equipe x temporada com mapa de calor de aproveitamento.
   - Estatística: distribuição de placares (coluna), dispersão saldo de gols x pontos, mandante x visitante, volatilidade (desvio dos pontos) por equipe.
   - Laboratório de Modelos: barras comparando MAE/RMSE por modelo e fase; tabela de métricas por temporada; importância por permutação com barras de erro aproximadas (delta MAE +- desvio); cartões com modelo selecionado, corte e cobertura.
   - Previsões: seleção de equipe; linha previsto vs observado no holdout com faixa do intervalo de 90%; tabela por data; aviso claro de que são previsões retrospectivas.
   - Assistente: substituir os textos de localhost por um botão com ação Web URL lido de uma tabela de parâmetros (URL pública vinda de um campo do gerador; padrão "https://ALTERAR"), uma imagem de prévia do chat (dashboard/assets/preview_assistente.png gerada pela F2) e 6 perguntas de exemplo.
   - Metodologia: cards e texto curto com fonte, licença, período, atributos, validação e limitações (texto vindo de docs/model_card.md, encurtado).
4. Medidas DAX novas necessárias (aproveitamento, % vitórias mandante, saldo, posição por temporada com RANKX, médias móveis quando viável) documentadas em docs/dashboard_setup.md.
5. Fonte de dados: adicionar ao gerador a opção `modo_fonte="web"` que gera as partições com `Parquet.Document(Web.Contents("https://raw.githubusercontent.com/<usuario>/alem-do-placar/main/data/processed/...parquet"))` (URL base por parâmetro). O padrão continua local. Testar ambos os modos.
6. Regerar o projeto com o gerador (nunca editar o PBIR gerado à mão sem refletir no gerador), rodar a suíte, ruff. Escrever em docs/qa/T008/checklist_desktop.md o roteiro de validação que eu farei no Power BI Desktop (abrir, carregar, conferir cards vs Python, navegar, prints).

Restrições: não tocar em src/api nem no front-end; não publicar nada; não fazer push. Relatório conforme AGENTS.md seção 9; próxima etapa = minha validação no Desktop e, depois, F4.
```

### F4 — Deploy e publicação (Sonnet)

```text
Projeto: Além do Placar (pasta atual). Leia docs/PLANO_LANCAMENTO_WEB.md (seções 2, 4 e a fase F4), AGENTS.md seção 5 e src/api/server.py. Você está executando a FASE F4. Pré-condição: F1, F2 e F3 mescladas em develop e eu já criei o repositório GitHub público `alem-do-placar` e a conta no Render (confirme comigo antes de começar).

Objetivo: colocar a aplicação no ar em um link público, sem segredos no Git e sem que nenhuma ação irreversível seja executada sem minha autorização explícita.

Tarefas:
1. Dockerfile multi-stage (python:3.12-slim, usuário não root, instala apenas dependências de execução, copia src/, config/, data/processed, data/predictions e docs necessários; CMD uvicorn via um novo módulo api.main que lê PORT, HOST=0.0.0.0, ALLOWED_HOSTS, ALLOWED_ORIGINS, LLM_API_KEY, LLM_DAILY_LIMIT, POWERBI_EMBED_URL). .dockerignore cobrindo .venv, mlruns, notebooks, tests, .git.
2. render.yaml (Web Service, Docker, plano starter, health check em /health, variáveis de ambiente declaradas com sync: false para as sensíveis). Documentar alternativa Hugging Face Spaces em docs/deploy.md.
3. Testar o container localmente (docker build e docker run com as variáveis), bater em /health, /, /api/contexto e uma pergunta. Registrar saída em docs/qa/T010/deploy_local.md. Se o Docker não estiver instalado, me avise e teste pelo menos `python -m api.main` com as variáveis de ambiente.
4. Segurança para produção: confirmar que docs/openapi continuam desativados, cabeçalhos básicos (X-Content-Type-Options, Referrer-Policy, Content-Security-Policy permitindo o iframe do Power BI e os CDNs usados), HTTPS forçado atrás do proxy do Render, rate limit ativo, logs sem conteúdo de perguntas.
5. CI: ampliar .github/workflows/ci.yml para rodar em push para develop e main e em pull requests; adicionar job de build da imagem Docker. Não adicionar deploy automático: o Render fará deploy por integração Git quando eu autorizar.
6. Repositório: trocar o remoto origin para o novo repositório, preparar README de portfólio (badges de CI, capturas, link público, como rodar local) e LICENSE para o código (MIT) mantendo o aviso de dados CC0 e as notas da Microsoft em dashboard/powerbi. PARE e peça minha autorização antes de `git push`.
7. Integração final: após eu publicar o relatório no Power BI Service e gerar o link "Publicar na web", receber a URL e me orientar a colocá-la em POWERBI_EMBED_URL no Render; atualizar a URL pública do assistente no gerador do Power BI (F3) e me pedir para republicar o .pbix. Verificar o fluxo completo: link público -> início -> dashboard carrega -> assistente responde.

Relatório conforme AGENTS.md seção 9, incluindo a URL final e o checklist de verificação; próxima etapa = F5.
```

### F5 — QA final, documentação e divulgação (Sonnet)

```text
Projeto: Além do Placar (pasta atual). Leia docs/PLANO_LANCAMENTO_WEB.md (fase F5), docs/TASKS.md (T010) e AGENTS.md. Você está executando a FASE F5 (T010). A aplicação já está publicada.

Tarefas:
1. Rodar suíte completa, ruff, build Docker e um smoke test contra a URL pública (/health, /api/contexto, 10 perguntas de categorias diferentes do catálogo). Registrar em docs/qa/T010/test-results.md com saídas reais.
2. Revisão de integridade: recalcular em Python os 5 KPIs da página inicial e os cards do Power BI e comparar com o que está publicado; registrar divergências.
3. Documentação final: README (visão, demo, arquitetura com diagrama em Mermaid, resultados, limitações, como reproduzir), docs/methodology.md e docs/model_card.md revisados, docs/TASKS.md com T010 "AGUARDANDO APROVAÇÃO" e histórico completo.
4. Material de divulgação em docs/divulgacao/: post para LinkedIn (PT-BR, 150–220 palavras, sem jargão excessivo, com os números reais e o link), roteiro de vídeo de 60 s, e 3 capturas de tela recortadas em 1200x630.
5. Lista de melhorias futuras priorizadas (temporada 2026, xG, novas competições, avaliação formal do assistente com conjunto de perguntas e respostas esperadas) em docs/roadmap.md.

Não fazer push nem merge sem autorização. Relatório conforme AGENTS.md seção 9.
```

---

## 6. Critérios de "lançado"

- [ ] Um único link público abre a página inicial em menos de 3 s, sem login.
- [ ] O dashboard carrega dentro do site e navega pelas 7 páginas com o tema novo.
- [ ] O assistente responde corretamente a pelo menos 20 perguntas de 10 categorias diferentes, cita fonte e período, e recusa fora de escopo com a frase do PRD 9.5.
- [ ] Nenhum segredo no repositório; chave do LLM só no Render; teto diário ativo.
- [ ] CI verde em `main`; `docs/qa/` com evidências de T001–T010; TASKS.md e README refletem a realidade.
- [ ] Aprovação formal sua registrada em `docs/qa/T010/approval.md`.
