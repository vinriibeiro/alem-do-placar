"""Inicialização local da API do assistente (T009).

Uso: python -m api.server --raiz <projeto> --port 8765

Escuta somente em 127.0.0.1, sem reload, sem debug e sem abrir navegador automaticamente.
"""

import argparse
from pathlib import Path

import uvicorn

from api.app import create_app
from api.config import carregar_env_local

HOST = "127.0.0.1"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Assistente local Além do Placar.")
    parser.add_argument("--raiz", required=True, type=Path, help="pasta do projeto")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    carregar_env_local(args.raiz)
    app = create_app(args.raiz)
    uvicorn.run(
        app,
        host=HOST,
        port=args.port,
        reload=False,
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
