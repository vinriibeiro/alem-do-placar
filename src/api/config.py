"""Configuração por ambiente do assistente (sem segredos no código)."""

import os
from collections.abc import Mapping
from pathlib import Path

HOSTS_LOCAIS = ("127.0.0.1", "localhost")


def carregar_env_local(raiz: Path) -> None:
    """Lê KEY=VALOR de ``.env`` (somente local) sem sobrescrever variáveis já definidas."""
    arquivo = Path(raiz) / ".env"
    if not arquivo.is_file():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave, valor = chave.strip(), valor.strip().strip('"').strip("'")
        if chave and valor and chave not in os.environ:
            os.environ[chave] = valor


def _lista(valor: str | None) -> list[str]:
    return [v.strip() for v in (valor or "").split(",") if v.strip()]


class Config:
    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        e = os.environ if env is None else env
        # RENDER_EXTERNAL_HOSTNAME é definido automaticamente pelo Render.
        self.hosts = [
            *HOSTS_LOCAIS,
            *_lista(e.get("ALLOWED_HOSTS")),
            *_lista(e.get("RENDER_EXTERNAL_HOSTNAME")),
        ]
        self.origens = _lista(e.get("ALLOWED_ORIGINS"))
        self.llm_key = (e.get("LLM_API_KEY") or "").strip() or None
        self.llm_modelo = e.get("LLM_MODEL") or "claude-opus-5-5"
        self.llm_diario = int(e.get("LLM_DAILY_LIMIT") or 500)
        self.taxa_por_min = int(e.get("RATE_LIMIT_PER_MIN") or 20)
        self.embed_url = (e.get("POWERBI_EMBED_URL") or "").strip()
        self.repo_url = (e.get("REPO_URL") or "").strip()
        self.forcar_https = (e.get("FORCE_HTTPS") or "").lower() in {"1", "true", "yes"}
        self.confia_proxy = (e.get("TRUST_PROXY") or "").lower() in {"1", "true", "yes"}
