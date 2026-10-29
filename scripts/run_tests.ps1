# Executa testes, lint e verificação de formatação.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$py = ".venv\Scripts\python.exe"
& $py -B -m pytest
& $py -m ruff check .
& $py -m ruff format --check .
