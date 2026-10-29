"""API FastAPI local do assistente (T009; PRD 9 e 10).

``create_app`` apenas monta a aplicação; não inicia servidor na importação. Somente hosts locais
são aceitos, e POST com ``Origin`` de outro domínio é rejeitado.
"""

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.assistant import BaseConsultas

HOSTS_LOCAIS = ("127.0.0.1", "localhost")
ESTATICO = Path(__file__).resolve().parent / "static" / "index.html"


class Pergunta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pergunta: str = Field(min_length=3, max_length=500)
    ano: int | None = None
    equipe: str | None = Field(default=None, max_length=100)


def _origem_valida(request: Request) -> bool:
    """Sem Origin (cliente local) ou Origin igual ao host local servido, com a mesma porta."""
    origem = request.headers.get("origin")
    if origem is None:
        return True
    try:
        partes = urlsplit(origem)
    except ValueError:
        return False
    return (
        partes.scheme == "http"
        and partes.hostname in HOSTS_LOCAIS
        and partes.netloc == request.headers.get("host", "")
    )


def create_app(raiz: Path) -> FastAPI:
    base = BaseConsultas(Path(raiz))
    html = ESTATICO.read_text(encoding="utf-8")
    app = FastAPI(title="Além do Placar", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(HOSTS_LOCAIS))

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
        return base.contexto()

    @app.post("/api/pergunta")
    def perguntar(corpo: Pergunta, request: Request) -> JSONResponse:
        if not _origem_valida(request):
            return JSONResponse({"detail": "origem não permitida"}, status_code=403)
        resposta = base.responder(corpo.pergunta, corpo.ano, corpo.equipe)
        status = 503 if resposta["status"] == "indisponivel" else 200
        return JSONResponse(resposta, status_code=status)

    return app
