from dataclasses import replace
from datetime import date

from processing.padronizacao import Partida
from processing.tabelas import gerar_tabelas


def _partidas() -> list[Partida]:
    return [
        Partida(
            "1", date(2024, 5, 4), 2024, "Brasileirão", "Flamengo", "Atlético Mineiro", 2, 1, 1
        ),
        Partida("2", date(2024, 5, 11), 2024, "Brasileirão", "Grêmio", "Palmeiras", 1, 3, 2),
        Partida("3", date(2024, 5, 18), 2024, "Brasileirão", "Palmeiras", "Flamengo", 1, 1, 3),
    ]


def _linha(tabela: list[dict], partida_id: str, mando: str) -> dict:
    (linha,) = [t for t in tabela if t["partida_id"] == partida_id and t["mando_campo"] == mando]
    return linha


def test_dim_equipes_tem_ids_unicos_e_nomes_ordenados():
    dim = gerar_tabelas(_partidas())["dim_equipes"]
    assert [d["nome_padronizado"] for d in dim] == [
        "Atlético Mineiro",
        "Flamengo",
        "Grêmio",
        "Palmeiras",
    ]
    assert len({d["equipe_id"] for d in dim}) == 4
    assert all(0 <= d["equipe_id"] < 2**63 for d in dim)


def test_dim_temporadas_e_fato_partidas_usam_ids_das_dimensoes():
    tabelas = gerar_tabelas(_partidas())
    (temporada,) = tabelas["dim_temporadas"]
    assert temporada["ano"] == 2024
    assert temporada["competicao"] == "Brasileirão"
    equipes = {d["nome"]: d["equipe_id"] for d in tabelas["dim_equipes"]}
    primeira = tabelas["fato_partidas"][0]
    assert primeira["temporada_id"] == temporada["temporada_id"]
    assert primeira["equipe_mandante_id"] == equipes["Flamengo"]
    assert primeira["equipe_visitante_id"] == equipes["Atlético Mineiro"]
    assert primeira["resultado"] == "H"


def test_ids_estaveis_entre_lotes_com_equipes_e_temporadas_diferentes():
    primeira = _partidas()[0]
    lote_a = gerar_tabelas([replace(primeira, visitante="Palmeiras")])
    lote_b = gerar_tabelas(
        [
            replace(primeira, temporada=2023, mandante="Atlético Mineiro", visitante="Flamengo"),
            primeira,
        ]
    )
    ids_a = {d["nome"]: d["equipe_id"] for d in lote_a["dim_equipes"]}
    ids_b = {d["nome"]: d["equipe_id"] for d in lote_b["dim_equipes"]}
    assert ids_a["Flamengo"] == ids_b["Flamengo"]
    assert lote_a["fato_partidas"][0]["temporada_id"] == lote_b["fato_partidas"][1]["temporada_id"]


def test_equipes_sem_alias_tem_identidade_estavel_e_dimensao_sem_duplicatas():
    partida = replace(_partidas()[0], mandante="Corinthians", visitante="Athletico-PR")
    variante = replace(
        partida, partida_id="outra", mandante="CORINTHIANS", visitante="ÁTHLETICO PR"
    )
    lote_a = gerar_tabelas([partida])
    lote_b = gerar_tabelas([variante])
    conjunto = gerar_tabelas([partida, variante])
    assert (
        lote_a["fato_partidas"][0]["equipe_mandante_id"]
        == lote_b["fato_partidas"][0]["equipe_mandante_id"]
    )
    assert (
        lote_a["fato_partidas"][0]["equipe_visitante_id"]
        == lote_b["fato_partidas"][0]["equipe_visitante_id"]
    )
    assert len(conjunto["dim_equipes"]) == 2
    assert any(d["nome"] == "Corinthians" for d in lote_a["dim_equipes"])


def test_desempenho_tem_duas_observacoes_por_partida_com_pontos_310():
    desempenho = gerar_tabelas(_partidas())["fato_desempenho_equipes"]
    assert len(desempenho) == 6
    assert _linha(desempenho, "1", "mandante")["pontos"] == 3
    assert _linha(desempenho, "1", "visitante")["pontos"] == 0
    assert _linha(desempenho, "2", "mandante")["pontos"] == 0
    assert _linha(desempenho, "2", "visitante")["pontos"] == 3
    assert _linha(desempenho, "3", "mandante")["pontos"] == 1
    assert _linha(desempenho, "3", "visitante")["pontos"] == 1


def test_saldo_de_gols_e_simetrico_por_partida():
    desempenho = gerar_tabelas(_partidas())["fato_desempenho_equipes"]
    for partida_id in ("1", "2", "3"):
        mandante = _linha(desempenho, partida_id, "mandante")
        visitante = _linha(desempenho, partida_id, "visitante")
        assert mandante["saldo_gols"] == -visitante["saldo_gols"]
        assert mandante["gols_pro"] == visitante["gols_contra"]
