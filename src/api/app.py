"""API FastAPI do assistente (T009; PRD 9 e 10).

``create_app`` apenas monta a aplicação; não inicia servidor na importação. Hosts e origens
permitidos vêm da configuração (padrão: somente locais). POST com ``Origin`` fora da lista é
rejeitado, há limite de taxa por IP, teto diário de chamadas ao LLM e limite de tamanho do corpo.
"""

from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.assistant import BaseConsultas
from api.config import Config
from api.servico import Servico

ESTATICO = Path(__file__).resolve().parent / "static" / "index.html"
MAX_CORPO = 4096


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
    html = ESTATICO.read_text(encoding="utf-8")
    app = FastAPI(title="Além do Placar", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.hosts)

    @app.middleware("http")
    async def protecoes(request: Request, call_next):
        tamanho = request.headers.get("content-length")
        if tamanho and tamanho.isdigit() and int(tamanho) > MAX_CORPO:
            return JSONResponse({"detail": "corpo muito grande"}, status_code=413)
        resposta = await call_next(request)
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resposta

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Não devolve o corpo recebido nem detalhes internos da validação.
        return JSONResponse({"detail": "entrada inválida"}, status_code=422)

    @app.get("/", response_class=HTMLResponse)
    def pagina() -> str:
        return html

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
