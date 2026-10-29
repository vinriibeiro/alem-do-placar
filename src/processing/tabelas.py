"""Tabelas analíticas do PRD 5.1: dimensões e fatos de partidas e desempenho (T003).

Cada partida gera duas observações de desempenho, uma por equipe. Os pontos seguem a regra
3/1/0 (PRD 5.2). Espera partidas já validadas por ``validation.integridade``.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence

from processing.padronizacao import Partida, normalizar_texto

PONTOS_VITORIA = 3
PONTOS_EMPATE = 1
PONTOS_DERROTA = 0

PONTOS_POR_RESULTADO = {
    "H": (PONTOS_VITORIA, PONTOS_DERROTA),
    "D": (PONTOS_EMPATE, PONTOS_EMPATE),
    "A": (PONTOS_DERROTA, PONTOS_VITORIA),
}


def gerar_tabelas(partidas: Sequence[Partida]) -> dict[str, list[dict[str, object]]]:
    """Gera dim_equipes, dim_temporadas, fato_partidas e fato_desempenho_equipes."""
    equipes = _ids_equipes(partidas)
    temporadas = _ids_temporadas(partidas)
    return {
        "dim_equipes": _dim_equipes(equipes),
        "dim_temporadas": [
            {"temporada_id": tid, "ano": ano, "competicao": competicao}
            for (ano, competicao), tid in temporadas.items()
        ],
        "fato_partidas": [
            {
                "partida_id": p.partida_id,
                "data_partida": p.data_partida,
                "temporada_id": temporadas[_chave_temporada(p)],
                "equipe_mandante_id": equipes[p.mandante],
                "equipe_visitante_id": equipes[p.visitante],
                "gols_mandante": p.gols_mandante,
                "gols_visitante": p.gols_visitante,
                "resultado": p.resultado,
            }
            for p in partidas
        ],
        "fato_desempenho_equipes": [linha for p in partidas for linha in _desempenho(p, equipes)],
    }


def _ids_equipes(partidas: Sequence[Partida]) -> dict[str, int]:
    nomes = {n for p in partidas for n in (p.mandante, p.visitante) if n is not None}
    return {nome: _id_estavel("equipe", normalizar_texto(nome)) for nome in sorted(nomes)}


def _dim_equipes(equipes: Mapping[str, int]) -> list[dict[str, object]]:
    """Uma linha por identidade, mantendo o nome de exibição separado do ID."""
    nomes_por_id: dict[int, str] = {}
    for nome, eid in equipes.items():
        nomes_por_id.setdefault(eid, nome)
    return [
        {"equipe_id": eid, "nome": nome, "nome_padronizado": nome}
        for eid, nome in sorted(nomes_por_id.items(), key=lambda item: item[1])
    ]


def _id_estavel(tipo: str, *valores: object) -> int:
    """ID determinístico de 63 bits, independente do lote ou temporada processada."""
    chave = json.dumps([tipo, *valores], ensure_ascii=False, separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(chave.encode("utf-8")).digest()[:8], "big") >> 1


def _chave_temporada(partida: Partida) -> tuple[int, str]:
    if partida.temporada is None or not partida.competicao:
        raise ValueError("temporada e competicao são obrigatórias para gerar tabelas")
    return (partida.temporada, partida.competicao)


def _ids_temporadas(partidas: Sequence[Partida]) -> dict[tuple[int, str], int]:
    chaves = sorted({_chave_temporada(p) for p in partidas})
    return {chave: _id_estavel("temporada", *chave) for chave in chaves}


def _desempenho(partida: Partida, equipes: Mapping[str, int]) -> list[dict[str, object]]:
    pontos_mandante, pontos_visitante = PONTOS_POR_RESULTADO[partida.resultado or "D"]
    gm = partida.gols_mandante or 0
    gv = partida.gols_visitante or 0
    return [
        {
            "partida_id": partida.partida_id,
            "equipe_id": equipes[partida.mandante or ""],
            "pontos": pontos_mandante,
            "gols_pro": gm,
            "gols_contra": gv,
            "saldo_gols": gm - gv,
            "mando_campo": "mandante",
            "rodada": partida.rodada,
        },
        {
            "partida_id": partida.partida_id,
            "equipe_id": equipes[partida.visitante or ""],
            "pontos": pontos_visitante,
            "gols_pro": gv,
            "gols_contra": gm,
            "saldo_gols": gv - gm,
            "mando_campo": "visitante",
            "rodada": partida.rodada,
        },
    ]
