# Auditoria do pipeline de Ciência de Dados

**Data:** 29/10/2026 · **Escopo:** atributos, divisão temporal, modelos, métricas, previsões e coerência com o dashboard e a Central de Consulta · **Resultado:** nenhuma falha que exija mudar métricas ou previsões; sete ressalvas documentadas abaixo. A metodologia não foi alterada.

## O que foi verificado

| Item | Situação | Evidência |
|---|---|---|
| Variável-alvo | `media_pontos_futuros_5`: soma dos pontos dos 5 jogos seguintes da mesma equipe e temporada, ÷ 5. Horizonte incompleto não recebe alvo. | `src/features/temporais.py` (`_media_futura`) |
| Divisão dos dados | Janela expansiva: validação em 2022, 2023 e 2024; teste exclusivo em 2025. O treino de cada etapa só usa linhas com data de referência **e** fim do alvo anteriores ao início do período avaliado. | `src/models/backtesting.py` (linha com `fim_alvo < inicio`) |
| Modelos treinados | Referências: média dos últimos 5 jogos (M00) e média histórica do treino (B01). Machine Learning: Ridge (mediana + padronização + `alpha=1`), Random Forest (50 árvores, profundidade 6) e Gradient Boosting (80 iterações, profundidade 4). Semente 42. | `src/models/backtesting.py` |
| Métricas | MAE, RMSE e viés, por fase, temporada e equipe. Seleção: ganho mínimo de 2% no MAE médio de validação e nenhuma temporada com piora acima de 10%. | `data/predictions/modelagem/metricas.json`, `docs/model_card.md` |
| Vazamento de dados | Não encontrado. Atributos usam apenas jogos encerrados até o jogo de referência; o alvo começa no jogo seguinte; a imputação (mediana) é ajustada dentro do pipeline, só no treino; o corte por `fim_alvo` impede que alvos do período avaliado entrem no treino. | Código acima e `tests/unit/test_features_temporais.py`, `test_backtesting.py` |
| Comparação com baseline | Sim. Ridge: MAE 0,489 na validação contra 0,604 da média recente; no teste, 0,478 contra 0,567. | `metricas.json` |
| Reprodutibilidade | Semente fixa, artefatos finais versionados, MLflow local (SQLite) com o `run_id` no model card. | `docs/model_card.md` |
| Coerência temporal das previsões | Previsões de 29/03/2025 a 15/11/2025: as últimas rodadas não têm 5 jogos futuros e corretamente não têm previsão. Valores limitados a [0, 3]. | `previsoes.parquet` |
| Dashboard igual ao código | Os cartões e tabelas do Power BI, o site e a Central leem os mesmos arquivos (`metricas.json`, `metadados.json`, `previsoes.parquet`, Parquet processados). O teste de fumaça conferiu 35 valores contra cálculos independentes; a Central recalcula a classificação e foi testada contra o desempate. | `scripts/smoke_test.py`, `tests/js/motor.test.mjs`, `docs/qa/T010/test-results.md` |

## Ressalvas (documentadas, sem alteração de resultados)

1. **Hipótese H02 não confirmada.** Na validação, a média dos últimos 5 jogos (MAE 0,604) foi pior que a média histórica global do treino (0,515). O ganho do Ridge vem da combinação de atributos; o experimento não isola cada contribuição.
2. **Faixa de incerteza constante.** O intervalo de 90% é o quantil dos erros absolutos da validação (cerca de ±1,0 ponto por jogo em uma escala de 0 a 3), igual para todas as previsões. A cobertura observada no teste foi 91,2%, mas a faixa é larga e não se adapta à equipe ou ao momento. Melhoria sugerida: intervalos condicionais (por exemplo, regressão quantílica), avaliados com a mesma separação temporal.
3. **Atributos reiniciam a cada temporada.** As janelas móveis são calculadas dentro da temporada; nas primeiras rodadas, valores ausentes são preenchidos com a mediana do treino. Não é vazamento, mas reduz a informação disponível no início do campeonato.
4. **Um único período de teste.** Há só um holdout (2025), cerca de 33 observações por equipe e alvos sobrepostos entre jogos consecutivos. Não há teste de significância para a diferença entre modelos.
5. **Comparação parcial no teste.** Apenas o modelo escolhido e a referência M00 foram avaliados em 2025, como manda o protocolo (o teste não deve orientar a escolha). B01, Random Forest e Gradient Boosting aparecem só na validação.
6. **Zonas da tabela simplificadas.** As zonas seguem a posição (1–4, 5–6, 7–12, 17–20). Vagas extras por títulos da Copa do Brasil ou da Libertadores não são consideradas. O desempate aplica pontos, vitórias, saldo e gols marcados; confronto direto e cartões não estão nos dados.
7. **Destaques individuais externos.** Artilheiros e prêmios vêm da Wikipédia em português, sem conferência direta com a CBF. Em 2023, a fonte não registra Craque nem Melhor Goleiro, e a ausência é mostrada como tal. Não há dados individuais de goleiros (gols sofridos por atleta); o cartão usa os gols sofridos pelo clube.

## Próximos passos recomendados

- Usar a temporada de 2026, quando completa, como segundo teste temporal, sem reajustar a escolha do modelo.
- Avaliar intervalos condicionais e medir a cobertura por equipe.
- Considerar atributos que atravessem temporadas (por exemplo, desempenho final da temporada anterior), validados com a mesma regra de corte.
