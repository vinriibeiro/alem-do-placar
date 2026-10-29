# Além do Placar

Plataforma analítica de inteligência esportiva (futebol, Campeonato Brasileiro Série A) que combina engenharia de dados, estatística, Machine Learning, Power BI e um assistente de IA.

**Status atual:** T001–T009 com código entregue e testado localmente (264 testes, lint limpo). Dados reais OpenFootball CC0 2018–2025 (3.040 partidas), modelo Ridge selecionado (MAE 0,478 no holdout de 2025 contra 0,567 do baseline), projeto Power BI gerado e assistente local. Ainda não publicado: o plano de lançamento está em `docs/PLANO_LANCAMENTO_WEB.md`. Revisão Codex, QA Gemini e aprovação do usuário seguem pendentes.

Referências: `docs/PRD.md` (requisitos), `docs/TASKS.md` (controle de tarefas), `docs/architecture.md` (arquitetura da fundação).

## Como executar

Com o ambiente criado (seção Ambiente virtual e Instalação):

```powershell
.\scriptsun_tests.ps1   # pytest, ruff check e ruff format --check
.\scriptsun_local.ps1   # assistente em http://127.0.0.1:8765
```

Plano de publicação: `docs/PLANO_LANCAMENTO_WEB.md`.

## Requisitos

- Python 3.12 ou superior.
- Git.

## Ambiente virtual

PowerShell (Windows):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

bash (Linux/macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

O diretório `.venv/` é ignorado pelo Git.

## Instalação

Com o ambiente virtual ativo, a partir da raiz do projeto:

```powershell
python -m pip install -e ".[test,lint]"
```

Grupos de dependências:

- Execução: DuckDB, PyArrow e PyYAML no pipeline; pandas e matplotlib na análise exploratória T004, declaradas em `pyproject.toml`.
- `test`: Pytest.
- `lint`: Ruff (lint e formatação).

O comando acima instala as dependências de execução. O controlador instalou as bibliotecas no ambiente separado e executou testes, notebook e análise real.

## Testes

```powershell
python -B -m pytest
```

O parâmetro `-B` evita a gravação de arquivos `__pycache__`. Os testes usam arquivos sintéticos criados em diretórios temporários, bloqueiam chamadas de rede e não usam dados reais.

## Lint e formatação

```powershell
python -m ruff check .
python -m ruff format --check .
```

## Configuração

1. Copie o modelo: `Copy-Item .env.example .env` (PowerShell) ou `cp .env.example .env` (bash).
2. Preencha somente localmente os valores necessários. O arquivo `.env` nunca deve ser versionado.
3. Parâmetros não sensíveis ficam em `config/settings.yaml`, inclusive os formatos de data do pipeline (`pipeline.formatos_data`). Credenciais são referenciadas pelo nome da variável de ambiente (`api_key_env`), nunca pelo valor.

## Catálogo de fontes (T002)

O arquivo `config/data_sources.toml` é o catálogo versionado das fontes candidatas do PRD (seção 3.1): Football-Data, StatsBomb Open Data e OpenFootball. Cada fonte é uma tabela `[[fontes]]` com licença, status de licença, cobertura do Brasileirão, temporadas, campos essenciais e complementares, riscos, decisão e um mapeamento preliminar dos campos do PRD (seções 3.3 e 3.4) para as colunas esperadas em cada fonte.

Regras e limites:

- **Registro de candidatas preservado:** em `config/data_sources.toml`, todas permanecem pendentes para manter a auditoria inicial. A execução real usa separadamente `config/approved_source.toml`, que seleciona o perfil OpenFootball CC0 auditado.
- **Valores "a verificar":** indicam ausência de evidência. Não devem ser tratados como fatos confirmados.
- **Licença verificada:** só é aceita com `url_termos`, `data_verificacao` e `verificador` preenchidos.
- **Fonte principal:** só pode ser marcada como `selecionada` com licença verificada e `justificativa` preenchida. No máximo uma fonte pode ser selecionada.
- **Verificação documental:** o controlador consultou os termos e a licença CC0 do OpenFootball; a evidência está em `docs/sources_audit.md`. O código só aplica regras formais e não substitui revisão jurídica. Outras candidatas continuam sem aprovação.
- **Sem rede:** a validação não acessa a internet e não baixa dados.

O carregamento e a validação ficam em `src/ingestion/source_catalog.py` (`carregar_catalogo`):

```python
from ingestion.source_catalog import carregar_catalogo

catalogo = carregar_catalogo("config/data_sources.toml")
```

## Pipeline de coleta e tratamento (T003)

Fluxo em `src/processing/pipeline.py` (`executar_pipeline`): fonte selecionada no catálogo -> leitura de um CSV local com o mapeamento da fonte -> cópia bruta em `data/raw` -> padronização (equipes por aliases, datas, gols) -> validação de integridade -> tabelas do PRD 5.1 -> Parquet em `data/processed`.

- Sem fonte selecionada, ou com qualquer campo do mapeamento `a verificar`, o pipeline falha com `ColetaErro` e não grava dados.
- Achados críticos da validação (duplicidade, mandante igual ao visitante, gols negativos ou não inteiros, pontos fora de 3/1/0, ausências obrigatórias) lançam `IntegridadeErro` antes da gravação das tabelas. Avisos (por exemplo, rodada ausente) são registrados em log.
- As consultas (`src/processing/consultas.py`) usam DuckDB em memória, com SQL fixo e parâmetros `?`, sem criar arquivos `.duckdb`.

## Estrutura

```text
config/            configurações externas (settings.yaml, data_sources.toml)
data/              raw, interim, processed, predictions (conteúdo fora do Git)
dashboard/         powerbi/ e assets/ (fases T008)
docs/              PRD, TASKS, arquitetura
notebooks/         análises exploratórias (fase T004)
reports/           figures/ e metrics/
src/               ingestion, validation, processing, features, models, evaluation, api
tests/             unit, integration, model, api
.github/workflows/ integração contínua básica
```

## Limites desta etapa

- O perfil config/approved_source.toml seleciona OpenFootball CC0 para 2018–2025, com auditoria em docs/sources_audit.md. O catálogo original de candidatas continua preservado.
- A licença CC0 do perfil OpenFootball foi verificada documentalmente. As demais candidatas não foram aprovadas.
- O controlador validou 3.040 partidas reais entre 2018 e 2025, 380 por temporada, com 20 clubes por temporada. Não foi realizada conferência externa com a CBF.
- O pipeline T003 foi validado nos arquivos reais fixos de OpenFootball 2018–2025 e em testes sintéticos. Dados de 2026 continuam fora do processamento.
- Os 54 nomes encontrados no OpenFootball 2018–2025 foram conferidos e normalizados; novas variantes exigirão nova auditoria.
- A CI executa instalação, lint, formatação e testes em Python 3.12, mas ainda não foi disparada.

## Próximos passos

1. T005: atributos temporais e testes contra vazamento de informação.
2. T006/T007: backtesting e avaliação científica com dados históricos já validados.
3. T008/T009: dashboard e assistente local; outras fontes só serão usadas após nova auditoria.

## Análise exploratória (T004)

Notebook em notebooks/01_exploratoria.ipynb e funções em src/evaluation/exploratoria.py. O controlador executou a análise real e salvou resultados reproduzíveis. Consulte docs/methodology.md. Fonte e período conforme docs/sources_audit.md.


