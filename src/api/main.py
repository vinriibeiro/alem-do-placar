"""Ponto de entrada de produção (container): lê a porta e o host do ambiente.

Uso: python -m api.main   (variáveis: PORT, HOST, APP_ROOT e as de api.config)
"""

import os
from pathlib import Path

import uvicorn

from api.app import create_app
from api.config import carregar_env_local


def criar() -> object:
    raiz = Path(os.environ.get("APP_ROOT") or Path.cwd())
    carregar_env_local(raiz)
    return create_app(raiz)


def main() -> None:
    uvicorn.run(
        criar(),
        host=os.environ.get("HOST", "0.0.0.0"),  # noqa: S104 - necessário dentro do container
        port=int(os.environ.get("PORT", "8000")),
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
