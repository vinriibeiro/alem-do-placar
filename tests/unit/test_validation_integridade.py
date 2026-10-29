from datetime import date

import pytest

from processing.padronizacao import Partida
from validation.integridade import (
    IntegridadeErro,
    RelatorioIntegridade,
    Severidade,
    levantar_se_critico,
    validar_desempenho,
    validar_partidas,
)


def _partida(**campos) -> Partida:
    base = {
        "partida_id": "1",
        "data_partida": date(2024, 5, 4),
        "temporada": 2024,
        "competicao": "Brasileirão",
        "mandante": "Flamengo",
        "visitante": "Palmeiras",
        "gols_mandante": 2,
        "gols_visitante": 1,
        "rodada": 1,
    }
    return Partida(**{**base, **campos})


def _regras(achados) -> set[str]:
    return {achado.regra for achado in achados}


def _severidade(achados, mensagem_parcial: str) -> Severidade:
    (achado,) = [a for a in achados if mensagem_parcial in a.mensagem]
    return achado.severidade


def test_partida_valida_nao_gera_achados():
    assert validar_partidas([_partida()]) == []


def test_partida_duplicada_e_critica():
    achados = validar_partidas([_partida(), _partida()])
    assert "partida_duplicada" in _regras(achados)
    assert _severidade(achados, "partida_id duplicado") is Severidade.CRITICO


def test_mandante_igual_ao_visitante_e_critico():
    achados = validar_partidas([_partida(visitante="Flamengo")])
    assert "mandante_igual_visitante" in _regras(achados)
    assert _severidade(achados, "mandante igual") is Severidade.CRITICO


def test_gols_negativos_ou_nao_inteiros_sao_criticos():
    assert "gols_negativos" in _regras(validar_partidas([_partida(gols_mandante=-1)]))
    assert "gols_nao_inteiros" in _regras(validar_partidas([_partida(gols_visitante=1.5)]))


def test_ausencias_sao_listadas_com_severidade_propria():
    achados = validar_partidas([_partida(gols_visitante=None, rodada=None)])
    assert _severidade(achados, "'gols_visitante' ausente") is Severidade.CRITICO
    assert _severidade(achados, "'rodada' ausente") is Severidade.AVISO


def test_pontos_fora_da_regra_sao_criticos():
    linhas = [
        {"partida_id": "1", "equipe_id": 1, "pontos": 2},
        {"partida_id": "1", "equipe_id": 2, "pontos": 0},
    ]
    assert "pontos_invalidos" in _regras(validar_desempenho(linhas))


def test_observacoes_diferentes_de_duas_por_partida_sao_criticas():
    linhas = [{"partida_id": "1", "equipe_id": 1, "pontos": 3}]
    assert "observacoes_por_partida" in _regras(validar_desempenho(linhas))


def test_desempenho_valido_nao_gera_achados():
    linhas = [
        {"partida_id": "1", "equipe_id": 1, "pontos": 3},
        {"partida_id": "1", "equipe_id": 2, "pontos": 0},
    ]
    assert validar_desempenho(linhas) == []


def test_levantar_se_critico_interrompe_com_relatorio():
    relatorio = RelatorioIntegridade(tuple(validar_partidas([_partida(gols_mandante=-1)])))
    with pytest.raises(IntegridadeErro) as info:
        levantar_se_critico(relatorio)
    assert info.value.relatorio is relatorio


def test_avisos_nao_interrompem():
    relatorio = RelatorioIntegridade(tuple(validar_partidas([_partida(rodada=None)])))
    levantar_se_critico(relatorio)
    assert relatorio.avisos
    assert relatorio.criticos == ()
