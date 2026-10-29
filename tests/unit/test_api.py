"""Testes da API local do assistente (T009) com cliente em processo, sem rede."""

import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.app import create_app

PERGUNTA = {"pergunta": "Qual é a previsão do Flamengo?"}


def _raiz(tmp_path: Path) -> Path:
    dados = tmp_path / "data"
    (dados / "processed").mkdir(parents=True)
    (dados / "predictions" / "modelagem").mkdir(parents=True)
    (dados / "predictions" / "cientifica").mkdir(parents=True)
    partes = []
    for equipe, pts in (("Flamengo", [3] * 8 + [1] * 8), ("Santos", [0] * 16)):
        p = pd.Series(pts, dtype="int64")
        partes.append(
            pd.DataFrame(
                {
                    "equipe": equipe,
                    "temporada": 2025,
                    "data_referencia": pd.date_range("2025-03-01", periods=16, freq="7D"),
                    "pontos": p,
                    "media_pontos_5": p.rolling(5).mean(),
                    "desvio_pontos_5": p.rolling(5, min_periods=1).std(ddof=0),
                }
            )
        )
    pd.concat(partes, ignore_index=True).to_parquet(
        dados / "processed" / "dataset_analitico.parquet", index=False
    )
    pd.DataFrame(
        {
            "equipe": ["Flamengo"],
            "data_referencia": pd.to_datetime(["2025-09-08"]),
            "previsao": [2.4],
            "limite_inferior": [1.2],
            "limite_superior": [3.0],
            "observado": [2.6],
        }
    ).to_parquet(dados / "predictions" / "modelagem" / "previsoes.parquet", index=False)
    meta = {
        "modelo_selecionado": "M01_ridge",
        "versao": "T006-1.0",
        "ano_holdout": 2025,
        "corte_treino": "2025-03-29",
    }
    (dados / "predictions" / "modelagem" / "metadados.json").write_text(
        json.dumps(meta), encoding="utf-8"
    )
    pd.DataFrame(
        {"atributo": ["media_pontos_5"], "delta_mae_media": [0.05], "delta_mae_desvio": [0.01]}
    ).to_csv(dados / "predictions" / "cientifica" / "importancias.csv", index=False)
    return tmp_path


@pytest.fixture
def cliente(tmp_path: Path) -> TestClient:
    return TestClient(create_app(_raiz(tmp_path)), base_url="http://127.0.0.1")


def test_health_contexto_e_resposta_valida(cliente):
    assert cliente.get("/health").json() == {"app": "alem-do-placar", "status": "ok"}
    assert cliente.get("/api/contexto").json()["anos"] == [2025]
    r = cliente.post("/api/pergunta", json=PERGUNTA)
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_origem_local_permitida_e_maliciosa_bloqueada(cliente):
    local = cliente.post("/api/pergunta", json=PERGUNTA, headers={"Origin": "http://127.0.0.1"})
    assert local.status_code == 200
    evil = cliente.post("/api/pergunta", json=PERGUNTA, headers={"Origin": "http://evil.example"})
    assert evil.status_code == 403


def test_host_malicioso_bloqueado(cliente):
    assert cliente.get("/health", headers={"Host": "evil.example"}).status_code == 400


def test_origem_malformada_e_rejeitada_sem_erro_interno(cliente):
    resposta = cliente.post("/api/pergunta", json=PERGUNTA, headers={"Origin": "http://["})
    assert resposta.status_code == 403


def test_entrada_invalida_e_campo_extra_rejeitados(cliente):
    assert cliente.post("/api/pergunta", json={"pergunta": "ab"}).status_code == 422
    assert cliente.post("/api/pergunta", json={"pergunta": "x" * 501}).status_code == 422
    extra = cliente.post("/api/pergunta", json={**PERGUNTA, "raiz": "/etc"})
    assert extra.status_code == 422 and "raiz" not in extra.text
    assert cliente.post("/api/pergunta", json={**PERGUNTA, "equipe": "x" * 101}).status_code == 422


def test_html_sem_cdn_sem_innerhtml_com_fontes_e_selo(cliente):
    r = cliente.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    html = r.text
    assert "Histórico 2018–2025" in html and "Segoe UI" in html and "Além do Placar" in html
    assert "#17364D" in html and "#188A8A" in html
    assert "http://" not in html and "https://" not in html
    assert "innerHTML" not in html


def test_sem_dados_retorna_503(tmp_path):
    cliente = TestClient(create_app(tmp_path), base_url="http://127.0.0.1")
    r = cliente.post("/api/pergunta", json={"pergunta": "Qual é o erro médio?"})
    assert r.status_code == 503 and r.json()["status"] == "indisponivel"
