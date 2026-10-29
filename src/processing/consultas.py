"""Consultas analíticas em DuckDB, em memória e somente leitura (T003; PRD 9.4).

As consultas são um catálogo fixo, com parâmetros passados por ``?``. Nenhum SQL vem de
entrada externa e nenhum arquivo ``.duckdb`` é criado.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from processing.persistencia import ESQUEMAS

TABELAS = tuple(ESQUEMAS)

CONSULTAS: Mapping[str, str] = {
    "pontos_por_equipe": """
        SELECT e.nome_padronizado AS equipe,
               COUNT(*) AS partidas,
               SUM(d.pontos) AS pontos,
               SUM(d.gols_pro) AS gols_pro,
               SUM(d.gols_contra) AS gols_contra
        FROM fato_desempenho_equipes AS d
        JOIN dim_equipes AS e ON e.equipe_id = d.equipe_id
        JOIN fato_partidas AS p ON p.partida_id = d.partida_id
        JOIN dim_temporadas AS t ON t.temporada_id = p.temporada_id
        WHERE t.ano = ?
        GROUP BY e.nome_padronizado
        ORDER BY pontos DESC, equipe ASC
    """,
    "partidas_por_temporada": """
        SELECT t.ano, t.competicao, COUNT(*) AS partidas
        FROM fato_partidas AS p
        JOIN dim_temporadas AS t ON t.temporada_id = p.temporada_id
        GROUP BY t.ano, t.competicao
        ORDER BY t.ano, t.competicao
    """,
}


def executar_consulta(
    pasta: Path, nome: str, parametros: Sequence[object] = ()
) -> list[dict[str, object]]:
    """Executa uma consulta autorizada sobre os Parquet de ``pasta``, em memória."""
    if nome not in CONSULTAS:
        raise KeyError(f"consulta não autorizada: {nome}")
    conexao = duckdb.connect(":memory:")
    try:
        for tabela in TABELAS:
            conexao.register(tabela, pq.read_table(str(pasta / f"{tabela}.parquet")))
        resultado = conexao.execute(CONSULTAS[nome], list(parametros))
        colunas = [descricao[0] for descricao in resultado.description]
        return [dict(zip(colunas, linha, strict=True)) for linha in resultado.fetchall()]
    finally:
        conexao.close()
