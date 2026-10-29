# Dashboard Power BI (T008)

O projeto Power BI é gerado por `src/evaluation/powerbi.py` (modelo semântico) e `src/evaluation/powerbi_layout.py` (tema, cabeçalho, navegação e páginas), a partir de arquivos Parquet, JSON e CSV. O gerador não baixa dados, não publica nada e não executa a CLI da Microsoft.

**Status:** código, testes e redesign entregues. A validação visual e de importação no Power BI Desktop ainda precisa ser feita por você, com o roteiro em `docs/qa/T008/checklist_desktop.md`. Nenhum QA foi aprovado.

## Pré-requisitos

- Python 3.12 com as dependências do `pyproject.toml`.
- Power BI Desktop, apenas para abrir e validar o `.pbip`.
- O scaffold oficial em `dashboard/powerbi/template` (versionado), criado com a ferramenta Microsoft `powerbi-report-author` 0.5.0. O gerador apenas o copia.

## Gerar o projeto

```powershell
.\.venv\Scripts\python.exe scripts\gerar_powerbi.py
```

O script recria `dashboard/powerbi/AlemDoPlacar`. Ele só apaga a pasta se ela já contiver `AlemDoPlacar.pbip`.

Opções:

| Opção | Efeito |
|---|---|
| `--fonte local` (padrão) | Partições `File.Contents` com o caminho absoluto desta máquina. Não acessa rede. |
| `--fonte web --url-base https://raw.githubusercontent.com/USUARIO/REPO/main/data` | Partições `Web.Contents`. Permite atualizar o relatório publicado sem gateway. |
| `--url-assistente https://SEU-SITE/assistente` | Endereço do botão da página Assistente. O padrão `https://ALTERAR` é um marcador visível. |

Os tokens de cor vêm de `dashboard/assets/tema_tokens.json`, gerado pelo site (`python scripts/gerar_og.py`). Assim o relatório e o site compartilham a identidade visual.

## Entradas

| Argumento | Conteúdo esperado |
|---|---|
| `pasta_processados` | `dim_equipes`, `dim_temporadas`, `fato_partidas`, `fato_desempenho_equipes` e `dataset_analitico` em Parquet |
| `pasta_modelagem` | `previsoes.parquet`, `metricas.json` e `metadados.json` (`modelo_selecionado`, `corte_treino`, `versao`; opcionais `notas`, `cobertura_holdout`) |
| `pasta_cientifica` | `importancias.csv` |
| `template_dir` | Scaffold oficial |

As pastas de entrada são somente lidas. A saída deve estar ausente ou vazia.

## Layout (canvas 1280 x 720)

Todas as páginas seguem a mesma estrutura:

| Faixa | Posição | Conteúdo |
|---|---|---|
| Cabeçalho | y 0–64 | Título e subtítulo da página, fundo azul-marinho |
| Navegação | y 68–104 | Navegador de páginas nativo do Power BI |
| Conteúdo | y 112–692 | Margens de 16 px, espaçamento de 12 px |
| Rodapé | y 698–718 | Fonte, modelo, versão e corte de treino |

Páginas:

1. **Visão Geral:** 5 indicadores, segmentações de temporada e equipe, gols por jogo por temporada, pontos por equipe e classificação.
2. **Tendências:** média móvel de 3, 5 e 10 jogos, média recente por equipe e matriz de aproveitamento equipe x temporada.
3. **Estatística:** distribuição de resultados, mandante x visitante, dispersão saldo de gols x pontos e volatilidade.
4. **Laboratório de Modelos:** MAE do modelo e do baseline, MAE e RMSE por modelo, métricas e importância por permutação.
5. **Previsões:** previsto, observado e intervalo de 90% por equipe, com aviso de que são previsões retrospectivas.
6. **Assistente:** botão que abre o site do assistente e exemplos de perguntas.
7. **Metodologia:** dados, modelo, leitura das previsões e limitações.

## Medidas DAX

Ficam na tabela `fato_desempenho_equipes`, com formato definido.

| Medida | Definição resumida |
|---|---|
| Partidas, Temporadas | Contagens distintas de partida e de ano |
| Gols, Gols sofridos, Saldo de gols, Pontos totais | Somas das colunas do fato |
| Vitórias, Empates, Derrotas | Contagem por pontos 3, 1 e 0 |
| Gols por jogo, Gols sofridos por jogo, Pontos por jogo | Divisões seguras por partidas ou observações |
| Aproveitamento | Pontos dividido por 3 vezes as observações |
| Vitórias do mandante | Vitórias como mandante dividido por jogos como mandante |
| Volatilidade de pontos | `STDEV.P` dos pontos por jogo |
| Posição | `RANKX` por pontos, dentro do filtro de temporada |
| Média prevista, Média observada, Limite inferior, Limite superior, Erro absoluto médio | Sobre a tabela `previsoes` |
| Média 3 jogos, Média recente, Média 10 jogos | Médias móveis do dataset analítico |
| MAE e RMSE de validação e de holdout, MAE global selecionado e baseline | Sobre `metricas`, sempre com temporada `todas` |
| Cobertura do intervalo | Constante do `metadados.json`, quando informada (não usada nas páginas) |

Posição só tem valor quando há uma equipe no contexto. Vitórias do mandante responde ao filtro de equipe e de temporada.

## O que foi verificado e o que não foi

Verificado por testes automatizados: sete páginas, cabeçalho, navegação e rodapé em todas, nenhum visual fora do canvas ou sobreposto, referências a tabelas, colunas e medidas existentes, tema registrado, URLs do botão e partições web.

**Não verificado:** a abertura no Power BI Desktop. Os visuais pageNavigator, pivotTable, scatterChart, o hiperlink da caixa de texto e o formato do tema são os mais recentes e os primeiros a conferir. Se algum falhar, a causa estará em `powerbi_layout.py`.

## Validação no Power BI Desktop

Siga `docs/qa/T008/checklist_desktop.md`. Se o Desktop acusar caminhos ambíguos entre dimensões e `analitico`/`previsoes`, desative os relacionamentos dessas duas tabelas com as dimensões.

## Publicação

1. Gere em modo web com a URL do repositório público e do site.
2. Abra no Desktop, confira e publique em um workspace.
3. No Serviço: Arquivo, Inserir relatório, Publicar na web (público). Copie o endereço do iframe para `POWERBI_EMBED_URL` do site.

Publicação e autenticação na nuvem não fazem parte do código.

## Versionamento

O gerador, o template e o projeto gerado são versionados. O cache local do Desktop (`.pbi/`) é ignorado.
