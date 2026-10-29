# TASKS — CONTROLE DE DESENVOLVIMENTO

## 1. Informações gerais

- **Projeto:** Além do Placar — Inteligência Esportiva e Ciência de Dados
- **Versão:** 1.0
- **PRD de referência:** `docs/PRD.md`
- **Status geral:** T001–T009 com código entregue (aguardando revisão Codex, QA Gemini e aprovação do usuário); T010 em desenvolvimento
- **Tarefa atual:** T010 — QA final e publicação (plano em `docs/PLANO_LANCAMENTO_WEB.md`, fase F0 concluída em código)
- **Responsável pelo projeto:** Vinícius Ribeiro
- **Desenvolvimento:** Claude Code
- **Revisão técnica:** Codex
- **Testes funcionais e QA:** Gemini/Antigravity
- **Aprovação final:** Usuário

---

## 2. Objetivo do controle

Este documento centraliza o acompanhamento das tarefas do projeto, garantindo que cada funcionalidade passe por desenvolvimento, revisão técnica, testes funcionais e validação antes de ser considerada concluída.

O processo deverá ser incremental, rastreável e orientado ao PRD.

**Fluxo oficial:**

PENDENTE → EM DESENVOLVIMENTO → EM REVISÃO → EM TESTE → CONCLUÍDA

Se forem identificados problemas:

EM REVISÃO / EM TESTE → CORREÇÃO → EM REVISÃO

A aprovação técnica não equivale à aprovação final do usuário.

---

## 3. Status das tarefas

| Status | Responsável | Significado |
|---|---|---|
| PENDENTE | Orquestrador | Aguardando dependências |
| EM DESENVOLVIMENTO | Claude Code | Implementação em andamento |
| EM REVISÃO | Codex | Revisão de código e arquitetura |
| EM TESTE | Gemini/Antigravity | QA técnico e funcional |
| CORREÇÃO | Claude Code | Correção de problemas identificados |
| AGUARDANDO APROVAÇÃO | Usuário | Revisão final da entrega |
| CONCLUÍDA | Usuário | Entrega formalmente aprovada |
| BLOQUEADA | Orquestrador | Dependência ou impedimento identificado |

---

## 4. Backlog principal

| ID | Funcionalidade | Responsável | Status |
|---|---|---|---|
| T001 | Fundação e configuração do projeto | Claude Code | AGUARDANDO APROVAÇÃO |
| T002 | Auditoria e seleção das fontes de dados | Claude Code | AGUARDANDO APROVAÇÃO |
| T003 | Pipeline de coleta e tratamento | Claude Code | AGUARDANDO APROVAÇÃO |
| T004 | Análise exploratória e estatística | Claude Code | AGUARDANDO APROVAÇÃO |
| T005 | Engenharia de atributos | Claude Code | AGUARDANDO APROVAÇÃO |
| T006 | Modelagem preditiva e backtesting | Claude Code | AGUARDANDO APROVAÇÃO |
| T007 | Explicabilidade e avaliação científica | Claude Code | AGUARDANDO APROVAÇÃO |
| T008 | Dashboard Power BI | Claude Code | AGUARDANDO APROVAÇÃO |
| T009 | Assistente de inteligência artificial | Claude Code | AGUARDANDO APROVAÇÃO |
| T010 | QA final, documentação e publicação | Claude Code | EM DESENVOLVIMENTO |

---

# 5. DETALHAMENTO DAS TAREFAS

## T001 — Fundação do projeto

**Prioridade:** CRÍTICA  
**Dependências:** Nenhuma  
**Status:** PENDENTE

### Objetivo

Estabelecer a estrutura técnica, as configurações e os mecanismos de qualidade necessários para o desenvolvimento.

### Entregáveis

- Estrutura de diretórios conforme PRD.
- Ambiente Python configurado.
- Arquivo `pyproject.toml`.
- Arquivo `.gitignore`.
- Arquivo `.env.example`.
- Configuração inicial do Pytest.
- Configuração de lint e formatação.
- README inicial.
- Repositório Git inicializado, caso necessário.
- Workflow básico de integração contínua.

### Critérios de aceite

- Estrutura consistente com o PRD.
- Ambiente inicializa corretamente.
- Dependências instaláveis.
- Testes básicos aprovados.
- Nenhuma credencial exposta.
- Documentação de instalação disponível.

### Evidências obrigatórias

- Resultado dos testes.
- Relatório de revisão Codex.
- Relatório de QA Gemini.
- Commit da implementação.

---

## T002 — Auditoria das fontes de dados

**Prioridade:** CRÍTICA  
**Dependências:** T001  
**Status:** PENDENTE

### Entregáveis

- Levantamento das fontes candidatas.
- Análise de licenças e condições de uso.
- Verificação de cobertura do Brasileirão.
- Avaliação das temporadas disponíveis.
- Análise de qualidade e campos.
- Dicionário preliminar.
- Relatório justificando a seleção.

### Critérios de aceite

- Fonte principal documentada.
- Cobertura histórica validada.
- Restrições de uso identificadas.
- Campos essenciais disponíveis.
- Riscos de licenciamento registrados.

**Regra:** não iniciar a coleta em escala antes da aprovação da fonte.

---

## T003 — Pipeline de dados

**Prioridade:** CRÍTICA  
**Dependências:** T002  
**Status:** PENDENTE

### Entregáveis

- Módulo de ingestão.
- Padronização de equipes.
- Tratamento de datas e resultados.
- Validação de duplicidades.
- Tratamento de valores ausentes.
- Persistência em Parquet.
- Consultas DuckDB.
- Testes de integridade.
- Logs de execução.

### Critérios de aceite

- Pipeline reproduzível.
- Dados históricos processados.
- Nenhuma falha crítica de integridade.
- Resultados consistentes com a fonte.
- Testes automatizados aprovados.

---

## T004 — Análise exploratória e estatística

**Prioridade:** ALTA  
**Dependências:** T003  
**Status:** PENDENTE

### Entregáveis

- Estatísticas descritivas.
- Análise de evolução temporal.
- Distribuições de resultados.
- Comparações entre equipes.
- Análise de gols e pontos.
- Identificação de anomalias.
- Investigação das hipóteses.
- Notebook documentado.
- Gráficos exploratórios.

### Critérios de aceite

- Resultados reproduzíveis.
- Conclusões sustentadas pelos dados.
- Limitações documentadas.
- Visualizações legíveis.
- Ausência de afirmações causais indevidas.

---

## T005 — Engenharia de atributos

**Prioridade:** CRÍTICA  
**Dependências:** T003 e T004  
**Status:** PENDENTE

### Entregáveis

- Médias móveis de 3, 5 e 10 partidas.
- Indicadores de desempenho recente.
- Saldo médio de gols.
- Variáveis de mando de campo.
- Indicadores de volatilidade.
- Variáveis temporais.
- Variável-alvo de cinco partidas futuras.
- Dataset analítico.
- Testes contra vazamento temporal.

### Critérios de aceite

- Variáveis calculadas corretamente.
- Ordenação cronológica preservada.
- Nenhuma variável futura utilizada como entrada.
- Dataset reproduzível.
- Testes aprovados.

---

## T006 — Modelagem preditiva

**Prioridade:** CRÍTICA  
**Dependências:** T005  
**Status:** PENDENTE

### Entregáveis

- Modelo baseline.
- Regressão Ridge.
- Random Forest.
- HistGradientBoosting.
- Backtesting temporal.
- Comparação de métricas.
- Registro de experimentos.
- Seleção justificada do modelo.
- Previsões persistidas.

### Critérios de aceite

- Treinamento reproduzível.
- Separação temporal correta.
- MAE e RMSE calculados.
- Baseline utilizado como referência.
- Resultados documentados.
- Modelo selecionado por evidência.

**Regra:** não declarar superioridade de um modelo sem avaliação em dados não utilizados no treinamento.

---

## T007 — Explicabilidade e avaliação

**Prioridade:** ALTA  
**Dependências:** T006  
**Status:** PENDENTE

### Entregáveis

- Análise de importância das variáveis.
- Permutation Importance ou SHAP, quando adequado.
- Análise de resíduos.
- Estudo de erros extremos.
- Avaliação por equipe.
- Avaliação por temporada.
- Documentação das limitações.
- Model Card.

### Critérios de aceite

- Resultados interpretáveis.
- Limitações identificadas.
- Métodos de explicabilidade apropriados.
- Nenhuma interpretação causal sem fundamento.
- Relatório científico concluído.

---

## T008 — Dashboard Power BI

**Prioridade:** ALTA  
**Dependências:** T003, T006 e T007  
**Status:** PENDENTE

### Entregáveis

- Modelo semântico.
- Relacionamentos.
- Medidas DAX.
- Página Visão Geral.
- Página Tendências.
- Página Análise Estatística.
- Página Laboratório de Modelos.
- Página Previsões.
- Página Metodologia.
- Navegação e filtros.
- Validação dos indicadores.

### Critérios de aceite

- Indicadores consistentes com Python/SQL.
- Navegação funcional.
- Filtros corretos.
- Identidade visual consistente.
- Gráficos legíveis.
- Nenhuma falha visual crítica.
- Desempenho aceitável.

**Observação:** a página conversacional dependerá da integração definida em T009.

---

## T009 — Assistente de inteligência artificial

**Prioridade:** ALTA  
**Dependências:** T006 e T008  
**Status:** PENDENTE

### Entregáveis

- Protótipo de integração com Power BI.
- API FastAPI.
- Catálogo de consultas permitidas.
- Interpretação de perguntas.
- Recuperação de indicadores.
- Recuperação de previsões.
- Respostas fundamentadas.
- Tratamento de perguntas fora do escopo.
- Testes de segurança.
- Integração visual com a experiência do dashboard.

### Critérios de aceite

- Perguntas suportadas respondidas corretamente.
- Informações inexistentes não inventadas.
- Consultas não autorizadas bloqueadas.
- Credenciais protegidas.
- Fontes e períodos apresentados.
- Testes funcionais aprovados.

---

## T010 — QA final e publicação

**Prioridade:** ALTA  
**Dependências:** T001 a T009  
**Status:** PENDENTE

### Entregáveis

- Execução da suíte completa.
- Revisão de integridade dos dados.
- Revisão dos modelos.
- Revisão visual do dashboard.
- Revisão do assistente.
- README final.
- Documentação metodológica.
- Model Card.
- Repositório preparado.
- Demonstração pública, quando viável.
- Material para LinkedIn.

### Critérios de aceite

- Nenhum defeito crítico pendente.
- Testes obrigatórios aprovados.
- Documentação completa.
- Credenciais protegidas.
- Licenças verificadas.
- Aprovação final do usuário.

---

# 6. ORQUESTRAÇÃO ENTRE AGENTES

## 6.1 Claude Code — Desenvolvimento

Responsabilidades:

1. Consultar PRD e TASKS.
2. Identificar a próxima tarefa elegível.
3. Analisar somente os arquivos relevantes.
4. Implementar a funcionalidade.
5. Executar testes técnicos.
6. Registrar alterações.
7. Encaminhar para revisão.

O Claude Code não poderá marcar tarefas como CONCLUÍDA.

## 6.2 Codex — Revisão

Responsabilidades:

- Revisar implementação.
- Verificar aderência ao PRD.
- Identificar falhas de lógica.
- Avaliar arquitetura.
- Verificar segurança.
- Revisar testes.
- Identificar regressões.

**Resultados possíveis:**

- APROVADO.
- APROVADO COM OBSERVAÇÕES.
- REPROVADO.

Problemas bloqueantes deverão retornar ao Claude Code.

## 6.3 Gemini/Antigravity — QA

Responsabilidades:

- Executar testes funcionais.
- Validar fluxos.
- Verificar interface, quando aplicável.
- Investigar erros de execução.
- Validar comportamento esperado.
- Registrar evidências.

**Resultados possíveis:**

- APROVADO.
- REPROVADO.
- BLOQUEADO.

## 6.4 Usuário — Aprovação final

O usuário deverá receber um resumo contendo:

- Tarefa executada.
- Funcionalidades entregues.
- Testes realizados.
- Resultado da revisão.
- Resultado do QA.
- Problemas remanescentes.
- Evidências disponíveis.

Somente o usuário poderá aprovar formalmente uma tarefa.

---

# 7. REGRAS DE AUTOMAÇÃO

## 7.1 Fluxo automático desejado

O orquestrador deverá:

1. Identificar a tarefa ativa.
2. Verificar dependências.
3. Encaminhar para Claude Code.
4. Aguardar implementação e testes.
5. Encaminhar para Codex.
6. Avaliar o resultado da revisão.
7. Encaminhar para Gemini/Antigravity.
8. Avaliar os resultados dos testes.
9. Reencaminhar problemas ao Claude Code.
10. Repetir revisão e testes após correções.
11. Solicitar aprovação do usuário.

A passagem automática entre agentes dependerá de integrações ou comandos de execução efetivamente configurados.

**Este documento define o fluxo desejado; não pressupõe que a integração já esteja funcionando.**

## 7.2 Limites de correção

- Até três ciclos automáticos de correção por tarefa.
- Problemas persistentes deverão gerar status BLOQUEADA.
- O orquestrador deverá registrar a causa.
- Não repetir testes completos sem necessidade, exceto quando houver risco de regressão.
- Não alterar o PRD automaticamente.

## 7.3 Controle de contexto

Cada agente deverá receber:

- Identificador da tarefa.
- Requisitos relevantes do PRD.
- Arquivos relacionados.
- Critérios de aceite.
- Resultado da etapa anterior.
- Restrições de implementação.

Evitar enviar todo o histórico do projeto quando um contexto menor for suficiente.

---

# 8. CONTROLE DE GIT

## 8.1 Convenção de branches

`feature/t001-fundacao`

`feature/t002-fontes-dados`

`feature/t003-pipeline`

`feature/t004-eda`

`feature/t005-features`

`feature/t006-modelagem`

`feature/t007-explicabilidade`

`feature/t008-powerbi`

`feature/t009-assistente`

`feature/t010-publicacao`

## 8.2 Convenção de commits

- `feat(T001): configurar estrutura inicial`
- `test(T003): validar integridade dos dados`
- `fix(T006): corrigir vazamento temporal`
- `docs(T007): documentar explicabilidade`
- `refactor(T009): otimizar consultas do assistente`

## 8.3 Política de integração

- Não integrar alterações com testes críticos reprovados.
- Preservar o histórico.
- Não sobrescrever trabalho não relacionado.
- Registrar o commit avaliado.
- Manter a branch principal estável.

---

# 9. REGISTRO DE EVIDÊNCIAS

Para cada tarefa, criar registros em:

`docs/qa/TXXX/`

Arquivos recomendados:

- `implementation.md`
- `codex-review.md`
- `gemini-qa.md`
- `test-results.md`
- `approval.md`

Cada relatório deverá conter:

- ID da tarefa.
- Data.
- Responsável.
- Branch.
- Commit avaliado.
- Testes executados.
- Resultados.
- Defeitos encontrados.
- Status final.

---

# 10. CRITÉRIOS DE CONCLUSÃO

Uma tarefa poderá receber status CONCLUÍDA somente quando:

- [ ] Requisitos do PRD atendidos.
- [ ] Implementação finalizada.
- [ ] Testes técnicos aprovados.
- [ ] Revisão Codex aprovada.
- [ ] QA Gemini/Antigravity aprovado.
- [ ] Problemas bloqueantes corrigidos.
- [ ] Documentação atualizada.
- [ ] Commit registrado.
- [ ] Aprovação do usuário registrada.

---

# 11. HISTÓRICO DE ENTREGAS

| Data | Tarefa | Resultado | Commit |
|---|---|---|---|
| 2026-10-29 | T001 | Código entregue; aguardando revisão Codex, QA Gemini e aprovação | 236671c |
| 2026-10-29 | T002 | Código entregue; aguardando revisão, QA e aprovação | fdd9205 |
| 2026-10-29 | T003 | Código entregue; aguardando revisão, QA e aprovação | 6842876, 82357e6 |
| 2026-10-29 | T004 | Código entregue; aguardando revisão, QA e aprovação | 2dfdfab |
| 2026-10-29 | T005 | Código entregue; aguardando revisão, QA e aprovação | f28105f |
| 2026-10-29 | T006 | Código entregue; aguardando revisão, QA e aprovação | 8319757 |
| 2026-10-29 | T007 | Código entregue; aguardando revisão, QA e aprovação | 03d5e80 |
| 2026-10-29 | T008 | Código entregue; validação visual no Power BI Desktop pendente | d0656a9, 1bb01d8 |
| 2026-10-29 | T009 | Código entregue; aguardando revisão, QA e aprovação | d962e98 |

Nenhuma tarefa foi aprovada formalmente pelo usuário. Revisões Codex e QA Gemini ainda não foram registradas em `docs/qa/`.

O histórico deverá ser atualizado a cada entrega aprovada.

Não registrar tarefas como concluídas sem evidência.

---

# 12. PRÓXIMA TAREFA

**ID:** T010
**Nome:** QA final, documentação e publicação
**Responsável:** Claude Code
**Status:** EM DESENVOLVIMENTO

**Referência:** `docs/PLANO_LANCAMENTO_WEB.md` (fases F0 a F5, com prompts por fase).

**Fase atual:** F0 (higiene e base) concluída em código. Próxima: F1 — assistente v2 com Claude.

---

# 13. REGRA PERMANENTE DE EFICIÊNCIA

Trabalhe de forma eficiente, aproveitando o código existente. Evite análises repetitivas, reconstruções desnecessárias e consumo excessivo de tokens. Implemente em etapas, execute testes relevantes e preserve as funcionalidades atuais.

---

# 14. REGRAS FINAIS

1. O PRD define o que será construído.
2. O TASKS define a ordem e o controle da execução.
3. Claude Code implementa.
4. Codex revisa.
5. Gemini/Antigravity testa.
6. O orquestrador controla as transições.
7. O usuário aprova as entregas.
8. Nenhuma tarefa deverá ser considerada concluída sem evidências.
9. Alterações de escopo exigem atualização do PRD.
10. A qualidade científica tem prioridade sobre a complexidade visual.

**Status do projeto:** T001–T009 entregues em código; T010 em desenvolvimento  
**Próxima execução:** T010, fase F1 — assistente v2 (ver plano de lançamento).