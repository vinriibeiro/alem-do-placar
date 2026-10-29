"""Persistência das tabelas em Parquet, com ordenação estável e escrita atômica (T003).

Os esquemas são explícitos e não há timestamps no arquivo, de modo que a mesma entrada gera
arquivos de conteúdo idêntico. A escrita passa por arquivo temporário seguido de ``os.replace``.
"""

import os
from collections.abc import Mapping, Sequence
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ESQUEMAS: Mapping[str, pa.Schema] = {
    "dim_equipes": pa.schema(
        [
            pa.field("equipe_id", pa.int64(), nullable=False),
            pa.field("nome", pa.string(), nullable=False),
            pa.field("nome_padronizado", pa.string(), nullable=False),
        ]
    ),
    "dim_temporadas": pa.schema(
        [
            pa.field("temporada_id", pa.int64(), nullable=False),
            pa.field("ano", pa.int64(), nullable=False),
            pa.field("competicao", pa.string(), nullable=False),
        ]
    ),
    "fato_partidas": pa.schema(
        [
            pa.field("partida_id", pa.string(), nullable=False),
            pa.field("data_partida", pa.date32(), nullable=False),
            pa.field("temporada_id", pa.int64(), nullable=False),
            pa.field("equipe_mandante_id", pa.int64(), nullable=False),
            pa.field("equipe_visitante_id", pa.int64(), nullable=False),
            pa.field("gols_mandante", pa.int64(), nullable=False),
            pa.field("gols_visitante", pa.int64(), nullable=False),
            pa.field("resultado", pa.string(), nullable=False),
        ]
    ),
    "fato_desempenho_equipes": pa.schema(
        [
            pa.field("partida_id", pa.string(), nullable=False),
            pa.field("equipe_id", pa.int64(), nullable=False),
            pa.field("pontos", pa.int64(), nullable=False),
            pa.field("gols_pro", pa.int64(), nullable=False),
            pa.field("gols_contra", pa.int64(), nullable=False),
            pa.field("saldo_gols", pa.int64(), nullable=False),
            pa.field("mando_campo", pa.string(), nullable=False),
            pa.field("rodada", pa.int64(), nullable=True),
        ]
    ),
}

CHAVES_ORDENACAO: Mapping[str, tuple[str, ...]] = {
    "dim_equipes": ("equipe_id",),
    "dim_temporadas": ("temporada_id",),
    "fato_partidas": ("data_partida", "partida_id"),
    "fato_desempenho_equipes": ("partida_id", "mando_campo"),
}


def escrever_tabela(nome: str, linhas: Sequence[Mapping[str, object]], pasta: Path) -> Path:
    """Ordena as linhas pela chave da tabela e grava ``<nome>.parquet`` de forma atômica."""
    if nome not in ESQUEMAS:
        raise ValueError(f"tabela desconhecida: {nome}")
    chaves = CHAVES_ORDENACAO[nome]
    ordenadas = sorted(linhas, key=lambda linha: tuple(linha[c] for c in chaves))
    tabela = pa.Table.from_pylist(ordenadas, schema=ESQUEMAS[nome])
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{nome}.parquet"
    temporario = pasta / f"{nome}.parquet.tmp"
    try:
        pq.write_table(tabela, str(temporario), compression="snappy")
        os.replace(temporario, destino)
    except BaseException:
        temporario.unlink(missing_ok=True)
        raise
    return destino
