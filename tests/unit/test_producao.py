"""Testes de configuração de produção: CSP, HTTPS, hosts do Render e ponto de entrada."""

import pytest
from fastapi.testclient import TestClient
from test_catalogo_llm import _raiz

import api.main as principal
from api.app import CSP, create_app
from api.config import Config, carregar_env_local


@pytest.fixture
def raiz(tmp_path):
    return _raiz(tmp_path)


def _cli(raiz, host="127.0.0.1", **env):
    return TestClient(create_app(raiz, env=env), base_url=f"http://{host}")


def test_csp_restringe_scripts_e_permite_apenas_powerbi_em_iframe(raiz):
    h = _cli(raiz).get("/").headers
    assert h["content-security-policy"] == CSP
    assert "script-src 'self'" in CSP and "unsafe-inline" not in CSP
    assert "frame-src https://app.powerbi.com" in CSP and "frame-ancestors 'none'" in CSP


def test_hsts_somente_quando_a_requisicao_chegou_por_https(raiz):
    c = _cli(raiz)
    assert "strict-transport-security" not in c.get("/health").headers
    h = c.get("/health", headers={"X-Forwarded-Proto": "https"}).headers
    assert h["strict-transport-security"].startswith("max-age=")


def test_force_https_redireciona_http_de_dominio_publico(raiz):
    c = _cli(raiz, host="alem.onrender.com", ALLOWED_HOSTS="alem.onrender.com", FORCE_HTTPS="true")
    r = c.get("/dashboard", follow_redirects=False)
    assert r.status_code == 308 and r.headers["location"] == "https://alem.onrender.com/dashboard"
    ok = c.get("/dashboard", headers={"X-Forwarded-Proto": "https"}, follow_redirects=False)
    assert ok.status_code == 200


def test_force_https_nao_atrapalha_health_nem_localhost(raiz):
    pub = _cli(
        raiz, host="alem.onrender.com", ALLOWED_HOSTS="alem.onrender.com", FORCE_HTTPS="true"
    )
    assert pub.get("/health", follow_redirects=False).status_code == 200
    assert _cli(raiz, FORCE_HTTPS="true").get("/", follow_redirects=False).status_code == 200


def test_host_do_render_e_aceito_automaticamente(raiz):
    c = _cli(
        raiz, host="meu-servico.onrender.com", RENDER_EXTERNAL_HOSTNAME="meu-servico.onrender.com"
    )
    assert c.get("/health").status_code == 200
    assert (
        _cli(raiz, host="outro.onrender.com", RENDER_EXTERNAL_HOSTNAME="meu-servico.onrender.com")
        .get("/health")
        .status_code
        == 400
    )


def test_head_nas_paginas_para_previews_de_links(raiz):
    c = _cli(raiz)
    for rota in ("/", "/dashboard", "/assistente", "/metodologia"):
        r = c.head(rota)
        assert r.status_code == 200 and r.content == b""


def test_config_padrao_e_segura():
    cfg = Config({})
    assert cfg.hosts == ["127.0.0.1", "localhost"] and cfg.llm_key is None
    assert cfg.forcar_https is False and cfg.confia_proxy is False
    assert cfg.llm_diario == 500 and cfg.taxa_por_min == 20


def test_carregar_env_local_nao_sobrescreve_ambiente(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "# c\nLLM_DAILY_LIMIT=7\nTESTE_X='abc'\nVAZIA=\n", encoding="utf-8"
    )
    monkeypatch.setenv("LLM_DAILY_LIMIT", "99")
    monkeypatch.delenv("TESTE_X", raising=False)
    carregar_env_local(tmp_path)
    import os

    assert os.environ["LLM_DAILY_LIMIT"] == "99" and os.environ["TESTE_X"] == "abc"
    monkeypatch.delenv("TESTE_X", raising=False)


def test_ponto_de_entrada_usa_app_root_e_sobe_o_app(raiz, monkeypatch):
    monkeypatch.setenv("APP_ROOT", str(raiz))
    app = principal.criar()
    assert TestClient(app, base_url="http://127.0.0.1").get("/health").json()["status"] == "ok"
