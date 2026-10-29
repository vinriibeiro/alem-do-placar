# Além do Placar

Plataforma analítica de inteligência esportiva (futebol, Campeonato Brasileiro Série A) que combina engenharia de dados, estatística, Machine Learning, Power BI e um assistente de IA.

**Status atual:** T002 — auditoria e catálogo das fontes de dados. A fundação (T001) permanece como base. Não há coleta de dados, modelos, API funcional, dashboard ou assistente.

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

As dependências de execução (Pandas, DuckDB, scikit-learn, MLflow, FastAPI etc.) serão declaradas somente nas tarefas que as utilizarem. O catálogo de fontes (T002) usa apenas a biblioteca padrão (`tomllib`); não há pacote novo.

## Testes

```powershell
python -B -m pytest
```

O parâmetro `-B` evita a gravação de arquivos `__pycache__`. Os testes da fundação e do catálogo usam apenas a biblioteca padrão e o Pytest, não exigem rede, dados reais nem bibliotecas de fases futuras.

## Lint e formatação

```powershell
python -m ruff check .
python -m ruff format --check .
```

## Configuração

1. Copie o modelo: `Copy-Item .env.example .env` (PowerShell) ou `cp .env.example .env` (bash).
2. Preencha somente localmente os valores necessários. O arquivo `.env` nunca deve ser versionado.
3. Parâmetros não sensíveis ficam em `config/settings.yaml`. Credenciais são referenciadas pelo nome da variável de ambiente (`api_key_env`), nunca pelo valor.

## Catálogo de fontes (T002)

O arquivo `config/data_sources.toml` é o catálogo versionado das fontes candidatas do PRD (seção 3.1): Football-Data, StatsBomb Open Data e OpenFootball. Cada fonte é uma tabela `[[fontes]]` com licença, status de licença, cobertura do Brasileirão, temporadas, campos essenciais e complementares, riscos, decisão e um mapeamento preliminar dos campos do PRD (seções 3.3 e 3.4) para as colunas esperadas em cada fonte.

Regras e limites:

- **Status pendente:** nesta etapa, todas as fontes têm `status_licenca = "pendente_verificacao"` e `decisao = "pendente"`. Nenhuma fonte foi selecionada.
- **Valores "a verificar":** indicam ausência de evidência. Não devem ser tratados como fatos confirmados.
- **Licença verificada:** só é aceita com `url_termos`, `data_verificacao` e `verificador` preenchidos.
- **Fonte principal:** só pode ser marcada como `selecionada` com licença verificada e `justificativa` preenchida. No máximo uma fonte pode ser selecionada.
- **Revisão humana:** a verificação de licenças depende de revisão humana. O código aplica regras formais de consistência, mas não confirma termos de uso. Cabe ao responsável do projeto ler os termos de cada fonte e registrar a evidência antes de qualquer decisão.
- **Sem rede:** a validação não acessa a internet e não baixa dados.

O carregamento e a validação ficam em `src/ingestion/source_catalog.py` (`carregar_catalogo`). Após a instalação editável, o uso é:

```python
from ingestion.source_catalog import carregar_catalogo

catalogo = carregar_catalogo("config/data_sources.toml")
```

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
- Nenhum módulo de `src/` contém pipeline; `source_catalog.py` apenas carrega e valida o catálogo.
- A CI executa instalação, lint, formatação e testes em Python 3.12, mas ainda não foi disparada.

## Próximos passos

1. Revisão técnica (Codex) e QA do catálogo T002.
2. Verificação humana das licenças e da cobertura de cada fonte candidata.
3. Decisão sobre a fonte principal, com justificativa registrada, antes da T003.
