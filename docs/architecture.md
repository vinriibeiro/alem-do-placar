# Arquitetura — Além do Placar (fundação T001)

## Camadas

O projeto separa coleta, validação, processamento, engenharia de atributos, modelagem, avaliação, API e apresentação, conforme `docs/PRD.md` (seção 4.3). Cada camada é um pacote em `src/` com responsabilidade documentada no próprio `__init__.py`:

| Pacote | Responsabilidade | Fase |
|---|---|---|
| `src/ingestion` | Coleta das fontes aprovadas | T003 |
| `src/validation` | Integridade de dados brutos | T003 |
| `src/processing` | Padronização de equipes, datas e resultados | T003 |
| `src/features` | Médias móveis e variável-alvo | T005 |
| `src/models` | Baseline e modelos candidatos | T006 |
| `src/evaluation` | Backtesting, métricas e explicabilidade | T006, T007 |
| `src/api` | API FastAPI do assistente | T009 |

## Dados

- `data/raw`, `data/interim`, `data/processed` e `data/predictions` mantêm apenas `.gitkeep` no Git; o conteúdo é ignorado (`.gitignore`).
- Artefatos grandes (Parquet, DuckDB, modelos serializados, `mlruns/`) não são versionados.

## Configuração e segredos

- Parâmetros não sensíveis: `config/settings.yaml`.
- Credenciais: variáveis de ambiente, definidas em `.env` local (não versionado). `.env.example` contém apenas placeholders.
- O YAML referencia credenciais pelo nome da variável (`api_key_env`).

## Decisões da fundação

- **Python 3.12+** com `requires-python = ">=3.12"`.
- **Layout `src/`** com build via setuptools; pacotes encontrados em `src/`.
- **Dependências de execução vazias** nesta fase; grupos `test` (Pytest) e `lint` (Ruff) são opcionais.
- **Testes da fundação** dependem apenas da biblioteca padrão e do Pytest, sem rede, dados reais ou subprocessos. Não são gravados caches (`-p no:cacheprovider`; `python -B` para bytecode).
- **CI** definida em `.github/workflows/ci.yml`, disparada em pull requests para `main` ou manualmente.

## Fora desta etapa

Coleta, modelos, API funcional, dashboard Power BI e assistente de IA não foram implementados.
