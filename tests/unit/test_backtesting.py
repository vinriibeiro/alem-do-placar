import json
import math

import joblib
import numpy as np
import pandas as pd
import pytest

from features.temporais import ALVO, FEATURES, FIM_ALVO, gerar_atributos
from models import backtesting as bt

EQUIPES = ("A", "B", "C", "D", "E", "F")
ARGS = {"anos_validacao": (2021, 2022), "ano_holdout": 2023}


def _base(anos=(2020, 2021, 2022, 2023)) -> pd.DataFrame:
    linhas = []
    for ano in anos:
        confrontos = [(m, v) for m in EQUIPES for v in EQUIPES if m != v]
        for k, (m, v) in enumerate(confrontos):
            linhas.append(
                {
                    "partida_id": f"{ano}-{k}",
                    "data_partida": pd.Timestamp(f"{ano}-01-01") + pd.Timedelta(days=k),
                    "temporada": ano,
                    "equipe_mandante": m,
                    "equipe_visitante": v,
                    "gols_mandante": k % 4,
                    "gols_visitante": (7 * k + ano) % 3,
                }
            )
    return pd.DataFrame(linhas)


def _dataset(anos=(2020, 2021, 2022, 2023)) -> pd.DataFrame:
    return gerar_atributos(_base(anos))


def test_executa_backtest_com_colunas_e_limites():
    resultado = bt.executar_backtest(_dataset(), **ARGS)
    previsoes = resultado["previsoes"]
    assert resultado["modelo_selecionado"] in bt.MODELOS
    assert resultado["corte_treino"] == "2023-01-01"
    assert resultado["atributos"] == list(FEATURES)
    assert list(previsoes.columns) == list(bt.COLUNAS_PREVISAO)
    assert previsoes["horizonte"].eq(5).all()
    assert set(previsoes["temporada"]) == {2023}
    assert previsoes[["alvo", "previsao", "limite_inferior", "limite_superior"]].notna().all().all()
    assert previsoes["previsao"].between(0, 3).all()
    assert (previsoes["limite_inferior"] <= previsoes["previsao"]).all()
    assert (previsoes["previsao"] <= previsoes["limite_superior"]).all()


def test_temporada_posterior_ao_holdout_nao_e_processada():
    resultado = bt.executar_backtest(_dataset((2020, 2021, 2022, 2023, 2024)), **ARGS)
    temporadas = set(resultado["metricas"]["temporada"].astype(str))
    assert temporadas <= {"2021", "2022", "2023", "todas"}


def test_features_nao_incluem_alvo_fim_ou_identificadores():
    proibidas = {
        ALVO,
        FIM_ALVO,
        "partida_id",
        "equipe",
        "pontos",
        "gols_pro",
        "gols_contra",
        "saldo_gols",
        "adversario",
        "data_referencia",
        "temporada",
    }
    assert not proibidas & set(FEATURES)


def test_treino_exclui_rotulo_que_alcanca_o_teste():
    inicio = pd.Timestamp("2023-01-01")
    elegiveis = pd.DataFrame(
        {
            "data_referencia": [pd.Timestamp("2022-12-20"), pd.Timestamp("2022-12-28")],
            FIM_ALVO: [pd.Timestamp("2022-12-31"), inicio],
        }
    )
    assert len(bt._treino_ate(elegiveis, inicio)) == 1


def test_guarda_de_vazamento_reprova_rotulo_no_teste():
    inicio = pd.Timestamp("2023-01-01")
    with pytest.raises(RuntimeError, match="vazamento"):
        bt._conferir_treino(pd.DataFrame({FIM_ALVO: [inicio] * 25}), inicio)


def test_holdout_nao_participa_da_selecao():
    dataset = _dataset()
    alterado = dataset.copy()
    alterado.loc[alterado["temporada"] == 2023, ALVO] = 3.0
    original = bt.executar_backtest(dataset, **ARGS)
    variante = bt.executar_backtest(alterado, **ARGS)
    assert variante["modelo_selecionado"] == original["modelo_selecionado"]
    pd.testing.assert_frame_equal(
        variante["resultados_validacao"], original["resultados_validacao"]
    )


def test_repeticao_produz_resultados_identicos():
    primeiro = bt.executar_backtest(_dataset(), **ARGS)
    segundo = bt.executar_backtest(_dataset(), **ARGS)
    pd.testing.assert_frame_equal(primeiro["previsoes"], segundo["previsoes"])
    pd.testing.assert_frame_equal(primeiro["metricas"], segundo["metricas"])


def test_selecao_mantem_baseline_sem_ganho_minimo():
    mae = pd.DataFrame(
        {2021: [1.0, 0.99, 0.99, 0.99], 2022: [1.0, 0.99, 0.99, 0.99]}, index=bt.MODELOS
    )
    assert bt._selecionar(mae)[0] == bt.BASELINE


def test_selecao_escolhe_ml_com_ganho_consistente():
    mae = pd.DataFrame(
        {2021: [1.0, 0.9, 0.95, 0.95], 2022: [1.0, 0.9, 0.95, 0.95]}, index=bt.MODELOS
    )
    assert bt._selecionar(mae)[0] == "M01_ridge"


def test_selecao_rejeita_ml_com_piora_anual_acima_de_10_por_cento():
    mae = pd.DataFrame(
        {2021: [1.0, 0.8, 0.99, 0.99], 2022: [1.0, 1.15, 0.99, 0.99]}, index=bt.MODELOS
    )
    assert bt._selecionar(mae)[0] == bt.BASELINE


def test_metricas_exatas():
    avaliacoes = pd.DataFrame(
        {
            "fase": ["validacao"] * 3,
            "modelo": ["m"] * 3,
            "temporada": [2021] * 3,
            "equipe": ["A", "B", "C"],
            "alvo": [0.0, 3.0, 2.0],
            "previsao": [1.0, 2.0, 4.0],
        }
    )
    metricas = bt._metricas(avaliacoes, ["fase", "modelo", "temporada"])
    assert metricas.loc[0, "mae"] == pytest.approx(4 / 3)
    assert metricas.loc[0, "rmse"] == pytest.approx(math.sqrt(2))
    assert metricas.loc[0, "vies"] == pytest.approx(2 / 3)
    assert metricas.loc[0, "n"] == 3


def test_baseline_usa_media_do_treino_quando_media_recente_ausente():
    modelo = bt._ajustar(bt.BASELINE, pd.DataFrame({"pontos": [0, 3, 3]}))
    teste = pd.DataFrame({bt.MEDIA_RECENTE: [np.nan, 1.5]})
    assert bt._predizer(modelo, teste).tolist() == [2.0, 1.5]


def test_media_historica_de_treino_e_constante():
    modelo = bt._ajustar(bt.BASELINE_HISTORICO, pd.DataFrame({ALVO: [1.0, 2.0, 3.0]}))
    assert bt._predizer(modelo, pd.DataFrame({"x": [0, 0]})).tolist() == [2.0, 2.0]


def test_rejeita_holdout_2026_fora_do_periodo_aprovado():
    with pytest.raises(ValueError, match="2026"):
        bt.executar_backtest(_dataset(), ano_holdout=2026)


def test_dados_insuficientes_geram_erro_explicito():
    dataset = _dataset()
    with pytest.raises(ValueError, match="treino insuficiente"):
        bt.executar_backtest(
            dataset[dataset["temporada"] == 2021], anos_validacao=(2021,), ano_holdout=2023
        )
    with pytest.raises(ValueError, match="anteriores ao holdout"):
        bt.executar_backtest(dataset, anos_validacao=(2023,), ano_holdout=2023)


def test_salva_arquivos_e_modelo_proprio(tmp_path):
    resultado = bt.executar_backtest(_dataset(), pasta_saida=tmp_path / "saida", **ARGS)
    caminhos = resultado["caminhos"]
    assert set(caminhos) == {"metricas", "metricas_equipe", "previsoes", "modelo", "metadados"}
    assert all(caminho.exists() for caminho in caminhos.values())
    previsoes = pd.read_parquet(caminhos["previsoes"])
    assert list(previsoes.columns) == list(bt.COLUNAS_PREVISAO)
    metadados = json.loads(caminhos["metadados"].read_text(encoding="utf-8"))
    assert metadados["modelo_selecionado"] == resultado["modelo_selecionado"]
    assert hasattr(joblib.load(caminhos["modelo"]), "predict")
    assert isinstance(json.loads(caminhos["metricas"].read_text(encoding="utf-8")), list)
