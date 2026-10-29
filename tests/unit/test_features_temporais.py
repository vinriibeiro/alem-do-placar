"""Testes sintéticos dos atributos temporais e do alvo de cinco partidas (T005).

Não usam rede nem dados reais; cada cenário é construído em memória ou em ``tmp_path``.
"""

import numpy as np
import pandas as pd
import pytest

from features.temporais import (
    ALVO,
    FEATURES,
    FIM_ALVO,
    exportar_dataset,
    gerar_atributos,
)

# Pontos da equipe Alfa, 2020, em 12 partidas (3 = vitória, 1 = empate, 0 = derrota).
PONTOS_ALFA = [3, 0, 1, 3, 3, 0, 1, 3, 0, 3, 1, 3]
INICIO = pd.Timestamp("2020-01-04")


def _partida(pid, dia, temporada, equipe, adversario, em_casa, pontos):
    """Partida com gols coerentes com os pontos da equipe informada."""
    pro, contra = {3: (1, 0), 1: (0, 0), 0: (0, 1)}[pontos]
    if em_casa:
        return (pid, dia, temporada, equipe, adversario, pro, contra)
    return (pid, dia, temporada, adversario, equipe, contra, pro)


def _base(partidas):
    colunas = [
        "partida_id",
        "data_partida",
        "temporada",
        "equipe_mandante",
        "equipe_visitante",
        "gols_mandante",
        "gols_visitante",
    ]
    return pd.DataFrame(partidas, columns=colunas)


def _base_alfa(pontos=PONTOS_ALFA):
    return _base(
        _partida(
            f"A20-{i:02d}",
            INICIO + pd.Timedelta(days=7 * i),
            2020,
            "Alfa",
            f"Adv{i:02d}",
            i % 2 == 0,
            p,
        )
        for i, p in enumerate(pontos)
    )


def _base_com_2021():
    base_2021 = [
        _partida(
            f"A21-{i:02d}",
            pd.Timestamp("2021-01-02") + pd.Timedelta(days=7 * i),
            2021,
            "Alfa",
            f"Adv21-{i:02d}",
            True,
            0,
        )
        for i in range(6)
    ]
    base = _base_alfa()
    return pd.concat([base, _base(base_2021)], ignore_index=True)


def _alfa(dataset):
    return dataset[dataset["equipe"] == "Alfa"].reset_index(drop=True)


def test_duas_linhas_por_partida_com_mando_complementar():
    base = _base_alfa()
    dataset = gerar_atributos(base)

    assert len(dataset) == 2 * len(base)
    assert (dataset.groupby("partida_id").size() == 2).all()
    for _, grupo in dataset.groupby("partida_id"):
        assert sorted(grupo["mando"]) == [0, 1]


def test_alvo_e_media_exata_das_cinco_partidas_seguintes():
    alfa = _alfa(gerar_atributos(_base_alfa()))
    esperado = [sum(PONTOS_ALFA[i + 1 : i + 6]) / 5 for i in range(len(PONTOS_ALFA) - 5)]

    assert np.allclose(alfa[ALVO].iloc[: len(esperado)], esperado)
    assert alfa[ALVO].iloc[0] == pytest.approx(1.4)


def test_ultimas_cinco_partidas_sem_alvo_nem_fim_alvo():
    alfa = _alfa(gerar_atributos(_base_alfa()))

    assert alfa[ALVO].iloc[-5:].isna().all()
    assert alfa[FIM_ALVO].iloc[-5:].isna().all()
    assert alfa[ALVO].iloc[:-5].notna().all()
    assert alfa[FIM_ALVO].iloc[:-5].notna().all()


def test_fim_alvo_e_data_da_quinta_partida_seguinte():
    alfa = _alfa(gerar_atributos(_base_alfa()))

    assert alfa[FIM_ALVO].iloc[0] == alfa["data_referencia"].iloc[5]
    assert alfa[FIM_ALVO].iloc[6] == alfa["data_referencia"].iloc[11]


def test_partida_atual_nao_entra_no_alvo_mas_entra_nos_atributos():
    alfa = _alfa(gerar_atributos(_base_alfa()))
    pontos_alterados = list(PONTOS_ALFA)
    pontos_alterados[3] = 0
    alterada = _alfa(gerar_atributos(_base_alfa(pontos_alterados)))

    assert alterada[ALVO].iloc[3] == pytest.approx(alfa[ALVO].iloc[3])
    assert alterada[ALVO].iloc[2] != pytest.approx(alfa[ALVO].iloc[2])
    assert alterada["media_pontos_3"].iloc[3] != pytest.approx(alfa["media_pontos_3"].iloc[3])


def test_valores_de_janelas_desvio_e_saldo():
    alfa = _alfa(gerar_atributos(_base_alfa()))

    assert alfa["media_pontos_3"].iloc[2] == pytest.approx((3 + 0 + 1) / 3)
    assert alfa["media_pontos_5"].iloc[4] == pytest.approx(2.0)
    # Saldos das cinco primeiras: +1, -1, 0, +1, +1.
    assert alfa["media_saldo_gols_3"].iloc[2] == pytest.approx(0.0)
    assert alfa["media_saldo_gols_5"].iloc[4] == pytest.approx(0.4)
    assert alfa["desvio_pontos_5"].iloc[1] == pytest.approx(np.std([3, 0]))


def test_cold_start_usa_nan_e_historico_de_mando():
    alfa = _alfa(gerar_atributos(_base_alfa()))

    assert alfa["media_pontos_3"].iloc[:2].isna().all()
    assert alfa["media_pontos_3"].iloc[2] == pytest.approx(4 / 3)
    assert alfa["media_pontos_10"].iloc[:9].isna().all()
    assert alfa["desvio_pontos_5"].iloc[0] == pytest.approx(0.0)
    assert alfa["jogos_acumulados"].iloc[0] == 1
    assert pd.isna(alfa["dias_descanso"].iloc[0])
    assert alfa["dias_descanso"].iloc[1] == pytest.approx(7.0)
    assert alfa["mando"].iloc[0] == 1
    assert alfa["mando"].iloc[1] == 0
    # Jogo em casa na primeira partida; primeiro jogo fora na segunda (derrota).
    assert alfa["media_pontos_mandante_historico"].iloc[0] == pytest.approx(3.0)
    assert pd.isna(alfa["media_pontos_visitante_historico"].iloc[0])
    assert alfa["media_pontos_visitante_historico"].iloc[1] == pytest.approx(0.0)
    assert alfa["media_pontos_mandante_historico"].iloc[1] == pytest.approx(3.0)


def test_mudancas_futuras_nao_alteram_atributos_passados():
    alfa = _alfa(gerar_atributos(_base_alfa()))
    futuro_alterado = list(PONTOS_ALFA)
    futuro_alterado[8:] = [1, 1, 0, 0]
    alterada = _alfa(gerar_atributos(_base_alfa(futuro_alterado)))

    pd.testing.assert_frame_equal(
        alfa[list(FEATURES)].iloc[:8],
        alterada[list(FEATURES)].iloc[:8],
    )


def test_permutacao_da_entrada_nao_altera_o_resultado():
    base = _base_com_2021()
    esperado = gerar_atributos(base)

    embaralhada = base.sample(frac=1, random_state=11).reset_index(drop=True)
    invertida = base.iloc[::-1].reset_index(drop=True)

    pd.testing.assert_frame_equal(esperado, gerar_atributos(embaralhada))
    pd.testing.assert_frame_equal(esperado, gerar_atributos(invertida))


def test_geracao_reproduzivel():
    base = _base_com_2021()

    pd.testing.assert_frame_equal(gerar_atributos(base), gerar_atributos(base))


def test_transicao_de_temporada_nao_cruza_o_horizonte_nem_o_historico():
    dataset = gerar_atributos(_base_com_2021())
    alfa = _alfa(dataset)
    temporada_2020 = alfa[alfa["temporada"] == 2020].reset_index(drop=True)
    temporada_2021 = alfa[alfa["temporada"] == 2021].reset_index(drop=True)

    # Os jogos de 2021 (pontos 0) não podem completar o horizonte das últimas de 2020.
    assert temporada_2020[ALVO].iloc[7:].isna().all()
    assert temporada_2020[FIM_ALVO].iloc[7:].isna().all()
    assert temporada_2020[ALVO].iloc[6] == pytest.approx(sum(PONTOS_ALFA[7:]) / 5)

    # O histórico de 2021 começa do zero.
    assert temporada_2021["jogos_acumulados"].iloc[0] == 1
    assert pd.isna(temporada_2021["dias_descanso"].iloc[0])
    assert temporada_2021["media_pontos_3"].iloc[:2].isna().all()
    assert temporada_2021[ALVO].iloc[0] == pytest.approx(0.0)


def test_identificadores_e_alvo_fora_das_features():
    proibidas = {
        "partida_id",
        "equipe",
        "adversario",
        "temporada",
        "data_referencia",
        "pontos",
        "gols_pro",
        "gols_contra",
        "saldo_gols",
        "rodada",
        ALVO,
        FIM_ALVO,
    }

    assert set(FEATURES).isdisjoint(proibidas)
    assert len(set(FEATURES)) == len(FEATURES)


def test_rejeita_partida_duplicada():
    base = pd.concat([_base_alfa(), _base_alfa().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicado"):
        gerar_atributos(base)


def test_rejeita_referencia_temporal_ambigua_da_mesma_equipe():
    base = _base_alfa()
    base.loc[1, "data_partida"] = base.loc[0, "data_partida"]
    with pytest.raises(ValueError, match="temporal ambígua"):
        gerar_atributos(base)


def test_rejeita_data_invalida():
    base = _base_alfa()
    # Coluna em objeto: pandas recusa texto em coluna datetime64 antes da validação do módulo.
    base["data_partida"] = base["data_partida"].astype(object)
    base.loc[2, "data_partida"] = "nao-e-data"

    with pytest.raises(ValueError, match="data_partida"):
        gerar_atributos(base)


def test_rejeita_mandante_igual_visitante_e_placar_negativo():
    base = _base_alfa()
    base.loc[0, "equipe_visitante"] = base.loc[0, "equipe_mandante"]
    with pytest.raises(ValueError, match="mandante igual"):
        gerar_atributos(base)

    negativo = _base_alfa()
    negativo.loc[1, "gols_mandante"] = -1
    with pytest.raises(ValueError, match="gols_mandante"):
        gerar_atributos(negativo)


def test_rejeita_base_sem_colunas_obrigatorias():
    with pytest.raises(ValueError, match="colunas obrigatórias"):
        gerar_atributos(_base_alfa().drop(columns=["gols_visitante"]))


def test_exporta_parquet_e_recusa_outros_formatos(tmp_path):
    dataset = gerar_atributos(_base_com_2021())
    destino = tmp_path / "saida" / "t005.parquet"

    caminho = exportar_dataset(dataset, destino)

    assert caminho == destino
    assert caminho.is_file()
    pd.testing.assert_frame_equal(pd.read_parquet(caminho), dataset)
    with pytest.raises(ValueError, match="Parquet"):
        exportar_dataset(dataset, tmp_path / "t005.csv")
