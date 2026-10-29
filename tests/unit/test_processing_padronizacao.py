from datetime import date

import pytest

from processing.padronizacao import (
    PadronizacaoErro,
    Partida,
    normalizar_texto,
    padronizar_data,
    padronizar_equipe,
    padronizar_partidas,
)

FORMATOS = ("%Y-%m-%d", "%d/%m/%Y")


def _partida(gols_mandante: int | None = 1, gols_visitante: int | None = 0) -> Partida:
    return Partida(
        partida_id="1",
        data_partida=date(2024, 5, 4),
        temporada=2024,
        competicao="Brasileirão",
        mandante="Flamengo",
        visitante="Palmeiras",
        gols_mandante=gols_mandante,
        gols_visitante=gols_visitante,
        rodada=1,
    )


def _linha(**campos: str | None) -> dict[str, str | None]:
    base: dict[str, str | None] = {
        "partida_id": "1",
        "data_partida": "2024-05-04",
        "temporada": "2024",
        "competicao": "Brasileirão",
        "equipe_mandante": "Gremio",
        "equipe_visitante": "Palmeiras",
        "gols_mandante": "1",
        "gols_visitante": "3",
        "rodada": "2",
    }
    return {**base, **campos}


def test_normalizar_texto_remove_acento_e_pontuacao():
    assert normalizar_texto("  Atlético-MG ") == "atletico mg"
    assert normalizar_texto("Grêmio FBPA") == "gremio fbpa"


def test_padronizar_equipe_aplica_aliases():
    assert padronizar_equipe("Atletico-MG") == "Atlético Mineiro"
    assert padronizar_equipe("Gremio") == "Grêmio"
    assert padronizar_equipe("CR  Flamengo") == "Flamengo"


def test_padronizar_equipe_sem_alias_mantem_nome_com_espacos_normalizados():
    assert padronizar_equipe("  Coritiba   FC ") == "Coritiba FC"


def test_datas_iso_e_brasileira_resultam_na_mesma_data():
    assert padronizar_data("2024-05-04", FORMATOS) == date(2024, 5, 4)
    assert padronizar_data("04/05/2024", FORMATOS) == date(2024, 5, 4)


def test_data_fora_dos_formatos_e_recusada():
    with pytest.raises(PadronizacaoErro):
        padronizar_data("2024/05/04", FORMATOS)


def test_resultado_derivado_dos_gols():
    assert _partida(2, 1).resultado == "H"
    assert _partida(1, 1).resultado == "D"
    assert _partida(0, 3).resultado == "A"
    assert _partida(None, 1).resultado is None


def test_padronizar_partidas_aplica_aliases_e_resultado():
    (partida,) = padronizar_partidas([_linha()], FORMATOS)
    assert partida.mandante == "Grêmio"
    assert partida.visitante == "Palmeiras"
    assert partida.data_partida == date(2024, 5, 4)
    assert partida.resultado == "A"


def test_padronizar_partidas_preserva_ausencias_sem_preencher():
    linha = _linha(competicao=None, rodada="", gols_visitante=None)
    (partida,) = padronizar_partidas([linha], FORMATOS)
    assert partida.competicao is None
    assert partida.rodada is None
    assert partida.gols_visitante is None
    assert partida.resultado is None


def test_padronizar_partidas_recusa_gols_nao_inteiros():
    with pytest.raises(PadronizacaoErro, match="gols_mandante"):
        padronizar_partidas([_linha(gols_mandante="1,5")], FORMATOS)
