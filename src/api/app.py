"""API FastAPI do assistente (T009; PRD 9 e 10).

``create_app`` apenas monta a aplicação; não inicia servidor na importação. Hosts e origens
permitidos vêm da configuração (padrão: somente locais). POST com ``Origin`` fora da lista é
rejeitado, há limite de taxa por IP, teto diário de chamadas ao LLM e limite de tamanho do corpo.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api import central
from api.assistant import BaseConsultas
from api.config import HOSTS_LOCAIS, Config
from api.paginas import FIGURAS, Paginas
from api.servico import Servico

ESTATICO = Path(__file__).resolve().parent / "static"
HOSTS_EMBED = ("https://app.powerbi.com/", "https://app.fabric.microsoft.com/")
MAX_CORPO = 4096
# Política de conteúdo: tudo do próprio site, fontes do Google e iframes somente do Power BI.
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https://upload.wikimedia.org https://thumb.wikimedia.org; "
    "connect-src 'self'; "
    "frame-src https://app.powerbi.com https://app.fabric.microsoft.com; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


class Pergunta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pergunta: str = Field(min_length=3, max_length=500)
    ano: int | None = None
    equipe: str | None = Field(default=None, max_length=100)


def _origem_valida(request: Request, config: Config) -> bool:
    """Sem Origin (cliente local), Origin explicitamente permitido ou igual ao host servido."""
    origem = request.headers.get("origin")
    if origem is None:
        return True
    if origem in config.origens:
        return True
    try:
        partes = urlsplit(origem)
    except ValueError:
        return False
    host = request.headers.get("host", "")
    return (
        partes.scheme in {"http", "https"}
        and partes.hostname in config.hosts
        and partes.netloc == host
    )


def _ip(request: Request, config: Config) -> str:
    if config.confia_proxy:
        encaminhado = request.headers.get("x-forwarded-for", "")
        if encaminhado:
            return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


def create_app(
    raiz: Path,
    cliente_llm=None,
    env: Mapping[str, str] | None = None,
) -> FastAPI:
    config = Config(env)
    base = BaseConsultas(Path(raiz))
    servico = Servico(base, config, cliente_llm)
    paginas = Paginas(Path(raiz))
    pasta_figuras = Path(raiz) / "data" / "predictions" / "cientifica"
    app = FastAPI(title="Além do Placar", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.hosts)

    @app.middleware("http")
    async def protecoes(request: Request, call_next):
        https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        local = request.url.hostname in HOSTS_LOCAIS or request.url.path == "/health"
        if config.forcar_https and not https and not local:
            return RedirectResponse(str(request.url.replace(scheme="https")), status_code=308)
        tamanho = request.headers.get("content-length")
        if tamanho and tamanho.isdigit() and int(tamanho) > MAX_CORPO:
            return JSONResponse({"detail": "corpo muito grande"}, status_code=413)
        resposta = await call_next(request)
        if request.url.path.startswith("/static/"):
            resposta.headers.setdefault("Cache-Control", "public, max-age=3600")
        resposta.headers.setdefault("Content-Security-Policy", CSP)
        if https:
            resposta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resposta

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Não devolve o corpo recebido nem detalhes internos da validação.
        return JSONResponse({"detail": "entrada inválida"}, status_code=422)

    def _rota_pagina(caminho: str, nome: str) -> None:
        @app.api_route(caminho, methods=["GET", "HEAD"], response_class=HTMLResponse, name=nome)
        def _pagina() -> str:
            return paginas.html[nome]

    for caminho, nome in (
        ("/", "inicio"),
        ("/index.html", "inicio"),
        ("/dashboard", "dashboard"),
        ("/dashboard.html", "dashboard"),
        ("/consulta", "consulta"),
        ("/consulta.html", "consulta"),
        ("/metodologia", "metodologia"),
        ("/metodologia.html", "metodologia"),
    ):
        _rota_pagina(caminho, nome)

    @app.get("/assistente")
    def assistente_antigo() -> RedirectResponse:
        return RedirectResponse("consulta", status_code=301)

    def _config_publica() -> dict:
        embed = config.embed_url if config.embed_url.startswith(HOSTS_EMBED) else ""
        repo = config.repo_url if config.repo_url.startswith("https://") else ""
        return {"powerbi_embed_url": embed, "repo_url": repo, "versao": "0.1.0"}

    try:
        dados_publicos = {
            nome: json.dumps(valor, ensure_ascii=False, separators=(",", ":"))
            for nome, valor in central.montar(Path(raiz), _config_publica()).items()
        }
    except (OSError, ValueError, KeyError, StopIteration):
        # Instalação sem dados completos: só a configuração fica disponível.
        dados_publicos = {"config": json.dumps(_config_publica())}

    @app.get("/dados/{nome}.json")
    def dados(nome: str) -> Response:
        if nome not in dados_publicos:
            return JSONResponse({"detail": "não encontrado"}, status_code=404)
        return Response(
            dados_publicos[nome],
            media_type="application/json",
            headers={"Cache-Control": "public, max-age=600"},
        )

    app.mount("/static", StaticFiles(directory=ESTATICO), name="static")

    @app.get("/figuras/{nome}")
    def figura(nome: str):
        if nome not in FIGURAS or not (pasta_figuras / nome).is_file():
            return JSONResponse({"detail": "não encontrado"}, status_code=404)
        return FileResponse(pasta_figuras / nome, headers={"Cache-Control": "public, max-age=3600"})

    @app.get("/api/config")
    def configuracao() -> dict:
        return _config_publica()

    @app.get("/health")
    def saude() -> dict:
        return {"app": "alem-do-placar", "status": "ok"}

    @app.get("/api/contexto")
    def contexto() -> dict:
        return servico.contexto()

    @app.get("/api/sugestoes")
    def sugestoes() -> dict:
        return {"sugestoes": servico.sugestoes()}

    @app.post("/api/pergunta")
    def perguntar(corpo: Pergunta, request: Request) -> JSONResponse:
        if not _origem_valida(request, config):
            return JSONResponse({"detail": "origem não permitida"}, status_code=403)
        if not servico.taxa.permitir(_ip(request, config)):
            return JSONResponse(
                {"detail": "Muitas perguntas em pouco tempo. Aguarde um minuto e tente de novo."},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        resposta = servico.perguntar(corpo.pergunta, corpo.ano, corpo.equipe)
        status = 503 if resposta["status"] == "indisponivel" else 200
        return JSONResponse(resposta, status_code=status)

    return app
