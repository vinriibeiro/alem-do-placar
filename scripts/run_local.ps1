# Sobe o assistente local do Além do Placar em http://127.0.0.1:8765
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Ambiente .venv ausente. Rode: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e '.[test,lint]'"
}
& ".venv\Scripts\python.exe" -m api.server --raiz $raiz --port 8765
