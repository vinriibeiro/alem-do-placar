"""Adaptador local do OpenFootball (T003; PRD 3.1 e 3.3).

Converte o ``Football.TXT`` de uma temporada no CSV canônico lido por ``ingestion.coleta``.
Não acessa a rede e não baixa dados: o texto é recebido pelo chamador. Linhas que não são
cabeçalho, rodada, data, partida ou comentário falham explicitamente, nunca são descartadas.
"""

import csv
import hashlib
import re
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from processing.padronizacao import normalizar_texto

TEMPORADAS_APROVADAS = tuple(range(2018, 2026))
"""Escopo do perfil em ``config/approved_source.toml``. 2015–2017 e 2026 ficam fora."""

COLUNAS_CSV = (
    "partida_id",
    "data_partida",
    "temporada",
    "competicao",
    "equipe_mandante",
    "equipe_visitante",
    "gols_mandante",
    "gols_visitante",
    "rodada",
)
"""Colunas do CSV canônico. ``resultado`` é derivado dos gols pelo pipeline."""

ALIASES_OPENFOOTBALL: Mapping[str, str] = {
    "AC Goianiense": "Atlético Goianiense",
    "América MG": "América Mineiro",
    "CA Paranaense": "Athletico Paranaense",
    "CA Mineiro": "Atlético Mineiro",
    "Bahia BA": "EC Bahia",
    "Botafogo RJ": "Botafogo FR",
    "Ceará CE": "Ceará SC",
    "Corinthians SP": "SC Corinthians Paulista",
    "Coritiba PR": "Coritiba FBC",
    "Cruzeiro": "Cruzeiro EC",
    "Cuiabá MT": "Cuiabá EC",
    "Flamengo RJ": "CR Flamengo",
    "Fluminense RJ": "Fluminense FC",
    "Fortaleza CE": "Fortaleza EC",
    "Goiás GO": "Goiás EC",
    "Grêmio Porto Alegre": "Grêmio FBPA",
    "Internacional": "SC Internacional",
    "Juventude RS": "EC Juventude",
    "Palmeiras": "SE Palmeiras",
    "Red Bull Bragantino": "RB Bragantino",
    "Sport Recife PE": "SC Recife",
    "Vasco da Gama RJ": "CR Vasco da Gama",
    "Vitória BA": "EC Vitória",
}
"""Alias revisável -> forma canônica. Correspondência exata após normalizar espaços.

Nomes fora da tabela são mantidos como estão. Não há inferência aproximada.
"""

MESES = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

_CABECALHO = re.compile(r"^=\s*(?P<competicao>.+?)\s+(?P<ano>\d{4})$")
_RODADA = re.compile(r"^▪\s*Matchday\s+(?P<rodada>\d+)$")
_DATA = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(?P<mes>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+(?P<dia>\d{1,2})(?:\s+(?P<ano>\d{4}))?$"
)
# Horário e placar do intervalo são aceitos e descartados; o placar final é obrigatório.
_PARTIDA = re.compile(
    r"^(?:\d{1,2}:\d{2}\s+)?(?P<mandante>.+?)\s+v\s+(?P<visitante>.+?)\s+"
    r"(?P<gols_mandante>\d+)-(?P<gols_visitante>\d+)(?:\s+\(\d+-\d+\))?$"
)


class ConversaoErro(ValueError):
    """Linha, cabeçalho, data ou partida que o adaptador não consegue interpretar com segurança."""


def converter_temporada(texto: str, temporada: int) -> list[dict[str, str]]:
    """Converte o ``Football.TXT`` de uma temporada em linhas canônicas, na ordem do arquivo.

    Cabeçalhos, rodadas e comentários não viram partidas. Qualquer outra linha que não seja
    partida válida gera ``ConversaoErro`` com o número da linha.
    """
    if temporada not in TEMPORADAS_APROVADAS:
        raise ConversaoErro(f"temporada fora do escopo aprovado: {temporada}")
    competicao: str | None = None
    rodada = ""
    data: date | None = None
    linhas: list[dict[str, str]] = []
    ids: set[str] = set()
    for numero, bruta in enumerate(texto.lstrip("﻿").splitlines(), 1):
        linha = bruta.strip()
        if not linha or linha.startswith("#"):
            continue
        if cabecalho := _CABECALHO.match(linha):
            competicao = _competicao(cabecalho, temporada, numero)
        elif rodada_encontrada := _RODADA.match(linha):
            rodada = rodada_encontrada["rodada"]
        elif data_encontrada := _DATA.match(linha):
            data = _data_da_linha(data_encontrada, temporada, numero)
        elif partida := _PARTIDA.match(linha):
            if competicao is None:
                raise ConversaoErro(f"linha {numero}: partida antes do cabeçalho da competição")
            if data is None:
                raise ConversaoErro(f"linha {numero}: partida antes de qualquer data")
            registro = _montar_partida(partida, competicao, temporada, data, rodada, numero)
            if registro["partida_id"] in ids:
                raise ConversaoErro(f"linha {numero}: partida duplicada")
            ids.add(registro["partida_id"])
            linhas.append(registro)
        else:
            raise ConversaoErro(f"linha {numero}: formato não reconhecido: '{linha}'")
    return linhas


def gravar_csv(linhas: Sequence[Mapping[str, str]], caminho: str | Path) -> Path:
    """Grava as linhas em CSV UTF-8 com as colunas canônicas. Não cria pastas."""
    destino = Path(caminho)
    with destino.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_CSV)
        escritor.writeheader()
        escritor.writerows(linhas)
    return destino


def nome_canonico(nome: str) -> str:
    """Devolve a forma canônica do alias revisado; nomes desconhecidos são preservados."""
    limpo = " ".join(nome.split())
    return ALIASES_OPENFOOTBALL.get(limpo, limpo)


def gerar_partida_id(temporada: int, data_iso: str, mandante: str, visitante: str) -> str:
    """SHA256 completo de temporada, data e equipes normalizadas; não usa número de linha."""
    chave = "|".join(
        (
            str(temporada),
            data_iso,
            normalizar_texto(mandante),
            normalizar_texto(visitante),
        )
    )
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()


def _competicao(match: re.Match[str], temporada: int, numero: int) -> str:
    if int(match["ano"]) != temporada:
        raise ConversaoErro(
            f"linha {numero}: cabeçalho de {match['ano']} em arquivo da temporada {temporada}"
        )
    return match["competicao"]


def _data_da_linha(match: re.Match[str], temporada: int, numero: int) -> date:
    mes = MESES[match["mes"]]
    if match["ano"]:
        ano = int(match["ano"])
    elif temporada == 2020 and mes in (1, 2):
        # A temporada 2020 (pandemia) foi concluída em janeiro e fevereiro de 2021.
        ano = 2021
    else:
        ano = temporada
    try:
        return date(ano, mes, int(match["dia"]))
    except ValueError as erro:
        raise ConversaoErro(f"linha {numero}: data inválida: '{match[0]}'") from erro


def _montar_partida(
    match: re.Match[str],
    competicao: str,
    temporada: int,
    data: date,
    rodada: str,
    numero: int,
) -> dict[str, str]:
    mandante = nome_canonico(match["mandante"])
    visitante = nome_canonico(match["visitante"])
    if mandante == visitante:
        raise ConversaoErro(f"linha {numero}: mandante e visitante iguais: '{mandante}'")
    data_iso = data.isoformat()
    return {
        "partida_id": gerar_partida_id(temporada, data_iso, mandante, visitante),
        "data_partida": data_iso,
        "temporada": str(temporada),
        "competicao": competicao,
        "equipe_mandante": mandante,
        "equipe_visitante": visitante,
        "gols_mandante": str(int(match["gols_mandante"])),
        "gols_visitante": str(int(match["gols_visitante"])),
        "rodada": rodada,
    }
