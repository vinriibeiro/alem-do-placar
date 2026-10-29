"""Testes da análise exploratória (T004) com tabelas Parquet pequenas gravadas pela T003.

Os dados são sintéticos e existem apenas nos testes; nenhum dado real é usado.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from evaluation.exploratoria import (
    COLUNAS_BASE,
    carregar_base,
    exportar_analise,
    resumo_exploratorio,
)
from processing.padronizacao import Partida
from processing.persistencia import escrever_tabela
from processing.tabelas import gerar_tabelas

COMPETICAO = "Campeonato Brasileiro Série A"
PNG = b"\x89PNG\r\n\x1a\n"


def _partida(id_, data, temporada, mandante, visitante, gm, gv, rodada) -> Partida:
    return Partida(
        partida_id=id_,
        data_partida=date.fromisoformat(data),
        temporada=temporada,
        competicao=COMPETICAO,
        mandante=mandante,
        visitante=visitante,
        gols_mandante=gm,
        gols_visitante=gv,
        rodada=rodada,
    )


def _partidas_sinteticas() -> list[Partida]:
    """Dados sintéticos de teste: 2 temporadas, 4 equipes, 7 partidas."""
    return [
        _partida("2018-01", "2018-04-01", 2018, "Alfa", "Beta", 2, 1, 1),
        _partida("2018-02", "2018-04-01", 2018, "Gama", "Delta", 0, 0, 1),
        _partida("2018-03", "2018-04-08", 2018, "Beta", "Gama", 1, 3, 2),
        _partida("2018-04", "2018-04-08", 2018, "Delta", "Alfa", 2, 0, 2),
        _partida("2019-01", "2019-04-07", 2019, "Alfa", "Gama", 1, 1, 1),
        _partida("2019-02", "2019-04-07", 2019, "Beta", "Delta", 0, 2, 1),
        _partida("2019-03", "2019-04-14", 2019, "Gama", "Beta", 4, 0, 2),
    ]


def _gravar(tmp_path: Path, partidas: list[Partida], ajustar=None) -> Path:
    """Grava as quatro tabelas T003 em ``tmp_path/processed``; ``ajustar`` altera antes."""
    tabelas = gerar_tabelas(partidas)
    if ajustar is not None:
        ajustar(tabelas)
    pasta = tmp_path / "processed"
    for nome, linhas in tabelas.items():
        escrever_tabela(nome, linhas, pasta)
    return pasta


@pytest.fixture
def pasta_sintetica(tmp_path):
    return _gravar(tmp_path, _partidas_sinteticas())


@pytest.fixture
def base_sintetica(pasta_sintetica):
    return carregar_base(pasta_sintetica)


def test_carregar_base_uma_linha_por_partida(base_sintetica):
    assert len(base_sintetica) == 7
    assert list(base_sintetica.columns) == list(COLUNAS_BASE)
    assert base_sintetica["partida_id"].is_unique
    assert base_sintetica["data_partida"].is_monotonic_increasing
    primeira = base_sintetica.iloc[0]
    assert primeira["partida_id"] == "2018-01"
    assert (primeira["equipe_mandante"], primeira["equipe_visitante"]) == ("Alfa", "Beta")
    assert (primeira["temporada"], primeira["rodada"]) == (2018, 1)


def test_medias_de_gols_e_distribuicao_hda(base_sintetica):
    resumo = resumo_exploratorio(base_sintetica)
    assert resumo["temporadas"] == [2018, 2019]
    assert resumo["quantidade_partidas"] == 7
    assert resumo["quantidade_equipes"] == 4
    assert resumo["media_gols"]["mandante"] == pytest.approx(10 / 7, abs=1e-4)
    assert resumo["media_gols"]["visitante"] == pytest.approx(1.0)
    assert resumo["media_gols"]["total"] == pytest.approx(17 / 7, abs=1e-4)
    dist = resumo["distribuicao_resultados"]
    assert {r: dist[r]["quantidade"] for r in "HDA"} == {"H": 3, "D": 2, "A": 2}
    assert dist["H"]["proporcao"] == pytest.approx(3 / 7, abs=1e-4)


def test_agregado_por_temporada(base_sintetica):
    por_temporada = {
        linha["temporada"]: linha for linha in resumo_exploratorio(base_sintetica)["por_temporada"]
    }
    assert por_temporada[2018]["partidas"] == 4
    assert por_temporada[2018]["gols_totais"] == 9
    assert por_temporada[2018]["media_gols"] == pytest.approx(2.25)
    assert por_temporada[2019]["gols_totais"] == 8
    assert por_temporada[2019]["media_gols"] == pytest.approx(8 / 3, abs=1e-4)


def test_pontos_3_1_0_por_equipe_temporada_e_mando(base_sintetica):
    resumo = resumo_exploratorio(base_sintetica)
    por_eq_temp = {
        (linha["temporada"], linha["equipe"]): linha for linha in resumo["por_equipe_temporada"]
    }
    alfa_2018 = por_eq_temp[(2018, "Alfa")]
    assert (alfa_2018["jogos"], alfa_2018["vitorias"]) == (2, 1)
    assert (alfa_2018["empates"], alfa_2018["derrotas"]) == (0, 1)
    assert alfa_2018["pontos"] == 3
    assert (alfa_2018["gols_pro"], alfa_2018["gols_contra"]) == (2, 3)
    assert alfa_2018["saldo_gols"] == -1
    assert por_eq_temp[(2019, "Alfa")]["pontos"] == 1

    por_equipe = {linha["equipe"]: linha["pontos"] for linha in resumo["por_equipe"]}
    assert por_equipe == {"Alfa": 4, "Beta": 0, "Delta": 7, "Gama": 8}
    assert sum(por_equipe.values()) == 19

    por_mando = {linha["mando"]: linha for linha in resumo["por_mando"]}
    assert (por_mando["mandante"]["vitorias"], por_mando["mandante"]["pontos"]) == (3, 11)
    assert (por_mando["visitante"]["vitorias"], por_mando["visitante"]["pontos"]) == (2, 8)


def test_qualidade_lista_placar_extremo_sem_remover(tmp_path):
    partidas = [
        _partida("x-1", "2018-05-01", 2018, "Alfa", "Beta", 5, 3, 1),
        _partida("x-2", "2018-05-02", 2018, "Gama", "Delta", 0, 0, 1),
    ]
    base = carregar_base(_gravar(tmp_path, partidas))
    resumo = resumo_exploratorio(base)
    assert resumo["quantidade_partidas"] == 2
    assert resumo["qualidade"]["placares_extremos"]["quantidade"] == 1
    assert resumo["qualidade"]["placares_extremos"]["partidas"] == ["x-1"]
    assert resumo["qualidade"]["datas_ausentes"] == 0
    assert resumo["qualidade"]["partidas_duplicadas"] == 0


def test_base_vazia_e_rejeitada(tmp_path):
    pasta = _gravar(tmp_path, [])
    with pytest.raises(ValueError, match="base vazia"):
        carregar_base(pasta)
    with pytest.raises(ValueError, match="base vazia"):
        resumo_exploratorio(pd_dataframe_vazio())


def pd_dataframe_vazio():
    import pandas as pd

    return pd.DataFrame(columns=COLUNAS_BASE)


def test_tabela_ausente_falha_com_mensagem_clara(tmp_path):
    with pytest.raises(FileNotFoundError, match="dim_equipes.parquet"):
        carregar_base(tmp_path)


@pytest.mark.parametrize(
    ("ajustar", "mensagem"),
    [
        (
            lambda t: t["dim_equipes"].append(dict(t["dim_equipes"][0])),
            "chave duplicada em dim_equipes",
        ),
        (
            lambda t: t["fato_partidas"].append(dict(t["fato_partidas"][0])),
            "chave duplicada em fato_partidas",
        ),
        (
            lambda t: t["dim_equipes"].pop(0),
            "sem correspondência",
        ),
        (
            lambda t: t["fato_desempenho_equipes"].append(
                {**t["fato_desempenho_equipes"][0], "partida_id": "nao-existe"}
            ),
            "partida_id ausente",
        ),
    ],
)
def test_joins_invalidos_falham_em_vez_de_duplicar(tmp_path, ajustar, mensagem):
    pasta = _gravar(tmp_path, _partidas_sinteticas(), ajustar=ajustar)
    with pytest.raises(ValueError, match=mensagem):
        carregar_base(pasta)


def test_temporada_2026_reservada_e_rejeitada(tmp_path):
    partidas = [_partida("y-1", "2026-04-01", 2026, "Alfa", "Beta", 1, 0, 1)]
    with pytest.raises(ValueError, match="2026"):
        carregar_base(_gravar(tmp_path, partidas))


def test_resumo_e_json_serializavel_e_sem_nan(base_sintetica):
    resumo = resumo_exploratorio(base_sintetica)
    texto = json.dumps(resumo, allow_nan=False)
    assert json.loads(texto) == resumo


def test_exportar_gera_resumo_e_tres_pngs(tmp_path, base_sintetica):
    caminhos = exportar_analise(base_sintetica, tmp_path / "saida")
    assert set(caminhos) == {
        "resumo",
        "gols_por_temporada",
        "distribuicao_resultados",
        "pontos_por_equipe",
    }
    resumo = json.loads(caminhos["resumo"].read_text(encoding="utf-8"))
    assert resumo == resumo_exploratorio(base_sintetica)
    for chave in ("gols_por_temporada", "distribuicao_resultados", "pontos_por_equipe"):
        dados = caminhos[chave].read_bytes()
        assert dados.startswith(PNG)
        assert len(dados) > 2000


def test_exportacao_do_resumo_e_reproduzivel(tmp_path, base_sintetica):
    primeira = exportar_analise(base_sintetica, tmp_path / "a")["resumo"]
    segunda = exportar_analise(base_sintetica, tmp_path / "b")["resumo"]
    assert primeira.read_bytes() == segunda.read_bytes()
