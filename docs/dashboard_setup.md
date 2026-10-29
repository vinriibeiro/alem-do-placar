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
| `--url-central https://...` e `--url-repositorio https://...` | Links reais da Central e do GitHub. Sem eles, as páginas mostram que o link estará disponível após a publicação. |

Os tokens de cor vêm de `dashboard/assets/tema_tokens.json`, gerado pelo site (`python scripts/gerar_og.py`). Assim o relatório e o site compartilham a identidade visual.

## Entradas

| Argumento | Conteúdo esperado |
|---|---|
| `pasta_processados` | `dim_equipes`, `dim_temporadas`, `fato_partidas`, `fato_desempenho_equipes` e `dataset_analitico` em Parquet |
| `pasta_modelagem` | `previsoes.parquet`, `metricas.json` e `metadados.json` (`modelo_selecionado`, `corte_treino`, `versao`; opcionais `notas`, `cobertura_holdout`) |
| `pasta_cientifica` | `importancias.csv` |
| `template_dir` | Scaffold oficial |

As pastas de entrada são somente lidas. A saída deve estar ausente ou vazia.

## Escudos dos clubes

`config/escudos.csv` liga cada equipe à imagem principal do artigo do clube na Wikipédia em português (miniatura PNG hospedada pela Wikimedia). O gerador junta essa URL à dimensão de equipes no Power Query, com categoria de dado `ImageUrl`, e as tabelas da Visão Geral e da Estatística mostram o escudo ao lado do nome.

- Para atualizar ou incluir um clube: edite o dicionário em `scripts/obter_escudos.py` e rode `python scripts/obter_escudos.py`. Confira as imagens antes de commitar.
- Os escudos são marcas registradas dos clubes. O projeto só aponta para as imagens da Wikimedia, para identificação visual e sem fins comerciais; nenhum arquivo de escudo é redistribuído no repositório.
- O Power BI busca as imagens na internet. Sem conexão, a coluna aparece vazia e o restante funciona.

## Layout (canvas 1280 x 720)

| Faixa | Posição | Conteúdo |
|---|---|---|
| Cabeçalho | y 0–72 | Faixa única verde-escura com título, marca e subtítulo, sem borda |
| Filete | y 72–76 | Linha amarela |
| Navegação | y 82–114 | Navegador de páginas nativo do Power BI |
| Conteúdo | y 122–688 | Margens de 16 px, espaçamento de 12 px |
| Rodapé | y 694–718 | Fonte, temporadas, data da última partida e modelo |

Páginas:

1. **Visão Geral:** classificação da temporada (escudo, posição, P, J, V, E, D, SG, aproveitamento e zona), aviso de temporada e quatro destaques: artilheiro, Craque do Brasileirão, Melhor Goleiro e melhor ataque. Temporada 2025 pré-selecionada.
2. **Tendências:** média móvel de 5 e 10 jogos da equipe escolhida (Flamengo pré-selecionado), ranking dos últimos 5 jogos e matriz de aproveitamento. A segmentação de equipe não filtra o ranking nem a matriz.
3. **Estatísticas:** resultados como Derrota, Empate e Vitória em percentual, pontos por jogo por equipe com a média do campeonato, dispersão saldo × pontos e regularidade.
4. **Modelos:** perguntas e respostas sobre o que é previsto, como, quais modelos, qual foi escolhido e a margem de erro; MAE e RMSE por modelo com nomes amigáveis; tabela comparativa e importância das variáveis.
5. **Previsões:** previsto, real e faixa de 90% tracejada para a equipe escolhida (Flamengo pré-selecionado), com aviso e cobertura observada.
6. **Central de Consulta:** apresentação, botão para a central publicada e seis temas com perguntas de exemplo.
7. **Metodologia:** indicadores reais, três blocos explicativos, as oito etapas do processo e o bloco "Explore o projeto por dentro".

### Filtros e proteção contra mistura de temporadas

- As medidas da classificação (`Pontos (temporada)`, `Posição` e as demais) ficam vazias quando há mais de uma temporada no filtro, e o cartão "Sobre esta tabela" pede a escolha.
- A pré-seleção (2025 e Flamengo) é gravada na segmentação. Se uma versão do Power BI ignorar a pré-seleção, a proteção acima continua valendo.

### Destaques e escudos

`config/destaques.csv` (gerado por `scripts/obter_destaques.py`) e `config/escudos.csv` (`scripts/obter_escudos.py`) alimentam as tabelas `destaque_artilheiro`, `destaque_craque`, `destaque_goleiro` e `destaque_ataque`, ligadas a `dim_temporadas[ano]`. Fotos só entram com licença livre; sem foto, aparece uma silhueta. Quando a fonte não registra um prêmio, a linha diz "Não informado na fonte".

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
