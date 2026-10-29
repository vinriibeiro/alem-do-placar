# Dashboard Power BI local (T008)

O projeto Power BI é gerado por `src/evaluation/powerbi.py`, a partir de arquivos Parquet, JSON e CSV locais. O gerador não baixa dados, não publica nada e não executa a CLI da Microsoft.

**Status:** código e testes entregues. A validação visual e de importação no Power BI Desktop ainda será feita pelo controlador. Nenhum QA foi aprovado nesta escrita.

## Pré-requisitos

- Python 3.12 e ambiente com as dependências do `pyproject.toml` (`pyarrow` é usado para ler os schemas).
- Power BI Desktop instalado (somente para abrir e validar o `.pbip`).
- Um scaffold oficial criado com a ferramenta Microsoft `powerbi-report-author` 0.5.0, contendo `AlemDoPlacar.pbip`, `AlemDoPlacar.Report/` e o tema `StaticResources/SharedResources/BaseThemes/Fluent2-CY26SU10.json`. Esse scaffold é preparado pelo controlador; o gerador apenas o copia.

Instalação (PowerShell, com o ambiente virtual ativo):

```powershell
python -m pip install -e ".[test,lint]"
```

## Entradas

| Argumento | Conteúdo esperado |
|---|---|
| `pasta_processados` | `dim_equipes.parquet`, `dim_temporadas.parquet`, `fato_partidas.parquet`, `fato_desempenho_equipes.parquet`, `dataset_analitico.parquet` |
| `pasta_modelagem` | `previsoes.parquet`, `metricas.json` (lista de registros) e `metadados.json` (`modelo_selecionado`, `corte_treino`, `versao`, `notas`) |
| `pasta_cientifica` | `importancias.csv` (`atributo`, `delta_mae_media`, `delta_mae_desvio`, decimais com ponto) |
| `template_dir` | Scaffold oficial descrito acima |

As pastas de entrada são somente lidas.

## Geração

```python
from pathlib import Path

from evaluation.powerbi import gerar_projeto

pbip = gerar_projeto(
    pasta_saida=Path("dashboard/powerbi/gerado"),
    pasta_processados=Path("data/processed"),
    pasta_modelagem=Path("data/predictions"),
    pasta_cientifica=Path("reports/metrics"),
    template_dir=Path("dashboard/powerbi/template"),
)
print(pbip)
```

Regras:

- `pasta_saida` deve estar ausente ou vazia. Se contiver arquivos, a geração falha sem sobrescrever nada.
- Tipos complexos (listas, estruturas, mapas) nos Parquet são rejeitados.
- Erros de entrada (arquivo ausente, campo ausente, valor inválido) são `ErroProjeto` com a causa indicada.

## Conteúdo do projeto

- `AlemDoPlacar.SemanticModel/model.bim`: tabelas em TMSL, partições M (`Parquet.Document(File.Contents(...))` ou `Table.FromRecords` para `metricas` e `importancias`), 7 relacionamentos 1:N unidirecionais e medidas DAX.
- `AlemDoPlacar.Report/`: sete páginas (Visão Geral, Tendências, Estatística, Laboratório de Modelos, Previsões, Assistente e Metodologia) com identificadores determinísticos.
- Previsões são retrospectivas de 2025, com horizonte de 5 partidas. A página mostra modelo, corte e intervalo de 90%.
- A página Assistente indica o endereço local `http://127.0.0.1:8765`, que depende da API do T009.

## Validação no Power BI Desktop

1. Abrir `AlemDoPlacar.pbip` no Power BI Desktop.
2. Confirmar que a importação termina sem erros e que o modelo carrega as 8 tabelas.
3. Na visão de modelo, conferir os 7 relacionamentos. Se o Desktop acusar caminhos ambíguos (dimensões ligadas a `analitico`/`previsoes` e a `fato_desempenho_equipes`), desativar os relacionamentos de `analitico` e `previsoes` com as dimensões.
4. Conferir se os valores dos cards batem com os resultados de Python (partidas, gols, pontos e MAE de holdout).
5. Só então publicar. Publicação e autenticação na nuvem não fazem parte deste projeto.

## Versionamento

O gerador e o template são versionados. A pasta gerada depende de caminhos locais e pode ser recriada a qualquer momento. O cache local do Power BI Desktop (`.pbi/`) é ignorado pelo Git.
