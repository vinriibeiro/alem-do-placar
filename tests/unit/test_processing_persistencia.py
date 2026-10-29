from datetime import date

import pyarrow.parquet as pq
import pytest

from processing.persistencia import ESQUEMAS, escrever_tabela

LINHAS_EQUIPES = [
    {"equipe_id": 2, "nome": "Flamengo", "nome_padronizado": "Flamengo"},
    {"equipe_id": 1, "nome": "Atlético Mineiro", "nome_padronizado": "Atlético Mineiro"},
]

LINHAS_PARTIDAS = [
    {
        "partida_id": "b",
        "data_partida": date(2024, 5, 11),
        "temporada_id": 1,
        "equipe_mandante_id": 1,
        "equipe_visitante_id": 2,
        "gols_mandante": 0,
        "gols_visitante": 1,
        "resultado": "A",
    },
]


def test_escrever_tabela_grava_parquet_legivel_e_ordenado(tmp_path):
    destino = escrever_tabela("dim_equipes", LINHAS_EQUIPES, tmp_path)
    assert destino == tmp_path / "dim_equipes.parquet"
    tabela = pq.read_table(destino)
    assert tabela.column("equipe_id").to_pylist() == [1, 2]
    assert tabela.schema.names == list(ESQUEMAS["dim_equipes"].names)


def test_mesma_entrada_produz_bytes_identicos(tmp_path):
    antes = escrever_tabela("dim_equipes", LINHAS_EQUIPES, tmp_path / "a")
    depois = escrever_tabela("dim_equipes", list(reversed(LINHAS_EQUIPES)), tmp_path / "b")
    assert antes.read_bytes() == depois.read_bytes()


def test_ordenacao_por_data_e_partida_independe_da_entrada(tmp_path):
    linhas = [dict(LINHAS_PARTIDAS[0], partida_id="a", data_partida=date(2024, 5, 4))]
    misturadas = linhas + list(LINHAS_PARTIDAS)
    destino = escrever_tabela("fato_partidas", misturadas, tmp_path)
    tabela = pq.read_table(destino)
    assert tabela.column("partida_id").to_pylist() == ["a", "b"]


def test_escrita_atomica_nao_deixa_temporarios(tmp_path):
    escrever_tabela("dim_equipes", LINHAS_EQUIPES, tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["dim_equipes.parquet"]


def test_tabela_desconhecida_e_recusada(tmp_path):
    with pytest.raises(ValueError, match="tabela desconhecida"):
        escrever_tabela("tabela_inexistente", [], tmp_path)
