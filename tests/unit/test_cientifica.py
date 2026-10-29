"""Testes unitários da avaliação científica (T007).

Usam ``ModeloStub``, um modelo determinístico sem treino, sem rede e sem pickle. Os arquivos
são gravados somente em ``tmp_path``. Observação (BAIXO, não bloqueia aceite): não há teste
determinístico de ΔMAE negativo, porque com erro original zero o embaralhamento não pode
reduzir o MAE; o código preserva o sinal sem recorte, mas essa propriedade só é verificável
com um cenário adicional de modelo não perfeito.
"""

import json

import numpy as np
import pandas as pd
import pytest

from evaluation.cientifica import avaliar_cientificamente
from features.temporais import ALVO, FEATURES, FIM_ALVO
from models.backtesting import BASELINE, BASELINE_HISTORICO, LIMITE_PREVISAO

ANO = 2025
SELECIONADO_ML = "M01_ridge"
N = 12
PNG = b"\x89PNG\r\n\x1a\n"


class ModeloStub:
    """Previsão = media_pontos_5 + deslocamento. Não treina e não lê arquivos."""

    def __init__(self, deslocamento: float = 0.0) -> None:
        self.deslocamento = deslocamento

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X["media_pontos_5"].to_numpy(dtype=float) + self.deslocamento


def _dataset(n: int = N) -> pd.DataFrame:
    gerador = np.random.default_rng(0)
    media = np.linspace(1.0, 2.0, n)
    colunas = {
        "equipe": [f"Equipe {i % 3}" for i in range(n)],
        "partida_id": np.arange(n),
        "data_referencia": pd.date_range("2025-01-01", periods=n, freq="7D"),
        "temporada": np.full(n, ANO),
        FIM_ALVO: pd.date_range("2025-02-01", periods=n, freq="7D"),
        ALVO: media,
        "media_pontos_5": media,
    }
    for atributo in FEATURES:
        colunas.setdefault(atributo, gerador.normal(size=n))
    return pd.DataFrame(colunas)


def _metricas(selecionado: str) -> pd.DataFrame:
    linhas = []
    for modelo in dict.fromkeys([BASELINE, selecionado]):
        mae = 0.6 if modelo == BASELINE else 0.4
        linhas.append(
            {
                "fase": "holdout",
                "modelo": modelo,
                "temporada": "todas",
                "mae": mae,
                "rmse": mae * 1.2,
                "vies": 0.0,
                "n": N,
            }
        )
    # Valores fictícios de fixture para validação; não são resultados reais.
    linhas += [
        {
            "fase": "validacao",
            "modelo": BASELINE,
            "temporada": "todas",
            "mae": 0.604116,
            "rmse": 0.75,
            "vies": 0.0,
            "n": 100,
        },
        {
            "fase": "validacao",
            "modelo": BASELINE_HISTORICO,
            "temporada": "todas",
            "mae": 0.65,
            "rmse": 0.8,
            "vies": 0.0,
            "n": 100,
        },
    ]
    return pd.DataFrame(linhas)


def _previsoes(dataset: pd.DataFrame, modelo: ModeloStub, meia_largura: float) -> pd.DataFrame:
    base = dataset[dataset["temporada"] == ANO]
    previsao = np.clip(modelo.predict(base), *LIMITE_PREVISAO)
    return (
        base[["equipe", "partida_id", "data_referencia"]]
        .assign(
            previsao=previsao,
            limite_inferior=previsao - meia_largura,
            limite_superior=previsao + meia_largura,
        )
        .reset_index(drop=True)
    )


def _cenario(
    selecionado: str = BASELINE,
    deslocamento: float = 0.0,
    meia_largura: float = 0.5,
    n: int = N,
) -> tuple[dict, pd.DataFrame]:
    dataset = _dataset(n)
    modelo = ModeloStub(deslocamento)
    resultado = {
        "previsoes": _previsoes(dataset, modelo, meia_largura),
        "modelo_ajustado": modelo,
        "modelo_selecionado": selecionado,
        "metadados": {"ano_holdout": ANO},
        "atributos": list(FEATURES),
        "metricas": _metricas(selecionado),
        "versao": "teste-T007",
        "corte_treino": "2025-01-01",
    }
    return resultado, dataset


def test_residuo_zero_quando_previsao_coincide_com_alvo():
    resultado, dataset = _cenario()
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    assert np.allclose(resposta["residuos"]["residuo"], 0.0)
    metricas = resposta["resumo"]["metricas_holdout"]
    assert metricas["n"] == N
    assert metricas["mae"] == pytest.approx(0.0)
    assert metricas["rmse"] == pytest.approx(0.0)
    assert metricas["vies"] == pytest.approx(0.0)
    assert metricas["cobertura_intervalo"] == 1.0


@pytest.mark.parametrize("deslocamento", [0.5, -0.5])
def test_residuo_e_previsao_menos_alvo_com_sinal(deslocamento):
    resultado, dataset = _cenario(deslocamento=deslocamento)
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    assert np.allclose(resposta["residuos"]["residuo"], deslocamento)
    metricas = resposta["resumo"]["metricas_holdout"]
    assert metricas["mae"] == pytest.approx(0.5)
    assert metricas["vies"] == pytest.approx(deslocamento)
    assert np.sign(metricas["vies"]) == np.sign(deslocamento)


def test_cobertura_mede_alvos_fora_do_intervalo():
    resultado, dataset = _cenario(deslocamento=0.5, meia_largura=0.1)
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    assert resposta["resumo"]["metricas_holdout"]["cobertura_intervalo"] == 0.0
    assert not resposta["residuos"]["dentro_intervalo"].any()


def test_importancia_positiva_para_atributo_usado_e_zero_para_os_demais():
    resultado, dataset = _cenario()
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=5)

    importancias = resposta["importancias"]
    assert list(importancias.columns) == ["atributo", "delta_mae_media", "delta_mae_desvio"]
    assert importancias.iloc[0]["atributo"] == "media_pontos_5"
    indice = importancias.set_index("atributo")["delta_mae_media"]
    assert indice["media_pontos_5"] > 0
    assert (indice.drop("media_pontos_5") == 0.0).all()


def test_permutacao_e_repetivel_com_mesma_seed():
    resultado, dataset = _cenario()
    primeira = avaliar_cientificamente(resultado, dataset, n_repeticoes=3)
    segunda = avaliar_cientificamente(resultado, dataset, n_repeticoes=3)

    pd.testing.assert_frame_equal(primeira["importancias"], segunda["importancias"])
    assert primeira["resumo"] == segunda["resumo"]


def test_nao_altera_entradas_nem_modelo():
    resultado, dataset = _cenario()
    dataset_antes = dataset.copy(deep=True)
    previsoes_antes = resultado["previsoes"].copy(deep=True)
    atributos_antes = list(resultado["atributos"])
    modelo = resultado["modelo_ajustado"]
    estado_antes = dict(vars(modelo))

    avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    pd.testing.assert_frame_equal(dataset, dataset_antes)
    pd.testing.assert_frame_equal(resultado["previsoes"], previsoes_antes)
    assert resultado["atributos"] == atributos_antes
    assert vars(modelo) == estado_antes


def test_chave_duplicada_em_previsoes_falha():
    resultado, dataset = _cenario()
    previsoes = resultado["previsoes"]
    resultado["previsoes"] = pd.concat([previsoes, previsoes.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=2)


def test_chave_sem_correspondencia_no_holdout_falha():
    resultado, dataset = _cenario()
    resultado["previsoes"].loc[0, "partida_id"] = 999

    with pytest.raises(ValueError, match="sem correspondência"):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=2)


def test_previsoes_sem_colunas_obrigatorias_falham():
    resultado, dataset = _cenario()
    resultado["previsoes"] = resultado["previsoes"].drop(columns="limite_superior")

    with pytest.raises(ValueError, match="sem colunas obrigatórias"):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=2)


def test_resultado_sem_chave_obrigatoria_falha():
    resultado, dataset = _cenario()
    del resultado["modelo_ajustado"]

    with pytest.raises(ValueError, match="sem chaves obrigatórias"):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=2)


def test_dataset_vazio_falha():
    resultado, dataset = _cenario()

    with pytest.raises(ValueError, match="dataset vazio"):
        avaliar_cientificamente(resultado, dataset.iloc[0:0], n_repeticoes=2)


def test_holdout_sem_linhas_elegiveis_falha():
    resultado, dataset = _cenario()
    dataset = dataset.assign(temporada=ANO - 1)

    with pytest.raises(ValueError, match="sem linhas elegíveis"):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=2)


def test_previsoes_divergentes_do_modelo_falham():
    resultado, dataset = _cenario()
    resultado["previsoes"]["previsao"] += 0.3

    with pytest.raises(RuntimeError, match="divergem"):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=2)


def test_n_repeticoes_invalido_falha():
    resultado, dataset = _cenario()

    with pytest.raises(ValueError, match="n_repeticoes"):
        avaliar_cientificamente(resultado, dataset, n_repeticoes=0)


def test_hipoteses_com_baseline_selecionado():
    resultado, dataset = _cenario(selecionado=BASELINE)
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    status = {h["id"]: h["status"] for h in resposta["hipoteses"]}
    assert list(status) == ["H01", "H02", "H03", "H04", "H05", "H06"]
    assert status["H01"] == "observado_nesta_comparacao"
    assert status["H02"] == "favoravel_nesta_comparacao"
    assert status["H03"] == "nao_conclusiva"
    assert status["H04"] == "nao_conclusiva"
    assert status["H05"] == "desfavoravel_nesta_comparacao"
    assert status["H06"] == "nao_avaliavel"


def test_hipoteses_com_modelo_ml_superior_ao_baseline():
    resultado, dataset = _cenario(selecionado=SELECIONADO_ML)
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    status = {h["id"]: h["status"] for h in resposta["hipoteses"]}
    assert status["H05"] == "favoravel_nesta_comparacao"
    assert status["H06"] == "nao_avaliavel"
    comparacao = resposta["resumo"]["comparacao"]["holdout"]
    assert comparacao["diferenca_mae_selecionado_menos_baseline"] == pytest.approx(-0.2)


def test_grupos_por_equipe_e_temporada_somam_observacoes():
    resultado, dataset = _cenario()
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    assert resposta["por_equipe"]["n"].sum() == N
    assert set(resposta["por_equipe"]["equipe"]) == {"Equipe 0", "Equipe 1", "Equipe 2"}
    assert resposta["por_temporada"]["temporada"].tolist() == [ANO]
    assert resposta["por_temporada"]["n"].tolist() == [N]


def test_piores_erros_limitados_e_ordenados():
    resultado, dataset = _cenario(deslocamento=0.2, n=25)
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    piores = resposta["piores_erros"]
    assert len(piores) == 10
    assert piores["erro_absoluto"].is_monotonic_decreasing


def test_limitacoes_declaram_xg_e_ausencia_de_causalidade():
    resultado, dataset = _cenario()
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    texto = " ".join(resposta["limitacoes"])
    assert "xG" in texto
    assert "causais" in texto


def test_sem_pasta_saida_nao_grava_arquivos():
    resultado, dataset = _cenario()
    resposta = avaliar_cientificamente(resultado, dataset, n_repeticoes=2)

    assert "caminhos" not in resposta


def test_exporta_relatorios_tabelas_e_graficos_nao_vazios(tmp_path):
    resultado, dataset = _cenario()
    pasta = tmp_path / "saida"
    resposta = avaliar_cientificamente(resultado, dataset, pasta, n_repeticoes=2)

    caminhos = resposta["caminhos"]
    assert set(caminhos) == {
        "relatorio_json",
        "relatorio_md",
        "importancias",
        "residuos",
        "grafico_residuos",
        "grafico_previsto_observado",
        "grafico_importancias",
    }
    for caminho in caminhos.values():
        assert caminho.parent == pasta
        assert caminho.stat().st_size > 0
    for chave in ("grafico_residuos", "grafico_previsto_observado", "grafico_importancias"):
        assert caminhos[chave].read_bytes().startswith(PNG)

    relatorio = json.loads(caminhos["relatorio_json"].read_text(encoding="utf-8"))
    assert relatorio["resumo"]["modelo_selecionado"] == BASELINE
    assert len(relatorio["hipoteses"]) == 6
    assert "Relatório científico" in caminhos["relatorio_md"].read_text(encoding="utf-8")
    assert len(pd.read_parquet(caminhos["residuos"])) == N
    assert len(pd.read_csv(caminhos["importancias"])) == len(FEATURES)
