import math
import sys

import pandas as pd
import pytest

from models.experimentos import registrar_experimento, tracking_uri_local

BASELINE = "M00_media_recente_5"


def _resultado() -> dict:
    metricas = pd.DataFrame(
        [
            {
                "fase": "validacao",
                "modelo": BASELINE,
                "temporada": "todas",
                "mae": 0.9,
                "rmse": 1.1,
                "vies": 0.01,
                "n": 30,
            },
            {
                "fase": "holdout",
                "modelo": BASELINE,
                "temporada": "todas",
                "mae": 0.8,
                "rmse": 1.0,
                "vies": -0.02,
                "n": 20,
            },
        ]
    )
    return {
        "metricas": metricas,
        "modelo_selecionado": BASELINE,
        "versao": "T006-1.0",
        "atributos": ["media_pontos_3", "media_pontos_5"],
        "metadados": {
            "seed": 42,
            "anos_validacao": [2021, 2022],
            "ano_holdout": 2023,
            "corte_treino": "2023-01-01",
            "horizonte": 5,
            "quantil_erro_absoluto": 1.2,
            "cobertura_holdout": 0.9,
        },
    }


def test_registra_parametros_e_metricas_em_sqlite_local(tmp_path):
    mlflow = pytest.importorskip("mlflow")
    from mlflow.tracking import MlflowClient

    uri_antes = mlflow.get_tracking_uri()
    pasta = tmp_path / "mlruns"
    run_id = registrar_experimento(_resultado(), pasta)

    assert mlflow.get_tracking_uri() == uri_antes
    assert (pasta / "mlflow.db").is_file()
    run = MlflowClient(tracking_uri=tracking_uri_local(pasta)).get_run(run_id)
    assert run.info.status == "FINISHED"
    assert run.data.params["seed"] == "42"
    assert run.data.params["modelo"] == BASELINE
    assert run.data.metrics[f"validacao_mae_{BASELINE}"] == pytest.approx(0.9)
    assert all(math.isfinite(valor) for valor in run.data.metrics.values())


def test_metrica_nao_finita_gera_erro_sem_registrar(tmp_path):
    resultado = _resultado()
    resultado["metadados"]["cobertura_holdout"] = float("nan")
    with pytest.raises(ValueError, match="não finita"):
        registrar_experimento(resultado, tmp_path / "mlruns")


def test_mlflow_indisponivel_gera_erro_claro(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "mlflow.tracking", None)
    with pytest.raises(RuntimeError, match="indisponível"):
        registrar_experimento(_resultado(), tmp_path / "mlruns")
