"""Testes do adaptador OpenFootball (T003). Textos sintéticos, sem rede e sem dados reais."""

import csv
from pathlib import Path

import pytest

from ingestion.coleta import ler_partidas
from ingestion.openfootball import (
    COLUNAS_CSV,
    ConversaoErro,
    converter_temporada,
    gerar_partida_id,
    gravar_csv,
)
from ingestion.source_catalog import CAMPOS_PRD, StatusLicenca, carregar_catalogo

RAIZ = Path(__file__).resolve().parents[2]
PERFIL = RAIZ / "config" / "approved_source.toml"
URL_TERMOS = (
    "https://github.com/openfootball/south-america/blob/"
    "f51b2dcf5e0fab9f0abd5206ab8c24a413e67277/LICENSE.md"
)

TEXTO_2024 = """\
= Brasileiro Série A 2024

▪ Matchday 1
  Sat Apr 13 2024
    18:30  SC Internacional        v EC Bahia                 2-1 (0-0)
           Criciúma EC             v EC Juventude             1-1 (1-0)
  Sun Apr 14
    16:00  Palmeiras               v Flamengo RJ              0-0
"""

TEXTO_2020 = """\
= Brasileiro Série A 2020

▪ Matchday 38
  Sat Jan 16
    16:00  Fluminense FC       v Fortaleza CE       1-0 (0-0)
  Sun Dec 13
    16:00  Cruzeiro            v Goiás GO           2-2
"""

TEXTO_REMARCACAO_2024 = """\
= Brasileiro Série A 2024

▪ Matchday 10
  Sat Apr 13
    16:00  Grêmio FBPA v Fluminense FC 1-0
  Sat Dec 14
    16:00  Cruzeiro v Atlético Mineiro 0-1
  Wed Apr 10
    20:00  Bahia BA v Vasco da Gama RJ 3-0
"""

JOGOS_MESMA_DATA = """\
= Brasileiro Série A 2024

▪ Matchday 2
  Sat Apr 20
    16:00  Fortaleza CE v Goiás GO 1-0
    18:30  Cruzeiro v Palmeiras 0-0
"""

JOGOS_REORDENADOS = """\
# comentário sem efeito

= Brasileiro Série A 2024


▪ Matchday 2
  Sat Apr 20
    18:30  Cruzeiro v Palmeiras 0-0
    16:00  Fortaleza CE v Goiás GO 1-0
"""


def _sem_id(linha: dict[str, str]) -> dict[str, str]:
    return {campo: valor for campo, valor in linha.items() if campo != "partida_id"}


def test_converte_cabecalho_rodada_datas_e_aliases():
    linhas = converter_temporada(TEXTO_2024, 2024)

    assert [_sem_id(linha) for linha in linhas] == [
        {
            "data_partida": "2024-04-13",
            "temporada": "2024",
            "competicao": "Brasileiro Série A",
            "equipe_mandante": "SC Internacional",
            "equipe_visitante": "EC Bahia",
            "gols_mandante": "2",
            "gols_visitante": "1",
            "rodada": "1",
        },
        {
            "data_partida": "2024-04-13",
            "temporada": "2024",
            "competicao": "Brasileiro Série A",
            "equipe_mandante": "Criciúma EC",
            "equipe_visitante": "EC Juventude",
            "gols_mandante": "1",
            "gols_visitante": "1",
            "rodada": "1",
        },
        {
            "data_partida": "2024-04-14",
            "temporada": "2024",
            "competicao": "Brasileiro Série A",
            "equipe_mandante": "SE Palmeiras",
            "equipe_visitante": "CR Flamengo",
            "gols_mandante": "0",
            "gols_visitante": "0",
            "rodada": "1",
        },
    ]
    assert all(len(linha["partida_id"]) == 64 for linha in linhas)
    assert tuple(linhas[0]) == COLUNAS_CSV


def test_linha_desconhecida_falha_com_numero_da_linha():
    texto = "= Brasileiro Série A 2024\n  Sat Apr 13 2024\n    texto solto sem placar\n"
    with pytest.raises(ConversaoErro, match="linha 3"):
        converter_temporada(texto, 2024)


def test_placar_nao_interpretado_falha_e_nao_some():
    texto = "= Brasileiro Série A 2024\n  Sat Apr 13 2024\n    Time A v Time B 2-x\n"
    with pytest.raises(ConversaoErro, match="linha 3"):
        converter_temporada(texto, 2024)


def test_partida_sem_cabecalho_ou_data_falha():
    with pytest.raises(ConversaoErro, match="antes do cabeçalho"):
        converter_temporada("  Sat Apr 13 2024\n    A v B 1-0\n", 2024)
    with pytest.raises(ConversaoErro, match="antes de qualquer data"):
        converter_temporada("= Brasileiro Série A 2024\n    A v B 1-0\n", 2024)


def test_cabecalho_de_outra_temporada_falha():
    with pytest.raises(ConversaoErro, match="cabeçalho de 2024"):
        converter_temporada(TEXTO_2024, 2023)


def test_comentarios_e_linhas_vazias_nao_viram_partidas():
    texto = "# comentário\n\n" + TEXTO_2024 + "\n# fim\n"
    assert len(converter_temporada(texto, 2024)) == 3


def test_2020_janeiro_e_fevereiro_pertencem_a_2021():
    linhas = converter_temporada(TEXTO_2020, 2020)

    assert [linha["data_partida"] for linha in linhas] == ["2021-01-16", "2020-12-13"]
    assert linhas[1]["equipe_mandante"] == "Cruzeiro EC"
    assert linhas[1]["equipe_visitante"] == "Goiás EC"


def test_data_com_ano_explicito_prevalece():
    texto = "= Brasileiro Série A 2024\n  Sat Jan 04 2025\n    16:00  A v B 1-0\n"
    assert converter_temporada(texto, 2024)[0]["data_partida"] == "2025-01-04"


def test_remarcacao_fora_de_ordem_nao_inferre_virada_de_ano():
    linhas = converter_temporada(TEXTO_REMARCACAO_2024, 2024)

    assert [linha["data_partida"] for linha in linhas] == [
        "2024-04-13",
        "2024-12-14",
        "2024-04-10",
    ]
    assert {linha["rodada"] for linha in linhas} == {"10"}


def test_alias_e_unificado_entre_epocas():
    antigo = converter_temporada(
        "= Brasileiro Série A 2018\n\n▪ Matchday 1\n  Sat Apr 28\n"
        "    16:00  CA Mineiro v Cruzeiro EC 1-0\n",
        2018,
    )[0]
    recente = converter_temporada(
        "= Brasileiro Série A 2024\n\n▪ Matchday 1\n  Sat Apr 28\n"
        "    16:00  Atlético Mineiro v Cruzeiro 2-0\n",
        2024,
    )[0]

    assert antigo["equipe_mandante"] == recente["equipe_mandante"] == "Atlético Mineiro"
    assert antigo["equipe_visitante"] == recente["equipe_visitante"] == "Cruzeiro EC"
    assert antigo["partida_id"] != recente["partida_id"]


def test_id_independe_da_ordem_e_do_numero_da_linha():
    original = converter_temporada(JOGOS_MESMA_DATA, 2024)
    reordenado = converter_temporada(JOGOS_REORDENADOS, 2024)

    assert len(original) == 2
    assert {linha["partida_id"]: _sem_id(linha) for linha in original} == {
        linha["partida_id"]: _sem_id(linha) for linha in reordenado
    }


def test_gerar_partida_id_normaliza_equipes_e_inclui_temporada():
    referencia = gerar_partida_id(2024, "2024-04-13", "Atlético Mineiro", "EC Bahia")

    assert referencia == gerar_partida_id(2024, "2024-04-13", "ATLETICO  MINEIRO", "EC Bahia")
    assert referencia != gerar_partida_id(2025, "2024-04-13", "Atlético Mineiro", "EC Bahia")


def test_mandante_igual_ao_visitante_falha():
    texto = (
        "= Brasileiro Série A 2024\n"
        "  Sat Apr 13 2024\n"
        "    16:00  CA Mineiro v Atlético Mineiro 1-0\n"
    )
    with pytest.raises(ConversaoErro, match="iguais"):
        converter_temporada(texto, 2024)


def test_partida_duplicada_falha():
    linha = "    16:00  Cruzeiro v Palmeiras 0-0\n"
    texto = "= Brasileiro Série A 2024\n  Sat Apr 13 2024\n" + linha + linha
    with pytest.raises(ConversaoErro, match="duplicada"):
        converter_temporada(texto, 2024)


@pytest.mark.parametrize("temporada", [2015, 2017, 2026])
def test_temporada_fora_do_escopo_falha(temporada):
    with pytest.raises(ConversaoErro, match="fora do escopo"):
        converter_temporada(TEXTO_2024, temporada)


def test_csv_roundtrip_preserva_linhas(tmp_path):
    linhas = converter_temporada(TEXTO_2024, 2024)
    caminho = gravar_csv(linhas, tmp_path / "partidas_2024.csv")

    with caminho.open(encoding="utf-8", newline="") as arquivo:
        cabecalho = next(csv.reader(arquivo))
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        lidas = list(csv.DictReader(arquivo))

    assert cabecalho == list(COLUNAS_CSV)
    assert lidas == linhas


def test_csv_e_lido_pelo_mapeamento_do_perfil(tmp_path):
    caminho = gravar_csv(converter_temporada(TEXTO_2024, 2024), tmp_path / "partidas_2024.csv")
    fonte = carregar_catalogo(PERFIL).buscar("openfootball_2018_2025")

    lidas = ler_partidas(caminho, fonte)

    assert lidas[0]["equipe_mandante"] == "SC Internacional"
    assert lidas[0]["rodada"] == "1"


def test_perfil_aprovado_carrega_com_licenca_verificavel():
    catalogo = carregar_catalogo(PERFIL)
    fonte = catalogo.fonte_selecionada()

    assert catalogo.versao == "0.1.0"
    assert fonte is not None
    assert fonte.id == "openfootball_2018_2025"
    assert fonte.licenca == "CC0-1.0"
    assert fonte.status_licenca is StatusLicenca.VERIFICADA
    assert fonte.url_termos == URL_TERMOS
    assert fonte.data_verificacao == "2026-10-29"
    assert fonte.verificador == "Codex (verificação documental)"
    assert fonte.justificativa
    assert set(fonte.mapeamento) == set(CAMPOS_PRD)
    assert fonte.mapeamento["resultado"] == "derivado"
    assert fonte.mapeamento["xg"] == "nao_utilizado"
    assert not any("a verificar" in coluna.lower() for coluna in fonte.mapeamento.values())
