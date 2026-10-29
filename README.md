# Além do Placar

Plataforma analítica de inteligência esportiva (futebol, Campeonato Brasileiro Série A) que combina engenharia de dados, estatística, Machine Learning, Power BI e um assistente de IA.

**Status atual:** T003 — pipeline de coleta e tratamento sobre arquivos locais sintéticos, implementado e pendente de revisão. A coleta real e a execução sobre dados reais estão bloqueadas até a seleção e a verificação de licença da fonte (T002). Não há modelos, API funcional, dashboard ou assistente.

Referências: `docs/PRD.md` (requisitos), `docs/TASKS.md` (controle de tarefas), `docs/architecture.md` (arquitetura da fundação).

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

- Execução: DuckDB, PyArrow e PyYAML (declaradas em `pyproject.toml`, usadas pelo pipeline T003).
- `test`: Pytest.
- `lint`: Ruff (lint e formatação).

O comando acima instala também as dependências de execução. Nesta etapa elas foram apenas declaradas; não foram instaladas nem executadas. Pandas não é usado.

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

- **Status pendente:** nesta etapa, todas as fontes têm `status_licenca = "pendente_verificacao"` e `decisao = "pendente"`. Nenhuma fonte foi selecionada.
- **Valores "a verificar":** indicam ausência de evidência. Não devem ser tratados como fatos confirmados.
- **Licença verificada:** só é aceita com `url_termos`, `data_verificacao` e `verificador` preenchidos.
- **Fonte principal:** só pode ser marcada como `selecionada` com licença verificada e `justificativa` preenchida. No máximo uma fonte pode ser selecionada.
- **Revisão humana:** a verificação de licenças depende de revisão humana. O código aplica regras formais de consistência, mas não confirma termos de uso.
- **Sem rede:** a validação não acessa a internet e não baixa dados.

O carregamento e a validação ficam em `src/ingestion/source_catalog.py` (`carregar_catalogo`):

```python
from ingestion.source_catalog import carregar_catalogo

catalogo = carregar_catalogo("config/data_sources.toml")
```

## Pipeline de coleta e tratamento (T003)

Fluxo em `src/processing/pipeline.py` (`executar_pipeline`): fonte selecionada no catálogo -> leitura de um CSV local com o mapeamento da fonte -> cópia bruta em `data/raw` -> padronização (equipes por aliases, datas, gols) -> validação de integridade -> tabelas do PRD 5.1 -> Parquet em `data/processed`.

- Sem fonte selecionada, ou com mapeamento `a verificar` em campos lidos, o pipeline falha com `ColetaErro` e não grava dados.
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

- Nenhuma fonte de dados foi aprovada. O catálogo T002 registra as candidatas com decisão pendente.
- As licenças das fontes permanecem `pendente_verificacao`; a verificação exige revisão humana.
- A cobertura do Brasileirão e as temporadas disponíveis estão marcadas como "a verificar".
- O pipeline T003 foi testado apenas com arquivos sintéticos. Não há coleta real, nem execução sobre dados reais, até a seleção da fonte.
- Os aliases de equipes são exemplos e devem ser revisados com a fonte aprovada.
- A CI executa instalação, lint, formatação e testes em Python 3.12, mas ainda não foi disparada.

## Próximos passos

1. Revisão técnica (Codex) do pipeline T003 e do catálogo T002.
2. Verificação humana das licenças e da cobertura de cada fonte candidata.
3. Decisão sobre a fonte principal, com justificativa registrada. Só depois disso a coleta real pode ser executada.
