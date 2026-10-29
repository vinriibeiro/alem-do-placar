"""Testes do front-end servido pela API (T009 v2, F2): páginas, estáticos, config e figuras."""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_catalogo_llm import _raiz

from api.app import create_app

ESTATICOS = Path(__file__).resolve().parents[2] / "src" / "api" / "static"


@pytest.fixture
def raiz(tmp_path):
    r = _raiz(tmp_path)
    docs = r / "docs"
    docs.mkdir()
    (docs / "model_card.md").write_text(
        "# Model Card\n\n## Alvo\n\nTexto.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8"
    )
    (docs / "methodology.md").write_text("# Metodologia\n\n## Limites\n\n- um\n", encoding="utf-8")
    fig = r / "data" / "predictions" / "cientifica"
    (fig / "importancias.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    return r


def _cli(raiz, **env):
    return TestClient(create_app(raiz, env=env), base_url="http://127.0.0.1")


def test_html_referencia_apenas_arquivos_existentes(raiz):
    c = _cli(raiz)
    for rota in ("/", "/dashboard", "/assistente", "/metodologia"):
        html = c.get(rota).text
        for ref in re.findall(r'(?:src|href)="(/static/[^"]+)"', html):
            assert c.get(ref).status_code == 200, ref
    assert (ESTATICOS / "img" / "og.png").is_file()


def test_nenhum_html_ou_js_usa_innerhtml_nem_script_inline(raiz):
    c = _cli(raiz)
    for rota in ("/", "/dashboard", "/assistente", "/metodologia"):
        html = c.get(rota).text
        assert "innerHTML" not in html
        assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html)
    for js in (ESTATICOS / "js").glob("*.js"):
        assert "innerHTML" not in js.read_text(encoding="utf-8"), js.name


def test_config_valida_url_do_embed(raiz):
    ok = _cli(
        raiz,
        POWERBI_EMBED_URL="https://app.powerbi.com/view?r=abc",
        REPO_URL="https://github.com/u/r",
    )
    cfg = ok.get("/api/config").json()
    assert cfg["powerbi_embed_url"].startswith("https://app.powerbi.com/") and cfg["repo_url"]
    ruim = _cli(raiz, POWERBI_EMBED_URL="https://evil.example/x", REPO_URL="javascript:alert(1)")
    cfg = ruim.get("/api/config").json()
    assert cfg["powerbi_embed_url"] == "" and cfg["repo_url"] == ""
    assert _cli(raiz).get("/api/config").json()["powerbi_embed_url"] == ""


def test_contexto_traz_numeros_para_os_kpis(raiz):
    ctx = _cli(raiz).get("/api/contexto").json()
    assert ctx["partidas"] == 24 and ctx["temporadas"] == 2
    assert "temas" in ctx


def test_metodologia_renderiza_documentos_e_figuras(raiz):
    html = _cli(raiz).get("/metodologia").text
    assert "<table>" in html and "Model Card" in html and "Limites" in html
    assert "/figuras/importancias.png" in html and "/figuras/residuos_hist.png" not in html


def test_figuras_somente_da_lista_branca(raiz):
    c = _cli(raiz)
    assert c.get("/figuras/importancias.png").status_code == 200
    assert c.get("/figuras/residuos_hist.png").status_code == 404
    assert c.get("/figuras/..%2Fmetadados.json").status_code == 404
    assert c.get("/figuras/importancias.png/../../x").status_code in {404, 400}


def test_cache_de_estaticos_e_sem_traversal(raiz):
    c = _cli(raiz)
    r = c.get("/static/css/app.css")
    assert "max-age" in r.headers["cache-control"]
    assert c.get("/static/../app.py").status_code == 404
    assert c.get("/static/%2e%2e/app.py").status_code == 404


def test_metodologia_sem_documentos_nao_quebra(tmp_path):
    r = _cli(_raiz(tmp_path)).get("/metodologia")
    assert r.status_code == 200 and "não estão disponíveis" in r.text


def test_dashboard_embeda_somente_via_config(raiz):
    html = _cli(raiz, POWERBI_EMBED_URL="https://app.powerbi.com/view?r=abc").get("/dashboard").text
    assert "app.powerbi.com" not in html  # a URL só chega pelo /api/config, nunca no HTML
