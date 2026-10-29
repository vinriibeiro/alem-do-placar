"""Testes da fundação do projeto (T001).

Usam apenas a biblioteca padrão e o Pytest: não acessam rede, dados reais
nem bibliotecas de fases futuras.
"""

import ast
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DIRETORIOS_PREVISTOS = [
    ".github/workflows",
    "config",
    "dashboard/assets",
    "dashboard/powerbi",
    "data/interim",
    "data/predictions",
    "data/processed",
    "data/raw",
    "docs",
    "notebooks",
    "reports/figures",
    "reports/metrics",
    "src/api",
    "src/evaluation",
    "src/features",
    "src/ingestion",
    "src/models",
    "src/processing",
    "src/validation",
    "tests/api",
    "tests/integration",
    "tests/model",
    "tests/unit",
]

DIRETORIOS_COM_GITKEEP = [
    "dashboard/assets",
    "dashboard/powerbi",
    "data/interim",
    "data/predictions",
    "data/processed",
    "data/raw",
    "notebooks",
    "reports/figures",
    "reports/metrics",
    "tests/api",
    "tests/integration",
    "tests/model",
]

DIRETORIOS_DADOS = ["data/raw", "data/interim", "data/processed", "data/predictions"]

PACOTES_SRC = [
    "api",
    "evaluation",
    "features",
    "ingestion",
    "models",
    "processing",
    "validation",
]

REGRAS_GITIGNORE_ORIGINAIS = [
    ".env",
    ".env.*",
    "!.env.example",
    "*.pem",
    "*.key",
    "secrets/",
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    "*.log",
    "*.tmp",
    ".cache/",
    ".pytest_cache/",
    "dist/",
    "build/",
    "coverage/",
    ".DS_Store",
    "Thumbs.db",
    ".vscode/*",
    "!.vscode/extensions.json",
    "!.vscode/settings.json",
]

REGRAS_GITIGNORE_NOVAS = [
    "*.parquet",
    "*.duckdb",
    "*.joblib",
    "*.pkl",
    "mlruns/",
    ".ruff_cache/",
    ".ipynb_checkpoints/",
]


def _ler(caminho: str) -> str:
    return (ROOT / caminho).read_text(encoding="utf-8")


def _regras_gitignore() -> set[str]:
    linhas = _ler(".gitignore").splitlines()
    return {
        linha.strip() for linha in linhas if linha.strip() and not linha.lstrip().startswith("#")
    }


def test_diretorios_previstos_existem():
    faltantes = [d for d in DIRETORIOS_PREVISTOS if not (ROOT / d).is_dir()]
    assert faltantes == []


def test_gitkeep_contem_comentario_e_nao_fica_vazio():
    for diretorio in DIRETORIOS_COM_GITKEEP:
        texto = _ler(f"{diretorio}/.gitkeep")
        assert texto.lstrip().startswith("#"), diretorio


def test_init_dos_pacotes_contem_apenas_docstring():
    for pacote in PACOTES_SRC:
        arvore = ast.parse(_ler(f"src/{pacote}/__init__.py"))
        assert ast.get_docstring(arvore), pacote
        assert len(arvore.body) == 1, pacote


def test_pyproject_define_python_pytest_e_grupos():
    dados = tomllib.loads(_ler("pyproject.toml"))
    projeto = dados["project"]
    assert projeto["requires-python"] == ">=3.12"
    assert isinstance(projeto["dependencies"], list)
    grupos = projeto["optional-dependencies"]
    assert {"test", "lint"} <= set(grupos)
    assert any(dep.startswith("pytest") for dep in grupos["test"])
    assert any(dep.startswith("ruff") for dep in grupos["lint"])
    assert dados["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
    assert dados["tool"]["ruff"]["target-version"] == "py312"


def test_settings_contem_secoes_e_nenhum_valor_secreto():
    texto = _ler("config/settings.yaml")
    assert "competition:" in texto
    assert "paths:" in texto
    assert "api_key_env: LLM_API_KEY" in texto
    suspeitas = re.findall(r"(?im)^\s*[\w-]*(?:token|password|secret|api_key)\s*:\s*\S", texto)
    assert suspeitas == []


def test_env_example_contem_apenas_placeholders():
    linhas = [
        linha.strip()
        for linha in _ler(".env.example").splitlines()
        if linha.strip() and not linha.lstrip().startswith("#")
    ]
    assert any(linha.startswith("LLM_API_KEY=") for linha in linhas)
    for linha in linhas:
        chave, sep, valor = linha.partition("=")
        assert sep == "=", linha
        if re.search(r"(KEY|TOKEN|SECRET|PASSWORD)$", chave):
            assert valor == "" or re.fullmatch(r"<[^<>]+>", valor), linha


def test_gitignore_preserva_regras_e_protege_dados():
    regras = _regras_gitignore()
    esperadas = set(REGRAS_GITIGNORE_ORIGINAIS) | set(REGRAS_GITIGNORE_NOVAS)
    esperadas |= {f"{d}/*" for d in DIRETORIOS_DADOS}
    esperadas |= {f"!{d}/.gitkeep" for d in DIRETORIOS_DADOS}
    assert esperadas <= regras


def test_workflow_ci_basico():
    texto = _ler(".github/workflows/ci.yml")
    trechos = [
        'python-version: "3.12"',
        "pip install -e",
        "ruff check",
        "ruff format --check",
        "python -B -m pytest",
        "pull_request",
    ]
    assert [trecho for trecho in trechos if trecho not in texto] == []


def test_readme_documenta_instalacao_e_testes():
    texto = _ler("README.md")
    trechos = [".venv", "python -m pip install -e", "python -B -m pytest", "## Limitações"]
    assert [trecho for trecho in trechos if trecho not in texto] == []
