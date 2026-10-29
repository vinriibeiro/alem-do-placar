# Além do Placar

Plataforma analítica de inteligência esportiva (futebol, Campeonato Brasileiro Série A) que combina engenharia de dados, estatística, Machine Learning, Power BI e um assistente de IA.

**Status atual:** T001 — fundação do projeto. Esta etapa contém apenas estrutura de diretórios, configuração de Python/Pytest, lint, CI básica e documentação. Não há coleta de dados, modelos, API funcional, dashboard ou assistente.

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

- `test`: Pytest.
- `lint`: Ruff (lint e formatação).

As dependências de execução (Pandas, DuckDB, scikit-learn, MLflow, FastAPI etc.) serão declaradas somente nas tarefas que as utilizarem.

## Testes

```powershell
python -B -m pytest
```

O parâmetro `-B` evita a gravação de arquivos `__pycache__`. Os testes da fundação usam apenas a biblioteca padrão e o Pytest, não exigem rede, dados reais nem bibliotecas de fases futuras.

## Lint e formatação

```powershell
python -m ruff check .
python -m ruff format --check .
```

## Configuração

1. Copie o modelo: `Copy-Item .env.example .env` (PowerShell) ou `cp .env.example .env` (bash).
2. Preencha somente localmente os valores necessários. O arquivo `.env` nunca deve ser versionado.
3. Parâmetros não sensíveis ficam em `config/settings.yaml`. Credenciais são referenciadas pelo nome da variável de ambiente (`api_key_env`), nunca pelo valor.

## Estrutura

```text
config/            configurações externas (settings.yaml)
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

- Nenhuma fonte de dados foi auditada ou aprovada (T002).
- Nenhum módulo de `src/` contém implementação; os `__init__.py` apenas documentam a responsabilidade.
- A CI executa instalação, lint, formatação e testes em Python 3.12, mas ainda não foi disparada.
- As licenças das fontes de dados permanecem pendentes de verificação.

## Próximos passos

1. Revisão técnica (Codex) e QA desta fundação.
2. T002: auditoria e seleção das fontes de dados.
