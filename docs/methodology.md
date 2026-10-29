# Metodologia — Análise exploratória (T004)

**Escopo:** descrição estatística das tabelas Parquet geradas pela T003 (PRD seções 5.1 e 5.2).
**Implementação:** `src/evaluation/exploratoria.py`, notebook `notebooks/01_exploratoria.ipynb`.

## 1. Entrada

- `dim_equipes`, `dim_temporadas`, `fato_partidas` e `fato_desempenho_equipes` em `data/processed`.
- `carregar_base` monta uma linha por partida com colunas `partida_id`, `data_partida`, `temporada`, `competicao`, `equipe_mandante`, `equipe_visitante`, `gols_mandante`, `gols_visitante`, `resultado` (H/D/A), `rodada` e os IDs correspondentes.
- A rodada vem da observação de desempenho do mandante. Partidas sem essa observação recebem `rodada` nulo, contado em `qualidade.rodadas_ausentes`.

## 2. Joins e validação

- Chaves primárias (`equipe_id`, `temporada_id`, `partida_id`) devem ser únicas; caso contrário, há erro.
- Os joins usam `validate="many_to_one"` (e `one_to_one` para a rodada). Chave sem correspondência gera erro, não valor nulo silencioso.
- `resultado` deve ser coerente com os gols; gols ausentes geram erro.
- Base vazia é rejeitada com a mensagem `base vazia`.

## 3. Período

- Período candidato do PRD 2.2: 2015–2025.
- Período real validado: **2018–2025** (3.040 partidas, 380 por temporada, 20 clubes por temporada).
- A temporada **2026 é reservada** para avaliação temporal final. O código a rejeita e não a processa.
- Dados sintéticos existem apenas nos testes (`tests/unit/test_exploratoria.py`) e nunca são apresentados como dados reais.

## 4. Estatísticas produzidas (`resumo_exploratorio`)

- Número de partidas, equipes e temporadas (lista ordenada).
- Médias de gols (mandante, visitante e total) e distribuição H/D/A com quantidades e proporções.
- Agregados por temporada (partidas, gols totais, média de gols, H/D/A).
- Agregados por mando de campo, por equipe e por equipe e temporada: jogos, vitórias, empates, derrotas, gols pró e contra, saldo e pontos.
- Pontos seguem a regra 3/1/0 (PRD 5.2).
- Indicadores de qualidade: partidas duplicadas, confrontos repetidos na mesma data, datas e rodadas ausentes, mandante igual ao visitante e placares extremos (total de gols de 7 ou mais, limiar exploratório).

Anomalias são **apenas listadas**. Nenhum registro é removido automaticamente.

## 5. Saídas (`exportar_analise`)

- `resumo.json`: JSON com ordenação estável e sem data de geração, portanto reproduzível.
- `gols_por_temporada.png`: média de gols por partida por temporada.
- `distribuicao_resultados.png`: quantidades e proporções H/D/A.
- `pontos_por_equipe.png`: pontos acumulados no período.
- Os gráficos usam o backend Agg (sem interface gráfica) e as figuras são liberadas após a gravação.

## 6. Hipóteses do PRD (planos de investigação)

Estas hipóteses são planos. **Nenhuma está confirmada nesta etapa.** Os testes de hipótese dependem de modelagem (T005 a T007).

- **H01** — indicadores recentes ajudam a prever a evolução futura. Plano: comparar médias móveis de pontos com o desempenho seguinte (T005/T006).
- **H02** — médias móveis superam médias históricas isoladas. Plano: comparação de erro de previsão em backtesting temporal (T006).
- **H03** — desempenho como mandante e visitante melhora previsões. Plano: a análise exploratória descreve pontos por mando (`por_mando`); o ganho preditivo só será avaliado em T006.
- **H04** — volatilidade e saldo de gols ajudam a identificar mudanças de tendência. Plano: calcular volatilidade em T005 e testá-la em backtesting (T006/T007).
- **H05** — modelos de ML superam baselines estatísticos. Plano: comparação com M00 em dados de teste temporais (T006).

## 7. Limites

- Descrição estatística **não é causalidade**. Diferenças entre equipes, temporadas ou mando não são efeitos comprovados.
- Nenhuma conclusão sobre as hipóteses é tirada desta etapa.
- A fonte OpenFootball (CC0) foi auditada na etapa T002 (`docs/sources_audit.md`). As outras fontes candidatas não foram aprovadas e não são usadas.
- Ausências e anomalias são reportadas, não preenchidas.

## 8. Reprodução

```powershell
python -m pip install -e ".[test,lint]"
python -B -m pytest tests/unit/test_exploratoria.py
```

O notebook `notebooks/01_exploratoria.ipynb` chama as mesmas funções. Os outputs são produzidos ao executar o notebook sobre `data/processed`.
