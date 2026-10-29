"""Padronização de equipes, datas, gols e resultados (T003; PRD 5.1 e 5.2).

Trabalha sobre linhas com nomes canônicos do PRD. Valores ausentes viram ``None``; nada é
preenchido silenciosamente. O resultado H/D/A é derivado dos gols.
"""

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime


class PadronizacaoErro(ValueError):
    """Valor com formato inválido, como data fora dos formatos ou gols não inteiros."""


ALIASES_EQUIPES: Mapping[str, str] = {
    "atletico mg": "Atlético Mineiro",
    "atletico mineiro": "Atlético Mineiro",
    "cr flamengo": "Flamengo",
    "flamengo": "Flamengo",
    "gremio": "Grêmio",
    "gremio fbpa": "Grêmio",
    "sao paulo": "São Paulo",
}
"""Exemplos. Chaves já normalizadas (sem acento, minúsculas, sem pontuação).

A lista real depende da fonte aprovada e deve ser revisada nessa etapa.
"""


@dataclass(frozen=True, slots=True)
class Partida:
    """Partida padronizada. Campos ausentes permanecem ``None`` até a validação."""

    partida_id: str | None
    data_partida: date | None
    temporada: int | None
    competicao: str | None
    mandante: str | None
    visitante: str | None
    gols_mandante: int | None
    gols_visitante: int | None
    rodada: int | None

    @property
    def resultado(self) -> str | None:
        """H se o mandante vence, D se empata, A se o visitante vence; None sem gols."""
        if self.gols_mandante is None or self.gols_visitante is None:
            return None
        if self.gols_mandante > self.gols_visitante:
            return "H"
        if self.gols_mandante == self.gols_visitante:
            return "D"
        return "A"


def normalizar_texto(texto: str) -> str:
    """Remove acentos, põe em minúsculas e troca pontuação por espaço."""
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sem_acento.casefold()).split())


def padronizar_equipe(nome: str, aliases: Mapping[str, str] = ALIASES_EQUIPES) -> str:
    """Devolve o nome padronizado; sem alias, mantém o nome com espaços normalizados."""
    chave = normalizar_texto(nome)
    if chave in aliases:
        return aliases[chave]
    return " ".join(nome.split())


def padronizar_data(texto: str, formatos: Sequence[str]) -> date:
    """Converte a data usando os formatos de settings.yaml, na ordem informada."""
    limpo = texto.strip()
    for formato in formatos:
        try:
            return datetime.strptime(limpo, formato).date()
        except ValueError:
            continue
    raise PadronizacaoErro(f"data fora dos formatos aceitos {list(formatos)}: '{texto}'")


def padronizar_inteiro(texto: str | None, campo: str) -> int | None:
    """Converte um inteiro opcional; vazio vira None e texto não inteiro é recusado."""
    limpo = _texto_opcional(texto)
    if limpo is None:
        return None
    try:
        return int(limpo)
    except ValueError as erro:
        raise PadronizacaoErro(f"{campo} não inteiro: '{texto}'") from erro


def padronizar_partidas(
    linhas: Sequence[Mapping[str, str | None]],
    formatos: Sequence[str],
    aliases: Mapping[str, str] = ALIASES_EQUIPES,
) -> list[Partida]:
    """Converte cada linha com nomes canônicos em ``Partida``, mantendo ausências."""
    return [
        Partida(
            partida_id=_texto_opcional(linha.get("partida_id")),
            data_partida=_data_opcional(linha.get("data_partida"), formatos),
            temporada=padronizar_inteiro(linha.get("temporada"), "temporada"),
            competicao=_texto_opcional(linha.get("competicao")),
            mandante=_equipe_opcional(linha.get("equipe_mandante"), aliases),
            visitante=_equipe_opcional(linha.get("equipe_visitante"), aliases),
            gols_mandante=padronizar_inteiro(linha.get("gols_mandante"), "gols_mandante"),
            gols_visitante=padronizar_inteiro(linha.get("gols_visitante"), "gols_visitante"),
            rodada=padronizar_inteiro(linha.get("rodada"), "rodada"),
        )
        for linha in linhas
    ]


def _texto_opcional(valor: str | None) -> str | None:
    if valor is None:
        return None
    limpo = " ".join(valor.split())
    return limpo or None


def _equipe_opcional(valor: str | None, aliases: Mapping[str, str]) -> str | None:
    texto = _texto_opcional(valor)
    return None if texto is None else padronizar_equipe(texto, aliases)


def _data_opcional(valor: str | None, formatos: Sequence[str]) -> date | None:
    texto = _texto_opcional(valor)
    return None if texto is None else padronizar_data(texto, formatos)
