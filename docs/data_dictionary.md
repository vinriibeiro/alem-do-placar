# Dicionário de dados — atributos temporais (T005)

Fonte de código: `src/features/temporais.py`. Entrada: base de partidas no formato de `evaluation.exploratoria.carregar_base` (T003/T004), derivada de OpenFootball CC0 para 2018–2025.

## 1. Chaves e granularidade

- Saída com **duas linhas por partida**: uma por equipe (`mando` = 1 para mandante, 0 para visitante).
- Chave lógica: `(partida_id, equipe)`.
- Chave de atributos: `(equipe, temporada)`. Todo cálculo é reiniciado em cada temporada.
- Ordenação: `data_referencia`, `partida_id`, `equipe`. O resultado não depende da ordem da entrada.

## 2. Campos de identificação e contexto

| Campo | Tipo | Unidade | Descrição |
|---|---|---|---|
| `partida_id` | texto/inteiro | — | Identificador da partida. Não é atributo. |
| `equipe` | texto | — | Nome padronizado da equipe. Não é atributo. |
| `adversario` | texto | — | Nome padronizado do adversário. Não é atributo. |
| `data_referencia` | datetime | data | Data da partida, tratada como o fim dela (ver seção 4). |
| `temporada` | inteiro | ano | Ano da temporada. Não é atributo. |
| `mando` | inteiro | 1/0 | 1 = mandante; 0 = visitante. Conhecido antes do jogo; é atributo. |
| `pontos` | inteiro | pontos | 3/1/0 pelo resultado da partida. **Não é atributo nem alvo:** serve só para janelas que incluem a partida atual. |
| `gols_pro` | inteiro | gols | Gols marcados pela equipe na partida. Não é atributo. |
| `gols_contra` | inteiro | gols | Gols sofridos pela equipe na partida. Não é atributo. |
| `saldo_gols` | inteiro | gols | `gols_pro - gols_contra`. Não é atributo. |
| `rodada` | inteiro | rodada | Presente somente se existir na entrada. Não é atributo. |

Pontos e gols são derivados dos placares. A coluna `resultado` da entrada não é usada.

## 3. Atributos (`FEATURES`)

Todos usam somente partidas com `data_referencia` até a data da partida atual, inclusive.

| Campo | Unidade | Cálculo | Dados ausentes (NaN) |
|---|---|---|---|
| `media_pontos_3` | pontos/jogo | média dos pontos nas últimas 3 partidas, incluindo a atual | menos de 3 jogos na temporada |
| `media_pontos_5` | pontos/jogo | idem, 5 partidas | menos de 5 jogos |
| `media_pontos_10` | pontos/jogo | idem, 10 partidas | menos de 10 jogos |
| `media_saldo_gols_3` | gols/jogo | média do saldo nas últimas 3 partidas | menos de 3 jogos |
| `media_saldo_gols_5` | gols/jogo | média do saldo nas últimas 5 partidas | menos de 5 jogos |
| `media_saldo_gols_10` | gols/jogo | média do saldo nas últimas 10 partidas | menos de 10 jogos |
| `desvio_pontos_5` | pontos | desvio-padrão amostral com ddof=0 dos pontos nas últimas 5 partidas (min_periods=1) | não há; 1 jogo resulta em 0,0 |
| `media_pontos_mandante_historico` | pontos/jogo | média dos pontos em todos os jogos como mandante até a data de referência | antes do primeiro jogo como mandante |
| `media_pontos_visitante_historico` | pontos/jogo | média dos pontos em todos os jogos como visitante até a data de referência | antes do primeiro jogo como visitante |
| `jogos_acumulados` | jogos | número de partidas da equipe na temporada até a data de referência, incluindo a atual | não há |
| `dias_descanso` | dias | diferença entre a data da partida e a da anterior da mesma equipe na temporada | primeira partida da temporada |
| `mando` | 1/0 | ver seção 2 | não há |

Não há imputação. Nenhum valor ausente é preenchido, nem por `bfill`. Modelos devem tratar os NaN explicitamente, por exemplo com imputação ajustada apenas no treino da validação temporal (T006).

## 4. Momento de referência

- `data_referencia` é a data da partida, tratada como o instante em que o resultado já é conhecido.
- Atributos da partida atual podem usar o próprio resultado, porque ele é conhecido ao término do jogo.
- Nenhum atributo usa partidas posteriores à data de referência.
- Ponto de corte de treino e teste: ao separar dados no backtesting, usar `fim_alvo` para purgar observações cujo horizonte ultrapassa a fronteira.

## 5. Alvo

| Campo | Tipo | Unidade | Definição |
|---|---|---|---|
| `media_pontos_futuros_5` | float | pontos/jogo | Média dos pontos das **5 partidas seguintes** da mesma equipe e temporada. Exclui a partida atual. |
| `fim_alvo` | datetime | data | `data_referencia` da 5ª partida seguinte. Marca o fim do horizonte para purga no backtesting. |

- Horizonte incompleto: as últimas 5 partidas de cada equipe e temporada têm `media_pontos_futuros_5` = NaN e `fim_alvo` = NaT. Nunca há média parcial nem preenchimento com zeros.
- O horizonte não atravessa a temporada: partidas de outra temporada não entram no alvo.
- Unidade do alvo: pontos por partida, na escala 0 a 3.

## 6. Cold start

- Primeiras partidas de cada equipe e temporada: janelas de 3, 5 e 10 jogos ficam NaN até completarem a janela.
- Primeira partida da temporada: `dias_descanso` é NaN, mesmo quando houve jogo na temporada anterior.
- Primeiro jogo em cada mando: o histórico correspondente é NaN.
- Desvio-padrão: com um único jogo, vale 0,0.
- Janelas de média não usam sub-janelas parciais: evitam rotular uma média de 2 jogos como média de 3.

## 7. Dados ausentes e validação de entrada

A função rejeita (`ValueError`) a base quando:

- ela está vazia ou falta alguma coluna obrigatória;
- há `partida_id` ausente ou duplicado;
- há data ausente ou inválida;
- há nome de equipe ausente ou vazio;
- mandante e visitante são iguais;
- há placar ausente, não inteiro ou negativo;
- a temporada é ausente, não inteira ou menor que 1.

## 8. Exportação

`exportar_dataset(dataset, caminho)` grava Parquet sem índice (`index=False`), via PyArrow, e cria o diretório pai se necessário. Outros formatos são recusados.

## 9. Limitações

- **Força do adversário não incluída.** O atributo opcional foi omitido. Não há fonte de força confiável e auditada no projeto; calculá-la sem vazamento exigiria ratings construídos só com jogos anteriores.
- **Dados de 2026 ausentes.** A temporada 2026 é reservada para avaliação final (PRD 2.2) e não é processada aqui.
- **Cobertura temporal.** As temporadas válidas dependem da base T003/T004, hoje 2018–2025.
- **Sem variáveis de estatísticas avançadas** (finalizações, xG, posse). Não há cobertura validada nas fontes aprovadas.
- **Correlação, não causalidade.** Os atributos são preditivos, não explicam causas de desempenho.
- **Partidas sem dados de posição.** Posição histórica na tabela e rodada atual não são calculadas.

## 10. Execução

Dependências já declaradas em `pyproject.toml` (pandas, numpy via pandas, PyArrow, Pytest). Comandos (não executados nesta entrega):

```powershell
python -m pip install -e ".[test,lint]"
python -B -m pytest tests/unit/test_features_temporais.py
```
