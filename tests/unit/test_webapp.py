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
    for rota in ("/", "/dashboard", "/consulta", "/metodologia"):
        html = c.get(rota).text
        for ref in re.findall(r'(?:src|href)="(static/[^"]+)"', html):
            ref = "/" + ref
            assert c.get(ref).status_code == 200, ref
    assert (ESTATICOS / "img" / "og.png").is_file()


def test_nenhum_html_ou_js_usa_innerhtml_nem_script_inline(raiz):
    c = _cli(raiz)
    for rota in ("/", "/dashboard", "/consulta", "/metodologia"):
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
    assert 'src="figuras/importancias.png"' in html and "figuras/residuos_hist.png" not in html


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


def test_paginas_usam_links_relativos_para_funcionar_no_github_pages(raiz):
    html = _cli(raiz).get("/").text
    assert 'href="consulta.html"' in html and 'href="dashboard.html"' in html
    assert 'href="/' not in html.replace('href="/"', "") and 'src="/' not in html


def test_rotas_html_e_redirecionamento_do_assistente(raiz):
    c = _cli(raiz)
    for rota in ("/index.html", "/dashboard.html", "/consulta.html", "/metodologia.html"):
        assert c.get(rota).status_code == 200, rota
    r = c.get("/assistente", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "consulta"


def test_dados_da_central_servidos_em_json(raiz):
    c = _cli(raiz)
    cfg = c.get("/dados/config.json")
    assert cfg.status_code == 200 and cfg.json()["powerbi_embed_url"] == ""
    assert c.get("/dados/inexistente.json").status_code == 404
