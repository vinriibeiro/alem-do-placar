# Dicionário de dados

Gerado por `scripts/gerar_dicionario.py` a partir de `src/evaluation/nomes.py`, dos esquemas Parquet e das medidas do gerador do Power BI. Para regras de cálculo detalhadas dos atributos, veja também `docs/data_dictionary.md`.

## 1. Tabelas de dados

### dim_equipes

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `equipe_id` | Identificador da equipe | int64 | Hash estável do nome padronizado. | — | OpenFootball (CC0), padronizado em src/processing |
| `nome` | Nome | string | Nome da equipe após a padronização. | — | OpenFootball (CC0), padronizado em src/processing |
| `nome_padronizado` | Equipe | string | Nome único do clube usado em todo o projeto. | — | OpenFootball (CC0), padronizado em src/processing |

### dim_temporadas

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `temporada_id` | Identificador da temporada | int64 | Hash estável do ano e da competição. | — | OpenFootball (CC0), padronizado em src/processing |
| `ano` | Temporada | int64 | Ano da temporada. | — | OpenFootball (CC0), padronizado em src/processing |
| `competicao` | Competição | string | Brasileiro Série A. | — | OpenFootball (CC0), padronizado em src/processing |

### fato_partidas

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `partida_id` | Identificador da partida | string | SHA-256 de temporada, data, mandante e visitante. | — | OpenFootball (CC0), padronizado em src/processing |
| `data_partida` | Data | date32[day] | Data da partida. | — | OpenFootball (CC0), padronizado em src/processing |
| `temporada_id` | Temporada | int64 | Chave para dim_temporadas. | — | OpenFootball (CC0), padronizado em src/processing |
| `equipe_mandante_id` | Mandante | int64 | Chave da equipe que jogou em casa. | — | OpenFootball (CC0), padronizado em src/processing |
| `equipe_visitante_id` | Visitante | int64 | Chave da equipe visitante. | — | OpenFootball (CC0), padronizado em src/processing |
| `gols_mandante` | Gols do mandante | int64 | Placar final do mandante. | — | OpenFootball (CC0), padronizado em src/processing |
| `gols_visitante` | Gols do visitante | int64 | Placar final do visitante. | — | OpenFootball (CC0), padronizado em src/processing |
| `resultado` | Resultado | string | H (mandante venceu), D (empate) ou A (visitante venceu). | — | OpenFootball (CC0), padronizado em src/processing |

### fato_desempenho_equipes

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `partida_id` | Identificador da partida | string | Chave para fato_partidas. | — | OpenFootball (CC0), padronizado em src/processing |
| `equipe_id` | Equipe | int64 | Chave para dim_equipes. | — | OpenFootball (CC0), padronizado em src/processing |
| `pontos` | Pontos no jogo | int64 | 3 vitória, 1 empate, 0 derrota. | — | OpenFootball (CC0), padronizado em src/processing |
| `gols_pro` | Gols marcados | int64 | Gols da equipe na partida. | — | OpenFootball (CC0), padronizado em src/processing |
| `gols_contra` | Gols sofridos | int64 | Gols do adversário na partida. | — | OpenFootball (CC0), padronizado em src/processing |
| `saldo_gols` | Saldo de gols | int64 | gols_pro − gols_contra. | — | OpenFootball (CC0), padronizado em src/processing |
| `mando_campo` | Mando | string | mandante ou visitante. | — | OpenFootball (CC0), padronizado em src/processing |
| `rodada` | Rodada | int64 | Rodada da partida na temporada. | — | OpenFootball (CC0), padronizado em src/processing |

## 2. Atributos do modelo

Todos calculados por equipe e temporada, em ordem cronológica, incluindo o jogo de referência.

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `media_pontos_3` | Média de pontos nos últimos 3 jogos | decimal | Média dos pontos (3, 1 ou 0) da equipe nos 3 jogos mais recentes da temporada, incluindo o jogo de referência. | Média dos pontos (3, 1 ou 0) da equipe nos 3 jogos mais recentes da temporada, incluindo o jogo de referência. | src/features/temporais.py |
| `media_pontos_5` | Média de pontos nos últimos 5 jogos | decimal | Média dos pontos da equipe nos 5 jogos mais recentes da temporada. Também é o modelo de referência. | Média dos pontos da equipe nos 5 jogos mais recentes da temporada. Também é o modelo de referência. | src/features/temporais.py |
| `media_pontos_10` | Média de pontos nos últimos 10 jogos | decimal | Média dos pontos da equipe nos 10 jogos mais recentes da temporada. | Média dos pontos da equipe nos 10 jogos mais recentes da temporada. | src/features/temporais.py |
| `media_saldo_gols_3` | Saldo médio de gols nos últimos 3 jogos | decimal | Média de (gols marcados − gols sofridos) nos 3 jogos mais recentes da temporada. | Média de (gols marcados − gols sofridos) nos 3 jogos mais recentes da temporada. | src/features/temporais.py |
| `media_saldo_gols_5` | Saldo médio de gols nos últimos 5 jogos | decimal | Média de (gols marcados − gols sofridos) nos 5 jogos mais recentes da temporada. | Média de (gols marcados − gols sofridos) nos 5 jogos mais recentes da temporada. | src/features/temporais.py |
| `media_saldo_gols_10` | Saldo médio de gols nos últimos 10 jogos | decimal | Média de (gols marcados − gols sofridos) nos 10 jogos mais recentes da temporada. | Média de (gols marcados − gols sofridos) nos 10 jogos mais recentes da temporada. | src/features/temporais.py |
| `desvio_pontos_5` | Oscilação dos pontos nos últimos 5 jogos | decimal | Desvio-padrão dos pontos nos 5 jogos mais recentes: quanto maior, mais irregular a equipe. | Desvio-padrão dos pontos nos 5 jogos mais recentes | src/features/temporais.py |
| `media_pontos_mandante_historico` | Média de pontos como mandante na temporada | decimal | Média dos pontos da equipe nos jogos em casa da temporada, até o jogo de referência. | Média dos pontos da equipe nos jogos em casa da temporada, até o jogo de referência. | src/features/temporais.py |
| `media_pontos_visitante_historico` | Média de pontos como visitante na temporada | decimal | Média dos pontos da equipe nos jogos fora de casa da temporada, até o jogo de referência. | Média dos pontos da equipe nos jogos fora de casa da temporada, até o jogo de referência. | src/features/temporais.py |
| `jogos_acumulados` | Jogos disputados na temporada | inteiro | Quantidade de jogos da equipe na temporada até o jogo de referência. | Quantidade de jogos da equipe na temporada até o jogo de referência. | src/features/temporais.py |
| `dias_descanso` | Dias de descanso | decimal | Dias entre o jogo de referência e o jogo anterior da equipe na mesma temporada. | Dias entre o jogo de referência e o jogo anterior da equipe na mesma temporada. | src/features/temporais.py |
| `mando` | Jogou em casa | inteiro | 1 quando a equipe foi mandante no jogo de referência; 0 quando foi visitante. | 1 quando a equipe foi mandante no jogo de referência; 0 quando foi visitante. | src/features/temporais.py |

## 3. Alvo

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `media_pontos_futuros_5` | Média de pontos nos próximos 5 jogos | decimal (0 a 3) | Soma dos pontos da equipe nos 5 jogos seguintes da mesma temporada, dividida por 5. | soma dos pontos dos 5 jogos seguintes ÷ 5 | src/features/temporais.py |

## 4. Indicadores do dashboard (medidas DAX)

Nomes exibidos no relatório entre parênteses quando diferentes.

| Nome original | Nome amigável | Formato | Descrição | Fórmula DAX | Origem |
|---|---|---|---|---|---|
| `Partidas` | Partidas | #,0 | Quantidade de partidas distintas no filtro. | `DISTINCTCOUNT(fato_desempenho_equipes[partida_id])` | src/evaluation/powerbi.py |
| `Temporadas` | Temporadas | 0 |  | `DISTINCTCOUNT(dim_temporadas[ano])` | src/evaluation/powerbi.py |
| `Observações de equipe` | Observações de equipe | #,0 |  | `COUNTROWS(fato_desempenho_equipes)` | src/evaluation/powerbi.py |
| `Gols` | Gols | #,0 |  | `SUM(fato_desempenho_equipes[gols_pro])` | src/evaluation/powerbi.py |
| `Gols sofridos` | Gols sofridos | #,0 |  | `SUM(fato_desempenho_equipes[gols_contra])` | src/evaluation/powerbi.py |
| `Saldo de gols` | Saldo de gols | +#,0;-#,0;0 |  | `SUM(fato_desempenho_equipes[saldo_gols])` | src/evaluation/powerbi.py |
| `Pontos totais` | Pontos totais | #,0 | Soma dos pontos das equipes no filtro. | `SUM(fato_desempenho_equipes[pontos])` | src/evaluation/powerbi.py |
| `Vitórias` | Vitórias | #,0 |  | `CALCULATE(COUNTROWS(fato_desempenho_equipes),fato_desempenho_equipes[pontos]=3)` | src/evaluation/powerbi.py |
| `Empates` | Empates | #,0 |  | `CALCULATE(COUNTROWS(fato_desempenho_equipes),fato_desempenho_equipes[pontos]=1)` | src/evaluation/powerbi.py |
| `Derrotas` | Derrotas | #,0 |  | `CALCULATE(COUNTROWS(fato_desempenho_equipes),fato_desempenho_equipes[pontos]=0)` | src/evaluation/powerbi.py |
| `Gols por jogo` | Gols marcados/jogo | 0.00 |  | `DIVIDE([Gols],[Partidas])` | src/evaluation/powerbi.py |
| `Gols sofridos por jogo` | Gols sofridos/jogo | 0.00 |  | `DIVIDE([Gols sofridos],[Observações de equipe])` | src/evaluation/powerbi.py |
| `Pontos por jogo` | Pontos por jogo | 0.00 | Pontos ÷ jogos disputados. | `DIVIDE([Pontos totais],[Observações de equipe])` | src/evaluation/powerbi.py |
| `Aproveitamento` | Aproveitamento | 0.0% | Pontos ÷ (3 × jogos). | `DIVIDE([Pontos totais],3*[Observações de equipe])` | src/evaluation/powerbi.py |
| `Vitórias do mandante` | Vitórias do mandante | 0.0% | Vitórias em casa ÷ jogos em casa. | `DIVIDE(CALCULATE(COUNTROWS(fato_desempenho_equipes),fato_desempenho_equipes[mando_campo]="mandante",fato_desempenho_equipes[pontos]=3),CALCULATE(COUNTROWS(fato_desempenho_equipes),fato_desempenho_equipes[mando_campo]="mandante"))` | src/evaluation/powerbi.py |
| `Volatilidade de pontos` | Oscilação | 0.00 | Desvio-padrão populacional dos pontos por jogo. | `STDEV.P(fato_desempenho_equipes[pontos])` | src/evaluation/powerbi.py |
| `Média prevista` | Previsto | 0.00 | Média das previsões do modelo no filtro. | `AVERAGE(previsoes[previsao])` | src/evaluation/powerbi.py |
| `Média observada` | Real | 0.00 | Média do alvo real nas mesmas datas das previsões. | `AVERAGE(previsoes[alvo])` | src/evaluation/powerbi.py |
| `Limite inferior` | Limite inferior (90%) | 0.00 |  | `AVERAGE(previsoes[limite_inferior])` | src/evaluation/powerbi.py |
| `Limite superior` | Limite superior (90%) | 0.00 |  | `AVERAGE(previsoes[limite_superior])` | src/evaluation/powerbi.py |
| `Erro absoluto médio` | Erro absoluto médio | 0.000 | Média de \|previsto − real\| no filtro. | `AVERAGEX(previsoes,ABS(previsoes[previsao]-previsoes[alvo]))` | src/evaluation/powerbi.py |
| `Média 3 jogos` | Média 3 jogos | 0.00 |  | `AVERAGE(analitico[media_pontos_3])` | src/evaluation/powerbi.py |
| `Média recente` | Últimos 5 jogos | 0.00 |  | `AVERAGE(analitico[media_pontos_5])` | src/evaluation/powerbi.py |
| `Média 10 jogos` | Últimos 10 jogos | 0.00 |  | `AVERAGE(analitico[media_pontos_10])` | src/evaluation/powerbi.py |
| `Importância` | Aumento do erro | 0.0000 | Aumento médio do MAE ao embaralhar a variável no teste (permutação). | `AVERAGE(importancias[delta_mae_media])` | src/evaluation/powerbi.py |
| `MAE global selecionado` | MAE global selecionado | 0.000 | MAE do modelo selecionado no teste de 2025, todas as equipes. | `VAR ModeloAtual = [Modelo selecionado] RETURN CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",metricas[modelo]=ModeloAtual,metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `MAE global baseline` | MAE global baseline | 0.000 | MAE da média dos últimos 5 jogos no teste de 2025. | `CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",metricas[modelo]="M00_media_recente_5",metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `MAE validação` | MAE validação | 0.000 |  | `CALCULATE(MAX(metricas[mae]),metricas[fase]="validacao",metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `MAE holdout` | MAE holdout | 0.000 |  | `CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `RMSE validação` | RMSE validação | 0.000 |  | `CALCULATE(MAX(metricas[rmse]),metricas[fase]="validacao",metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `RMSE holdout` | RMSE holdout | 0.000 |  | `CALCULATE(MAX(metricas[rmse]),metricas[fase]="holdout",metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `RMSE global selecionado` | RMSE global selecionado | 0.000 |  | `VAR ModeloAtual = [Modelo selecionado] RETURN CALCULATE(MAX(metricas[rmse]),metricas[fase]="holdout",metricas[modelo]=ModeloAtual,metricas[temporada]="todas")` | src/evaluation/powerbi.py |
| `Jogos (temporada)` | J | 0 |  | `IF(HASONEVALUE(dim_temporadas[ano]),[Observações de equipe])` | src/evaluation/powerbi.py |
| `Pontos (temporada)` | P | 0 | Pontos, só quando há uma única temporada no filtro. | `IF(HASONEVALUE(dim_temporadas[ano]),[Pontos totais])` | src/evaluation/powerbi.py |
| `Vitórias (temporada)` | V | 0 |  | `IF(HASONEVALUE(dim_temporadas[ano]),COALESCE([Vitórias],0))` | src/evaluation/powerbi.py |
| `Empates (temporada)` | E | 0 |  | `IF(HASONEVALUE(dim_temporadas[ano]),COALESCE([Empates],0))` | src/evaluation/powerbi.py |
| `Derrotas (temporada)` | D | 0 |  | `IF(HASONEVALUE(dim_temporadas[ano]),COALESCE([Derrotas],0))` | src/evaluation/powerbi.py |
| `Saldo (temporada)` | SG | +0;-0;0 |  | `IF(HASONEVALUE(dim_temporadas[ano]),[Saldo de gols])` | src/evaluation/powerbi.py |
| `Aproveitamento (temporada)` | Aprov. | 0.0% |  | `IF(HASONEVALUE(dim_temporadas[ano]),[Aproveitamento])` | src/evaluation/powerbi.py |
| `Posição` | Pos. | 0 | Posição na temporada: pontos, vitórias, saldo e gols marcados; vazio sem uma única temporada. | `IF(HASONEVALUE(dim_temporadas[ano]) && ISINSCOPE(dim_equipes[nome_padronizado]) && [Observações de equipe] > 0, RANKX(FILTER(ALL(dim_equipes[nome_padronizado]), [Observações de equipe] > 0), COALESCE([Pontos totais],0)*100000000 + COALESCE([Vitórias],0)*1000000 + (COALESCE([Saldo de gols],0)+500)*1000 + COALESCE([Gols],0),, DESC, Skip))` | src/evaluation/powerbi.py |
| `Zona` | Zona | texto | Faixa da tabela pela posição (1–4, 5–6, 7–12, 17–20). | `VAR p = [Posição] RETURN SWITCH(TRUE(), ISBLANK(p), BLANK(), p <= 4, "Libertadores", p <= 6, "Pré-Libertadores", p <= 12, "Sul-Americana", p >= 17, "Rebaixamento", "")` | src/evaluation/powerbi.py |
| `Aviso temporada` | Aviso temporada | texto |  | `IF(HASONEVALUE(dim_temporadas[ano]), "Temporada " & FORMAT(SELECTEDVALUE(dim_temporadas[ano]), "0") & " · zona pela posição; vagas extras de copas não consideradas", "Selecione uma única temporada para ver a classificação")` | src/evaluation/powerbi.py |
| `Média do campeonato` | Média do campeonato | 0.00 | Pontos por jogo de todas as equipes no filtro de temporada. | `CALCULATE([Pontos por jogo],ALL(dim_equipes))` | src/evaluation/powerbi.py |
| `% dos resultados` | % dos resultados | 0.0% | Participação de cada resultado (Derrota, Empate, Vitória) no total. | `DIVIDE([Observações de equipe],CALCULATE([Observações de equipe],ALL(fato_desempenho_equipes[resultado_equipe])))` | src/evaluation/powerbi.py |
| `Modelos avaliados` | Modelos avaliados | 0 |  | `COUNTROWS(comparacao_modelos)` | src/evaluation/powerbi.py |
| `MAE do modelo` | Erro médio absoluto (MAE) | 0.000 |  | `AVERAGE(comparacao_modelos[mae_validacao])` | src/evaluation/powerbi.py |
| `RMSE do modelo` | RMSE | 0.000 |  | `AVERAGE(comparacao_modelos[rmse_validacao])` | src/evaluation/powerbi.py |

## 5. Métricas de avaliação

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `mae` | Erro médio absoluto (MAE) | decimal | Em média, quantos pontos por jogo a previsão erra, para mais ou para menos. | média de \|previsto − real\| | src/models/backtesting.py |
| `rmse` | Raiz do erro quadrático médio (RMSE) | decimal | Parecido com o MAE, mas pesa mais os erros grandes. | raiz da média de (previsto − real)² | src/models/backtesting.py |
| `vies` | Viés | decimal | Média de (previsto − real): positivo indica previsões otimistas; negativo, pessimistas. | média de (previsto − real) | src/models/backtesting.py |

## 6. Destaques individuais (`config/destaques.csv`)

| Nome original | Nome amigável | Tipo | Descrição | Fórmula | Origem |
|---|---|---|---|---|---|
| `categoria` | Destaque | texto | artilheiro, craque (Prêmio Brasileirão) ou goleiro (Prêmio Brasileirão). | — | Wikipédia (pt), caixa de informações da temporada |
| `gols` | Gols | inteiro | Gols do artilheiro na temporada. | — | Wikipédia (pt) |
| `foto_url` | Foto | URL | Imagem principal do artigo do jogador, só com licença livre. | — | Wikimedia Commons |
| `foto_licenca`, `foto_autor` | Crédito | texto | Licença e autor da foto, exibidos no crédito. | — | Wikimedia Commons |
