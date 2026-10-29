# Model Card — Além do Placar (T006–T007)

**Status:** execução histórica real (T006) realizada pelo controlador, com fonte OpenFootball CC0 de 2018–2025 e holdout exclusivo de 2025. Não há dados de 2026.

Explicabilidade e avaliação científica (T007): código, testes e execução real entregues. Os números abaixo vêm de `data/predictions/cientifica/relatorio_cientifico.md`.

## Modelo e alvo

- **Alvo:** `media_pontos_futuros_5`, média de pontos nas cinco partidas seguintes da mesma equipe e temporada, calculada após o jogo de referência (pós-jogo).
- **Horizonte:** 5 partidas. Observações com horizonte incompleto não recebem alvo.
- **Candidatos:** M00 média recente de 5 partidas (baseline); M01 Ridge; M02 Random Forest; M03 HistGradientBoosting. B01 média histórica do treino é referência adicional.
- **Seleção:** modelo ML só é escolhido com ganho mínimo de 2% no MAE médio de validação e sem piora superior a 10% em nenhum ano. Caso contrário, M00 é mantido.

## Atributos (FEATURES)

`media_pontos_3`, `media_pontos_5`, `media_pontos_10`, `media_saldo_gols_3`, `media_saldo_gols_5`, `media_saldo_gols_10`, `desvio_pontos_5`, `media_pontos_mandante_historico`, `media_pontos_visitante_historico`, `jogos_acumulados`, `dias_descanso`, `mando`.

Identificadores, pontos e gols da partida atual, rodada, alvo e `fim_alvo` não são entradas.

## Validação e corte

- Backtesting por temporadas com janela expansiva: validação em 2022–2024 e holdout em 2025.
- Treino de cada fold: somente linhas com data de referência e `fim_alvo` estritamente anteriores à primeira data do teste.
- 2026 não é processado.
- O holdout não participa da seleção. O modelo escolhido é reajustado uma única vez com dados anteriores a 2025.
- Previsões são cortadas no intervalo [0, 3].

## Intervalo de previsão

Intervalo de 90% empírico: quantil de 90% dos erros absolutos das previsões de validação do modelo escolhido. A cobertura é medida no holdout. Não há garantia estatística, porque os alvos de partidas consecutivas se sobrepõem no tempo.

## Explicabilidade e avaliação científica (T007)

- **Função:** `avaliar_cientificamente` em `src/evaluation/cientifica.py` (versão `T007-1.0`). Consome a saída de `executar_backtest` e usa o modelo congelado em memória. Não há treino, reajuste nem carregamento de pickle externo.
- **Resíduos:** resíduo = previsão − alvo. São reportados MAE, RMSE, viés, cobertura do intervalo e n, no holdout de 2025, por equipe e por temporada. Diferenças entre equipes com n diferente não são ranking de mérito.
- **Erros extremos:** as 10 maiores observações por erro absoluto.
- **Importância por permutação:** cada atributo é embaralhado no holdout congelado, com seed 42 e 5 repetições por padrão. ΔMAE = MAE embaralhado − MAE original. Valores negativos são mantidos. É medida preditiva e exploratória: não é estudo causal nem ablação, e atributos correlacionados podem dividir a importância. Não altera seleção, parâmetros ou treino.
- **Comparação:** modelo selecionado contra M00 no holdout. B01 (média histórica global do treino) aparece somente na validação.
- **Hipóteses:**
  - H01 (indicadores recentes): resultado observado nesta comparação, sem generalização.
  - H02 (médias móveis contra médias históricas): comparação específica de M00 contra B01 na validação. B01 não é média por clube.
  - H03 (mando) e H04 (volatilidade e saldo de gols): não conclusivas. A importância é preditiva e exploratória.
  - H05 (ML contra baseline): resultado observado nesta comparação, sem generalização para outras temporadas ou competições.
  - H06 (xG): não avaliável. xG não está disponível e nenhum valor foi preenchido com zero.
- **Não há** valor-p, intervalo estatístico nem teste de significância para os erros.
- **Saídas** (pasta explícita): `relatorio_cientifico.json`, `relatorio_cientifico.md`, `importancias.csv`, `residuos.parquet` e três PNGs (distribuição dos resíduos, previsto versus observado com linha de identidade, importância por permutação).

### Resultados da execução T007

Fonte: `data/predictions/cientifica/relatorio_cientifico.md` (versão T007-1.0, seed 42, 5 repetições de permutação, holdout 2025 de 2025-03-29 a 2025-11-15).

| Métrica (holdout, n=660) | M01_ridge | M00_media_recente_5 |
|---|---:|---:|
| MAE | 0.478089 | 0.567091 |
| RMSE | 0.590887 | 0.722596 |
| Viés | -0.016830 | -0.001520 |

Diferença de MAE (selecionado menos baseline): -0.089002. Cobertura do intervalo de 90%: 91,21%.

Importância por permutação (ΔMAE médio, maiores): media_saldo_gols_5 +0.0151; media_pontos_visitante_historico +0.0124; media_pontos_10 +0.0058; media_pontos_5 +0.0039; media_pontos_mandante_historico +0.0031. Mando e dias de descanso ficaram próximos de zero ou negativos. É medida preditiva exploratória, não causal.

Hipóteses (resultado observado nesta comparação, sem generalização):

- H01 e H05: favoráveis. O Ridge supera o baseline no holdout.
- H02: desfavorável. Na validação, a média recente (MAE 0.604) ficou pior que a média histórica global do treino (MAE 0.515). A referência B01 não é média por clube.
- H03 e H04: não conclusivas.
- H06: não avaliável, pois xG não está disponível.

Erros extremos concentram-se em São Paulo, Bragantino e Vasco no segundo semestre de 2025. Os erros por equipe têm viés de sinal variado (por exemplo, SC Recife +0.52 e Mirassol -0.33), então não há ranking de mérito.

## Limitações

- Dados observacionais e uma única competição; resultados não são causais.
- Avaliação em um único holdout temporal; amostra pequena por equipe.
- Alvos de partidas consecutivas se sobrepõem no tempo; as observações não são independentes.
- Previsões não são certezas nem recomendações de apostas.
- Qualquer resultado depende da fonte OpenFootball CC0 auditada (T002–T003).

## Persistência e segurança

- Modelos são gravados com joblib apenas para objetos criados pelo projeto.
- Pickles externos nunca são carregados.
- Os experimentos são registrados em MLflow local (SQLite), sem servidor, nuvem ou credenciais.

## Métricas

Resultados reais (660 observações de holdout com horizonte completo):

| Modelo | MAE | RMSE | Viés |
|---|---:|---:|---:|
| M00_media_recente_5 | 0.567091 | 0.722596 | -0.001520 |
| M01_ridge | 0.478089 | 0.590887 | -0.016830 |

Modelo selecionado na validação: **M01_ridge**. MAE médio de validação 0.488755 contra 0.604116 do baseline recente. Cobertura empírica no holdout: 91.21%. Corte exclusivo do treino: 2025-03-29. O holdout não foi usado para escolher o modelo. Rastreamento local SQLite, run_id `1c65e28718854750b7d3f35b0c972fa1`.

## Reprodução

```powershell
python -m pip install -e ".[test,lint]"
python -B -m pytest tests/unit/test_backtesting.py tests/unit/test_experimentos.py tests/unit/test_cientifica.py
```
