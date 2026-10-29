import hashlib
import socket
from pathlib import Path

import pytest

from ingestion.coleta import (
    CAMPOS_LIDOS,
    ColetaErro,
    copiar_bruto,
    ler_partidas,
    selecionar_fonte,
    verificar_mapeamento,
)
from ingestion.source_catalog import CatalogoFontes, construir_catalogo

MAPEAMENTO = {
    "partida_id": "id",
    "data_partida": "data",
    "temporada": "temporada",
    "competicao": "competicao",
    "equipe_mandante": "mandante",
    "equipe_visitante": "visitante",
    "gols_mandante": "gols_m",
    "gols_visitante": "gols_v",
    "resultado": "resultado_fonte",
    "rodada": "rodada",
    "finalizacoes": "nao_usado",
    "finalizacoes_no_alvo": "nao_usado",
    "posse_de_bola": "nao_usado",
    "cartoes": "nao_usado",
    "escanteios": "nao_usado",
    "xg": "nao_usado",
    "dias_descanso": "nao_usado",
    "outras_estatisticas": "nao_usado",
}

CSV_VALIDO = (
    "id,data,temporada,competicao,mandante,visitante,gols_m,gols_v,rodada\n"
    "1,2024-05-04,2024,Brasileirão,Flamengo,Atlético-MG,2,1,1\n"
    "2,04/05/2024,2024,Brasileirão,Atlético MG,Flamengo,0,0,1\n"
    "3,11/05/2024,2024,Brasileirão,Grêmio,Palmeiras,1,3,2\n"
)


@pytest.fixture(autouse=True)
def _bloquear_rede(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("rede não permitida em teste")

    monkeypatch.setattr(socket, "socket", proibido)
    monkeypatch.setattr(socket, "create_connection", proibido)
    monkeypatch.setattr(socket, "getaddrinfo", proibido)


def _catalogo(selecionada: bool = True, mapeamento: dict | None = None) -> CatalogoFontes:
    fonte = {
        "id": "fonte_teste",
        "nome": "Fonte sintética",
        "url": "https://exemplo.invalid/fonte",
        "licenca": "licença de teste",
        "status_licenca": "verificada" if selecionada else "pendente_verificacao",
        "cobertura_brasileirao": "sintética",
        "temporadas": "sintética",
        "campos_essenciais": ["id"],
        "campos_complementares": [],
        "riscos": ["dados sintéticos para teste"],
        "decisao": "selecionada" if selecionada else "pendente",
        "mapeamento": dict(mapeamento or MAPEAMENTO),
    }
    if selecionada:
        fonte.update(
            url_termos="https://exemplo.invalid/termos",
            data_verificacao="2026-10-29",
            verificador="teste automatizado",
            justificativa="teste automatizado",
        )
    return construir_catalogo({"catalogo": {"versao": "0.0.0-teste"}, "fontes": [fonte]})


def _csv(tmp_path: Path, conteudo: str = CSV_VALIDO, nome: str = "partidas.csv") -> Path:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_selecionar_fonte_recusa_catalogo_sem_selecao():
    with pytest.raises(ColetaErro, match="nenhuma fonte selecionada"):
        selecionar_fonte(_catalogo(selecionada=False))


def test_selecionar_fonte_devolve_a_fonte_selecionada():
    assert selecionar_fonte(_catalogo()).id == "fonte_teste"


def test_verificar_mapeamento_recusa_campo_a_verificar():
    fonte = selecionar_fonte(_catalogo(mapeamento={**MAPEAMENTO, "partida_id": "a verificar"}))
    with pytest.raises(ColetaErro, match="partida_id"):
        verificar_mapeamento(fonte)


def test_ler_partidas_usa_mapeamento_e_preserva_ausencias(tmp_path):
    fonte = selecionar_fonte(_catalogo())
    conteudo = "id,data,temporada,competicao,mandante,visitante,gols_m,gols_v,rodada\n"
    conteudo += "7,2024-05-04,2024,,Flamengo,Grêmio,2,1,\n"
    linhas = ler_partidas(_csv(tmp_path, conteudo), fonte)
    assert len(linhas) == 1
    assert linhas[0]["partida_id"] == "7"
    assert linhas[0]["equipe_mandante"] == "Flamengo"
    assert linhas[0]["competicao"] is None
    assert linhas[0]["rodada"] is None
    assert set(linhas[0]) == set(CAMPOS_LIDOS)


def test_ler_partidas_recusa_cabecalho_sem_coluna_mapeada(tmp_path):
    fonte = selecionar_fonte(_catalogo())
    with pytest.raises(ColetaErro, match="colunas mapeadas"):
        ler_partidas(_csv(tmp_path, "id,data\n1,2024-05-04\n"), fonte)


def test_ler_partidas_recusa_arquivo_inexistente(tmp_path):
    with pytest.raises(ColetaErro, match="não encontrado"):
        ler_partidas(tmp_path / "nao_existe.csv", selecionar_fonte(_catalogo()))


def test_copiar_bruto_grava_copia_identica_em_pasta_raw(tmp_path):
    fonte = selecionar_fonte(_catalogo())
    origem = _csv(tmp_path)
    pasta_raw = tmp_path / "raw"
    destino = copiar_bruto(origem, fonte, pasta_raw)
    assert destino.parent == pasta_raw
    assert destino.name.startswith("fonte_teste_")
    assert destino.read_bytes() == origem.read_bytes()
    digest = hashlib.sha256(origem.read_bytes()).hexdigest()
    assert digest[:12] in destino.name
    assert list(pasta_raw.glob("*.tmp")) == []


def test_copiar_bruto_recusa_origem_inexistente(tmp_path):
    with pytest.raises(ColetaErro, match="não encontrado"):
        copiar_bruto(tmp_path / "x.csv", selecionar_fonte(_catalogo()), tmp_path / "raw")
    assert not (tmp_path / "raw").exists()
