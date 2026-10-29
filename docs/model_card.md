# Model Card — Além do Placar (T006)

**Status:** execução histórica real realizada pelo controlador, com fonte OpenFootball CC0 de 2018–2025 e holdout exclusivo de 2025. Não há dados de 2026.

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

## Limitações

- Dados observacionais e uma única competição; resultados não são causais.
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
python -B -m pytest tests/unit/test_backtesting.py tests/unit/test_experimentos.py
```

