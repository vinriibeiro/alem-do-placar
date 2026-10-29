# Relatório científico — Além do Placar (T007)

- Versão da avaliação: T007-1.0
- Versão do backtesting: T006-1.0
- Modelo selecionado: M01_ridge
- Holdout: 2025; período 2025-03-29 a 2025-11-15
- Corte do treino: 2025-03-29; seed 42; repetições de permutação: 5

## Métricas no holdout

| n | mae | rmse | vies | cobertura_intervalo |
|---|---|---|---|---|
| 660 | 0.478089 | 0.590887 | -0.016830 | 0.912121 |

## Comparação com o baseline (holdout)

| modelo | n | mae | rmse | vies |
|---|---|---|---|---|
| M01_ridge | 660 | 0.478089 | 0.590887 | -0.016830 |
| M00_media_recente_5 | 660 | 0.567091 | 0.722596 | -0.001520 |

Diferença de MAE (selecionado menos baseline): -0.089002.

## Validação (média histórica disponível apenas nesta fase)

| modelo | n | mae | rmse | vies |
|---|---|---|---|---|
| M00_media_recente_5 | 1980 | 0.604116 | 0.760987 | -0.002110 |
| B01_media_historica_treino | 1980 | 0.514966 | 0.631618 | -0.006035 |

## Importância por permutação (holdout congelado)

| atributo | delta_mae_media | delta_mae_desvio |
|---|---|---|
| media_saldo_gols_5 | 0.015114 | 0.003581 |
| media_pontos_visitante_historico | 0.012377 | 0.001149 |
| media_pontos_10 | 0.005767 | 0.003437 |
| media_pontos_5 | 0.003908 | 0.002123 |
| media_pontos_mandante_historico | 0.003101 | 0.001694 |
| media_pontos_3 | 0.002065 | 0.001353 |
| media_saldo_gols_3 | 0.000693 | 0.001027 |
| media_saldo_gols_10 | 0.000286 | 0.000851 |
| desvio_pontos_5 | 0.000206 | 0.000530 |
| jogos_acumulados | 0.000021 | 0.000152 |
| dias_descanso | -0.000476 | 0.000335 |
| mando | -0.000501 | 0.000704 |

## Desempenho por equipe (sem ranking de mérito; n difere)

| equipe | n | mae | rmse | vies | cobertura_intervalo |
|---|---|---|---|---|---|
| Atlético Mineiro | 33 | 0.559856 | 0.652969 | -0.003409 | 0.878788 |
| Botafogo FR | 33 | 0.431599 | 0.529875 | -0.163696 | 0.939394 |
| CR Vasco da Gama | 33 | 0.595301 | 0.705922 | 0.161128 | 0.818182 |
| Ceará SC | 33 | 0.322355 | 0.427493 | 0.204639 | 0.969697 |
| Cruzeiro EC | 33 | 0.516571 | 0.611848 | -0.309902 | 0.909091 |
| EC Bahia | 33 | 0.490201 | 0.583974 | -0.206443 | 0.909091 |
| EC Juventude | 33 | 0.507319 | 0.583922 | 0.196890 | 0.939394 |
| EC Vitória | 33 | 0.411671 | 0.491674 | -0.024938 | 1.000000 |
| Flamengo | 33 | 0.426365 | 0.517218 | -0.297308 | 0.969697 |
| Fluminense FC | 33 | 0.422346 | 0.528903 | -0.200539 | 0.939394 |
| Fortaleza EC | 33 | 0.540346 | 0.665145 | 0.097660 | 0.848485 |
| Grêmio | 33 | 0.316031 | 0.385573 | 0.015230 | 0.969697 |
| Mirassol FC | 33 | 0.436863 | 0.549339 | -0.331876 | 0.909091 |
| RB Bragantino | 33 | 0.660770 | 0.814596 | 0.058379 | 0.818182 |
| SC Corinthians Paulista | 33 | 0.351905 | 0.430050 | 0.048010 | 0.969697 |
| SC Internacional | 33 | 0.455459 | 0.545158 | 0.159096 | 0.939394 |
| SC Recife | 33 | 0.625787 | 0.717115 | 0.518264 | 0.878788 |
| SE Palmeiras | 33 | 0.574232 | 0.679805 | -0.240088 | 0.878788 |
| Santos FC | 33 | 0.373808 | 0.453573 | 0.012852 | 0.939394 |
| São Paulo FC | 33 | 0.543000 | 0.727130 | -0.030549 | 0.818182 |

## Desempenho por temporada

| temporada | n | mae | rmse | vies | cobertura_intervalo |
|---|---|---|---|---|---|
| 2025 | 660 | 0.478089 | 0.590887 | -0.016830 | 0.912121 |

## Erros extremos (maiores erros absolutos)

| equipe | data_referencia | partida_id | alvo | previsao | residuo | dentro_intervalo |
|---|---|---|---|---|---|---|
| São Paulo FC | 2025-07-16 00:00:00 | 607b80433d87b813dd0c18361303ae368fb70eee63935bb0c712b400c275600b | 3.000000 | 1.132733 | -1.867267 | False |
| RB Bragantino | 2025-04-06 00:00:00 | cd3bfc4790d4d6a8b7f753e58b89709e10495daa46ad13d063991612486ba5ca | 3.000000 | 1.159666 | -1.840334 | False |
| CR Vasco da Gama | 2025-10-26 00:00:00 | 74ee03b0e94a09cb6a7832091e55db14f6d344a8ac6869c9e540fe85860a4cfe | 0.000000 | 1.618685 | 1.618685 | False |
| RB Bragantino | 2025-07-20 00:00:00 | 3fbb5a7bb0c509922e7ce537671aa58bbe020b9c536e423d34c324429f60863f | 0.000000 | 1.568983 | 1.568983 | False |
| RB Bragantino | 2025-07-16 00:00:00 | 607b80433d87b813dd0c18361303ae368fb70eee63935bb0c712b400c275600b | 0.000000 | 1.555009 | 1.555009 | False |
| São Paulo FC | 2025-07-12 00:00:00 | 0c6d98b8e997ad9efdb6b5fef14e6f967182e54fff0840d89b512362a22dbc84 | 2.600000 | 1.094404 | -1.505596 | False |
| Fortaleza EC | 2025-05-10 00:00:00 | 9cc049ae5a585cfcae45b0b973a24cfae295d918cbc73cd7c15e63693ad1499f | 0.000000 | 1.469553 | 1.469553 | False |
| SE Palmeiras | 2025-11-06 00:00:00 | bfd048b3cbf7d913344cca5410f547bdacfc0081bcf8dc0500340e9e5fb1ddf1 | 0.400000 | 1.857597 | 1.457597 | False |
| São Paulo FC | 2025-07-19 00:00:00 | 316210f20f50aa9c1cd0c5bc03ce5541e477fa3b99010c83cc7160ea13ce3d42 | 2.600000 | 1.143849 | -1.456151 | False |
| RB Bragantino | 2025-07-13 00:00:00 | 408f3dd1419efc659350a067cade9badc771fd7eb161ea0d16f8bd3de2fa6069 | 0.200000 | 1.618486 | 1.418486 | False |

## Hipóteses

- **H01** (observado_nesta_comparacao): Indicadores recentes de desempenho ajudam a prever a evolução futura das equipes. Holdout 2025: M01_ridge MAE 0.478089 (n=660) contra M00_media_recente_5 MAE 0.567091. Resultado observado, sem generalização.
- **H02** (desfavoravel_nesta_comparacao): Médias móveis apresentam maior capacidade preditiva que médias históricas isoladas. Validação: M00_media_recente_5 MAE 0.604116 contra B01_media_historica_treino MAE 0.514966. B01 é média histórica global do treino, não por clube.
- **H03** (nao_conclusiva): Diferenças entre desempenho como mandante e visitante contribuem para as previsões. media_pontos_visitante_historico: delta MAE +0.012377 (desvio 0.001149); media_pontos_mandante_historico: delta MAE +0.003101 (desvio 0.001694); mando: delta MAE -0.000501 (desvio 0.000704) Importância preditiva exploratória; não é estudo causal nem ablação.
- **H04** (nao_conclusiva): Volatilidade de resultados e saldo de gols ajudam a identificar mudanças de tendência. media_saldo_gols_5: delta MAE +0.015114 (desvio 0.003581); media_saldo_gols_3: delta MAE +0.000693 (desvio 0.001027); media_saldo_gols_10: delta MAE +0.000286 (desvio 0.000851); desvio_pontos_5: delta MAE +0.000206 (desvio 0.000530) Importância preditiva exploratória; não é estudo causal nem ablação.
- **H05** (favoravel_nesta_comparacao): Modelos de Machine Learning podem superar modelos estatísticos baseline. Holdout 2025: M01_ridge MAE 0.478089 (n=660) contra M00_media_recente_5 MAE 0.567091. Sem generalização para outras temporadas ou competições.
- **H06** (nao_avaliavel): Métricas avançadas, como xG, quando disponíveis, podem oferecer ganhos adicionais. xG não está disponível no dataset; valores ausentes não foram preenchidos com zeros.

## Limitações

- Avaliação em um único holdout temporal e uma única competição; amostra pequena por equipe.
- Alvos de partidas consecutivas se sobrepõem no tempo; as observações não são independentes.
- Não há intervalo estatístico, valor-p ou teste de significância para os erros.
- A importância por permutação é preditiva e exploratória: não é estudo causal nem ablação, e atributos correlacionados podem dividir a importância.
- Erros por equipe têm n diferente; diferenças de pontos não são ranking de mérito.
- xG não está disponível; H06 não é avaliável e nenhum valor foi preenchido com zero.
- Dados observacionais: resultados não são causais nem recomendações de apostas.
