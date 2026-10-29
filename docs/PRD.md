# PRD — ALÉM DO PLACAR
## Inteligência Esportiva, Ciência de Dados e Análise Preditiva

**Versão:** 1.0  
**Status:** Aprovado para planejamento técnico  
**Responsável:** Vinícius Ribeiro  
**Data:** 29/10/2026  
**Modalidade:** Futebol  
**Competição inicial:** Campeonato Brasileiro Série A  
**Tipo:** Projeto de portfólio em Ciência de Dados e Business Intelligence

---

# 1. VISÃO GERAL

## 1.1 Descrição

O Além do Placar é uma plataforma analítica de inteligência esportiva que combina Engenharia de Dados, Estatística, Machine Learning, Power BI e Inteligência Artificial.

O projeto permitirá analisar a evolução histórica de equipes de futebol, identificar tendências de desempenho e gerar previsões estatísticas fundamentadas em dados.

Um assistente inteligente permitirá que os usuários realizem perguntas em linguagem natural sobre indicadores, tendências, comparações e previsões.

## 1.2 Problema

As informações esportivas são frequentemente apresentadas de maneira descritiva e fragmentada, dificultando a identificação de padrões, tendências e mudanças de desempenho.

O projeto busca responder:

**É possível antecipar a evolução do desempenho de uma equipe de futebol utilizando seus indicadores históricos?**

## 1.3 Objetivo principal

Construir uma solução de Ciência de Dados de ponta a ponta, demonstrando competências em:

- Coleta e engenharia de dados.
- SQL e modelagem analítica.
- Análise exploratória e estatística.
- Engenharia de atributos.
- Machine Learning supervisionado.
- Séries temporais e backtesting.
- Explicabilidade de modelos.
- Business Intelligence.
- Inteligência artificial conversacional.
- Testes automatizados e documentação técnica.

## 1.4 Resultados esperados

O produto deverá permitir:

1. Analisar a evolução de equipes em diferentes temporadas.
2. Identificar tendências de crescimento, estabilidade e declínio.
3. Comparar o desempenho histórico de clubes.
4. Prever a média de pontos nas próximas cinco partidas.
5. Apresentar intervalos de incerteza.
6. Explicar os principais fatores associados às previsões.
7. Responder perguntas fundamentadas nos dados disponíveis.
8. Demonstrar a qualidade e as limitações dos modelos utilizados.

---

# 2. ESCOPO CIENTÍFICO

## 2.1 População analisada

Clubes participantes do Campeonato Brasileiro Série A.

## 2.2 Período histórico

Período candidato: temporadas de 2015 a 2025.

A utilização dependerá da disponibilidade, integridade, cobertura e licença dos dados.

A temporada de 2026 poderá ser reservada para avaliação temporal final, mediante definição prévia da data de corte.

## 2.3 Hipóteses

**H01:** indicadores recentes de desempenho ajudam a prever a evolução futura das equipes.

**H02:** médias móveis de desempenho apresentam maior capacidade preditiva que médias históricas isoladas.

**H03:** diferenças entre desempenho como mandante e visitante contribuem para melhorar as previsões.

**H04:** volatilidade de resultados e saldo de gols ajudam a identificar mudanças de tendência.

**H05:** modelos de Machine Learning podem superar modelos estatísticos baseline.

**H06:** métricas avançadas, como xG, quando disponíveis, podem oferecer ganhos preditivos adicionais.

Todas as hipóteses deverão ser avaliadas empiricamente.

---

# 3. FONTES DE DADOS

## 3.1 Fontes candidatas

- Football-Data: https://www.football-data.co.uk/data.php
- StatsBomb Open Data: https://github.com/statsbomb/open-data
- OpenFootball: https://github.com/openfootball
- Outras fontes públicas documentadas e licenciadas.

## 3.2 Política de utilização

Antes de incorporar qualquer fonte, verificar:

- Permissão de uso.
- Restrições de redistribuição.
- Condições de atribuição.
- Permissão para processamento automatizado.
- Possíveis restrições de uso com inteligência artificial.
- Cobertura temporal e consistência dos registros.

Nenhum conjunto de dados será considerado aprovado apenas por estar disponível publicamente.

## 3.3 Campos mínimos

- Identificador da partida.
- Data da partida.
- Temporada.
- Competição.
- Equipe mandante.
- Equipe visitante.
- Gols do mandante.
- Gols do visitante.
- Resultado final.
- Rodada, quando disponível.

## 3.4 Campos complementares

- Finalizações.
- Finalizações no alvo.
- Posse de bola.
- Cartões.
- Escanteios.
- Expected Goals (xG).
- Dias de descanso.
- Outras estatísticas relevantes.

Campos complementares serão opcionais e não poderão impedir o funcionamento do núcleo do MVP.

---

# 4. ARQUITETURA TÉCNICA

## 4.1 Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem principal | Python |
| Manipulação de dados | Pandas / NumPy |
| Consultas analíticas | SQL |
| Banco local | DuckDB |
| Armazenamento | Parquet |
| Machine Learning | Scikit-learn |
| Experimentos | MLflow |
| API | FastAPI |
| Dashboard | Power BI |
| Linguagem analítica | DAX |
| Assistente | API de modelo de linguagem |
| Testes | Pytest |
| Versionamento | Git / GitHub |

## 4.2 Fluxo de processamento

1. Coleta dos dados.
2. Validação de integridade.
3. Limpeza e padronização.
4. Armazenamento de dados brutos.
5. Construção de tabelas analíticas.
6. Engenharia de atributos.
7. Treinamento dos modelos.
8. Backtesting e avaliação.
9. Geração de previsões.
10. Persistência dos resultados.
11. Consumo pelo Power BI.
12. Consulta pelo assistente de IA.

## 4.3 Princípios arquiteturais

- Separação entre coleta, transformação, modelagem e apresentação.
- Configurações externas ao código.
- Credenciais armazenadas de maneira segura.
- Componentes reutilizáveis.
- Processos reproduzíveis.
- Testes automatizados.
- Rastreabilidade dos resultados.
- Controle de versões de dados e modelos.

---

# 5. MODELO DE DADOS

## 5.1 Tabelas principais

**dim_equipes**

- equipe_id
- nome
- nome_padronizado

**dim_temporadas**

- temporada_id
- ano
- competicao

**fato_partidas**

- partida_id
- data_partida
- temporada_id
- equipe_mandante_id
- equipe_visitante_id
- gols_mandante
- gols_visitante
- resultado

**fato_desempenho_equipes**

- partida_id
- equipe_id
- pontos
- gols_pro
- gols_contra
- saldo_gols
- mando_campo
- rodada

**fato_previsoes**

- previsao_id
- equipe_id
- data_corte
- horizonte
- media_pontos_prevista
- limite_inferior
- limite_superior
- modelo_versao

**fato_avaliacao_modelos**

- experimento_id
- modelo
- versao
- periodo_teste
- mae
- rmse
- vies
- data_execucao

## 5.2 Regras de integridade

- Cada partida deverá possuir identificador único.
- Cada partida produzirá duas observações de desempenho, uma por equipe.
- Pontos deverão obedecer à regra 3, 1 ou 0.
- Identificadores de equipes deverão ser consistentes entre temporadas.
- Dados ausentes deverão ser identificados explicitamente.
- Previsões deverão possuir data de corte e versão do modelo.

---

# 6. ENGENHARIA DE ATRIBUTOS

## 6.1 Variáveis candidatas

- Média de pontos nas últimas 3 partidas.
- Média de pontos nas últimas 5 partidas.
- Média de pontos nas últimas 10 partidas.
- Média de gols marcados.
- Média de gols sofridos.
- Saldo médio de gols.
- Aproveitamento recente.
- Desempenho como mandante.
- Desempenho como visitante.
- Desvio-padrão dos pontos recentes.
- Força estimada dos adversários.
- Rodada atual.
- Posição histórica calculada até a data de corte.

## 6.2 Regras

Nenhuma variável poderá utilizar informações posteriores à data de referência da previsão.

As janelas móveis deverão ser calculadas por equipe, em ordem cronológica.

Dados indisponíveis antes do início de uma temporada deverão receber tratamento documentado.

---

# 7. MODELAGEM PREDITIVA

## 7.1 Problema principal

Prever a média de pontos por partida que uma equipe obterá nas próximas cinco partidas.

**Variável-alvo:**

`media_pontos_futuros_5 = soma_pontos_proximas_5_partidas / 5`

A variável deverá ser calculada somente para observações históricas com cinco partidas futuras disponíveis.

## 7.2 Modelos candidatos

**M00 — Baseline**

Média móvel recente.

**M01 — Ridge Regression**

Modelo linear regularizado e interpretável.

**M02 — Random Forest Regressor**

Modelo não linear baseado em árvores.

**M03 — HistGradientBoosting Regressor**

Modelo de boosting para comparação de desempenho.

## 7.3 Validação

- Separação temporal entre treinamento e teste.
- Backtesting com janelas expansivas.
- Prevenção de vazamento de dados.
- Tratamento de sobreposição entre horizontes de previsão.
- Comparação com baseline.
- Avaliação por temporada e equipe.

## 7.4 Métricas

**Primárias:**

- MAE.
- RMSE.

**Complementares:**

- Viés médio.
- Erro por equipe.
- Erro por temporada.
- Estabilidade temporal.
- Cobertura dos intervalos de previsão.

## 7.5 Critério de seleção

O modelo principal deverá superar o baseline em dados de teste temporal e apresentar estabilidade aceitável.

Caso nenhum modelo apresente ganho consistente, o baseline será mantido como solução principal, com os resultados documentados.

## 7.6 Explicabilidade

Implementar, quando adequado:

- Importância de variáveis.
- Permutation Importance.
- SHAP.
- Análise de resíduos.
- Investigação de erros extremos.

Importância preditiva não deverá ser apresentada como evidência de causalidade.

---

# 8. POWER BI

## 8.1 Página 01 — Visão Geral

Apresentar:

- Total de equipes analisadas.
- Temporadas disponíveis.
- Quantidade de partidas.
- Média de gols.
- Média de pontos.
- Rankings de desempenho.
- Indicadores de evolução.

## 8.2 Página 02 — Tendências

- Evolução temporal.
- Médias móveis.
- Crescimento e declínio.
- Comparação de equipes.
- Consistência de desempenho.
- Análise por temporada.

## 8.3 Página 03 — Análise Estatística

- Distribuições.
- Correlações.
- Dispersões.
- Volatilidade.
- Comparações históricas.
- Indicadores avançados disponíveis.

## 8.4 Página 04 — Laboratório de Modelos

- Comparação de algoritmos.
- MAE e RMSE.
- Baseline versus modelos.
- Erros históricos.
- Importância das variáveis.
- Versão e período de treinamento.

## 8.5 Página 05 — Previsões

- Seleção de equipe.
- Desempenho recente.
- Projeção para cinco partidas.
- Intervalos de incerteza.
- Histórico versus previsão.
- Explicação dos fatores associados.

## 8.6 Página 06 — Assistente Inteligente

Interface de perguntas e respostas sobre dados, tendências e previsões.

A implementação poderá utilizar uma aplicação web complementar ao Power BI, caso as restrições técnicas impeçam a experiência desejada diretamente no relatório.

## 8.7 Página 07 — Metodologia

- Fontes.
- Períodos analisados.
- Metodologia estatística.
- Modelos.
- Limitações.
- Métricas de qualidade.
- Informações de atualização.

## 8.8 Identidade visual

- Interface profissional.
- Preferência por tema claro.
- Paleta de cores limitada.
- Tipografia consistente.
- Navegação superior.
- Gráficos legíveis.
- Espaçamento uniforme.
- Contraste acessível.
- Consistência entre páginas.

---

# 9. ASSISTENTE DE INTELIGÊNCIA ARTIFICIAL

## 9.1 Objetivo

Permitir consultas em português sobre os dados e previsões do projeto.

## 9.2 Exemplos de perguntas

- Qual equipe mais evoluiu nas últimas dez rodadas?
- Quais clubes apresentam tendência de queda?
- Qual equipe foi mais consistente na temporada?
- Qual é a previsão de desempenho do Flamengo?
- Por que o modelo prevê crescimento para determinada equipe?
- Quais variáveis mais influenciaram o modelo?
- Qual é o erro médio das previsões?

## 9.3 Fluxo técnico

1. Receber pergunta.
2. Identificar intenção e entidades.
3. Validar escopo.
4. Selecionar consulta autorizada.
5. Recuperar indicadores ou previsões.
6. Verificar disponibilidade dos dados.
7. Produzir resposta fundamentada.
8. Apresentar fonte, período e limitações.

## 9.4 Regras obrigatórias

- Não inventar dados.
- Não executar SQL arbitrário gerado pela IA.
- Não apresentar previsões como certezas.
- Não utilizar informações externas sem autorização.
- Não divulgar credenciais.
- Não confundir correlação com causalidade.
- Informar ausência de dados.
- Diferenciar resultados históricos de previsões.

## 9.5 Resposta para informações indisponíveis

"Não é possível calcular essa informação com os dados atualmente disponíveis no projeto."

Quando possível, explicar qual informação está faltando.

---

# 10. REQUISITOS NÃO FUNCIONAIS

**RNF01 — Segurança:** proteção de chaves e credenciais.

**RNF02 — Desempenho:** otimização das consultas e carregamento do dashboard.

**RNF03 — Reprodutibilidade:** execução documentada do pipeline.

**RNF04 — Manutenibilidade:** código modular, tipado quando apropriado e testável.

**RNF05 — Acessibilidade:** contraste, legibilidade e navegação compreensível.

**RNF06 — Escalabilidade:** possibilidade de incluir novas competições.

**RNF07 — Rastreabilidade:** registro de fontes, versões e experimentos.

**RNF08 — Disponibilidade:** versão demonstrável do produto, respeitando dependências externas.

**RNF09 — Transparência:** comunicação das limitações dos dados e modelos.

---

# 11. ESTRUTURA DE DIRETÓRIOS

```text
alem-do-placar/
│
├── PRD.md
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── config/
│   └── settings.yaml
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── predictions/
│
├── notebooks/
│   ├── 01_exploracao.ipynb
│   ├── 02_estatistica.ipynb
│   └── 03_modelagem.ipynb
│
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── processing/
│   ├── features/
│   ├── models/
│   ├── evaluation/
│   └── api/
│
├── dashboard/
│   ├── powerbi/
│   └── assets/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── model/
│   └── api/
│
├── reports/
│   ├── figures/
│   └── metrics/
│
├── docs/
│   ├── architecture.md
│   ├── methodology.md
│   ├── data_dictionary.md
│   └── model_card.md
│
└── .github/
    └── workflows/
```

Dados brutos, modelos grandes, credenciais e arquivos temporários deverão ser tratados conforme a política de versionamento.

---

# 12. PLANO DE EXECUÇÃO

## T001 — Fundação do projeto

**Entregáveis:**

- Estrutura inicial de diretórios.
- Ambiente Python.
- Configuração do Git.
- Dependências.
- README inicial.
- Configuração de testes.
- CI básica.

**Critério de aceite:** projeto inicializa e os testes básicos executam sem erros.

## T002 — Auditoria das fontes

**Entregáveis:**

- Avaliação das fontes candidatas.
- Verificação de licença.
- Análise de cobertura.
- Dicionário preliminar.
- Escolha da fonte principal.

**Critério de aceite:** fonte selecionada com justificativa documentada.

## T003 — Pipeline de dados

**Entregáveis:**

- Coleta.
- Padronização.
- Validação.
- Persistência em Parquet.
- Consultas SQL.
- Testes de integridade.

**Critério de aceite:** pipeline reproduzível e sem falhas críticas.

## T004 — Análise exploratória

**Entregáveis:**

- Estatísticas descritivas.
- Distribuições.
- Análise temporal.
- Identificação de anomalias.
- Hipóteses investigadas.

**Critério de aceite:** relatório exploratório documentado.

## T005 — Engenharia de atributos

**Entregáveis:**

- Médias móveis.
- Indicadores de desempenho.
- Variáveis temporais.
- Variável-alvo.
- Testes de vazamento.

**Critério de aceite:** conjunto analítico validado cronologicamente.

## T006 — Modelagem preditiva

**Entregáveis:**

- Baseline.
- Modelos candidatos.
- Treinamento.
- Backtesting.
- Métricas.
- Seleção do modelo.
- Registro de experimentos.

**Critério de aceite:** avaliação temporal reproduzível e comparação documentada.

## T007 — Explicabilidade

**Entregáveis:**

- Importância de variáveis.
- Análise de resíduos.
- Estudo de erros.
- Interpretação das previsões.
- Model Card.

**Critério de aceite:** limitações e fatores preditivos documentados.

## T008 — Dashboard Power BI

**Entregáveis:**

- Modelo semântico.
- Medidas DAX.
- Páginas analíticas.
- Filtros.
- Navegação.
- Validação dos indicadores.

**Critério de aceite:** indicadores conferem com os resultados calculados em Python/SQL.

## T009 — Assistente inteligente

**Entregáveis:**

- API FastAPI.
- Catálogo de consultas permitidas.
- Integração com modelo de linguagem.
- Respostas fundamentadas.
- Tratamento de erros.
- Testes de segurança e alucinação.

**Critério de aceite:** assistente responde corretamente às perguntas de referência e rejeita consultas sem suporte.

## T010 — QA e publicação

**Entregáveis:**

- Testes finais.
- Revisão visual.
- Documentação.
- Repositório GitHub.
- Dashboard demonstrável.
- Case para LinkedIn.

**Critério de aceite:** todos os requisitos críticos aprovados.

---

# 13. ESTRATÉGIA DE TESTES

## 13.1 Testes de dados

- Integridade de identificadores.
- Duplicidades.
- Valores ausentes.
- Consistência de resultados.
- Ordenação temporal.
- Padronização de equipes.

## 13.2 Testes de Machine Learning

- Ausência de vazamento temporal.
- Separação correta de treino e teste.
- Reprodutibilidade.
- Comparação com baseline.
- Consistência das métricas.
- Validação dos intervalos preditivos.

## 13.3 Testes de Power BI

- Validação das medidas.
- Filtros e relacionamentos.
- Navegação.
- Consistência dos gráficos.
- Performance.
- Legibilidade.

## 13.4 Testes do assistente

- Perguntas suportadas.
- Perguntas ambíguas.
- Perguntas fora do escopo.
- Informações inexistentes.
- Tentativas de manipulação de instruções.
- Tentativas de consultas não autorizadas.
- Consistência dos valores retornados.

## 13.5 Testes de regressão

Alterações no código não poderão comprometer funcionalidades previamente aprovadas.

---

# 14. INDICADORES DE SUCESSO

| Indicador | Meta inicial |
|---|---|
| Integridade dos dados | 100% dos testes críticos aprovados |
| Reprodutibilidade | Pipeline executável conforme documentação |
| Modelagem | Baseline e pelo menos 2 candidatos avaliados |
| Validação | Backtesting temporal documentado |
| Qualidade preditiva | Superar baseline quando demonstrado empiricamente |
| Explicabilidade | Fatores e limitações apresentados |
| Dashboard | Todas as páginas essenciais funcionais |
| Assistente | Pelo menos 90% de acerto no conjunto de referência |
| Segurança do assistente | 100% dos testes críticos aprovados |
| Documentação | README, metodologia e Model Card |
| Portfólio | Publicação final no GitHub e LinkedIn |

---

# 15. RISCOS E DEPENDÊNCIAS

| Risco | Severidade | Mitigação |
|---|---|---|
| Cobertura insuficiente de dados | Alta | Auditoria antes da implementação |
| Licenciamento restritivo | Alta | Seleção de fonte compatível |
| Vazamento temporal | Crítica | Testes e backtesting |
| Modelos sem ganho preditivo | Alta | Comparação com baseline |
| Alucinação da IA | Crítica | Consultas controladas |
| Limitações de integração Power BI | Alta | Protótipo de viabilidade |
| Custos de APIs | Média | Limites e monitoramento |
| Escopo excessivo | Alta | Desenvolvimento por etapas |

---

# 16. FORA DO ESCOPO DO MVP

- Previsão garantida de resultados.
- Recomendações de apostas.
- Transmissão de partidas.
- Atualização em tempo real.
- Aplicativo mobile nativo.
- Cobertura de todas as ligas.
- Treinamento de LLM próprio.
- Infraestrutura empresarial de alta disponibilidade.

---

# 17. DEFINITION OF DONE

Uma tarefa será considerada concluída quando:

1. A implementação corresponder aos requisitos.
2. O código estiver organizado.
3. Os testes relevantes forem executados.
4. Não houver falhas críticas conhecidas.
5. A documentação necessária estiver atualizada.
6. As funcionalidades anteriores forem preservadas.
7. O resultado puder ser reproduzido.
8. A alteração estiver registrada no Git.

O projeto completo será considerado concluído quando o pipeline, os modelos, o dashboard, o assistente e a documentação estiverem integrados e validados.

---

# 18. DIRETRIZES PERMANENTES DE DESENVOLVIMENTO

**Instrução obrigatória para agentes de desenvolvimento:**

Trabalhe de forma eficiente, aproveitando o código existente. Evite análises repetitivas, reconstruções desnecessárias e consumo excessivo de tokens. Implemente em etapas, execute testes relevantes e preserve as funcionalidades atuais.

**Diretrizes complementares:**

- Consultar este PRD antes de implementar funcionalidades.
- Não iniciar múltiplas etapas sem validação.
- Não modificar requisitos críticos sem registrar a decisão.
- Não recriar componentes funcionais desnecessariamente.
- Priorizar testes automatizados.
- Registrar decisões arquiteturais relevantes.
- Evitar dependências sem justificativa técnica.
- Preservar a rastreabilidade científica.
- Não sacrificar a qualidade dos modelos em favor da aparência visual.

---

# 19. CRITÉRIOS PARA PUBLICAÇÃO

Antes da publicação:

- Revisar as licenças dos dados.
- Validar resultados científicos.
- Confirmar ausência de credenciais.
- Executar testes.
- Revisar o design.
- Preparar README e documentação.
- Criar demonstração do dashboard.
- Publicar o repositório.
- Preparar apresentação do projeto no LinkedIn.

**Mensagem central do portfólio:**

"Além do Placar é um projeto de Ciência de Dados que investiga tendências de desempenho no futebol brasileiro, combinando engenharia de dados, modelos preditivos, análise estatística, Power BI e inteligência artificial para transformar dados históricos em informações interpretáveis."

---

# 20. CONTROLE DE APROVAÇÃO

**Versão:** 1.1  
**Status:** Planejamento técnico definido; implementação pendente  
**Responsável:** Vinícius Ribeiro

**Próxima tarefa:** T001 — Fundação do projeto.

**Restrições pendentes:** aprovação da fonte de dados, verificação das licenças e validação técnica da integração do assistente.

**Princípio final:** o Além do Placar deverá ser um projeto cientificamente defensável, tecnicamente reproduzível e visualmente profissional.