"""Catálogo versionado das fontes de dados candidatas (T002; PRD seções 3.1 a 3.4).

Carrega ``config/data_sources.toml`` com ``tomllib``, valida o schema e aplica as regras
de verificação de licença e de seleção da fonte principal. Não acessa a rede e não
baixa dados.
"""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class CatalogoInvalido(ValueError):
    """Catálogo com campo ausente, valor inválido ou regra de seleção violada."""


class StatusLicenca(StrEnum):
    """Situação da licença. Só 'verificada' permite uso, e somente com evidência."""

    PENDENTE_VERIFICACAO = "pendente_verificacao"
    VERIFICADA = "verificada"
    RESTRITA = "restrita"
    REJEITADA = "rejeitada"


class Decisao(StrEnum):
    """Decisão sobre a fonte. Apenas uma fonte pode ser 'selecionada'."""

    PENDENTE = "pendente"
    SELECIONADA = "selecionada"
    DESCARTADA = "descartada"


CAMPOS_MINIMOS_PRD = (
    "partida_id",
    "data_partida",
    "temporada",
    "competicao",
    "equipe_mandante",
    "equipe_visitante",
    "gols_mandante",
    "gols_visitante",
    "resultado",
    "rodada",
)

CAMPOS_COMPLEMENTARES_PRD = (
    "finalizacoes",
    "finalizacoes_no_alvo",
    "posse_de_bola",
    "cartoes",
    "escanteios",
    "xg",
    "dias_descanso",
    "outras_estatisticas",
)

CAMPOS_PRD = CAMPOS_MINIMOS_PRD + CAMPOS_COMPLEMENTARES_PRD

CAMPOS_OBRIGATORIOS_FONTE = (
    "id",
    "nome",
    "url",
    "licenca",
    "status_licenca",
    "cobertura_brasileirao",
    "temporadas",
    "campos_essenciais",
    "campos_complementares",
    "riscos",
    "decisao",
    "mapeamento",
)


@dataclass(frozen=True, slots=True)
class Fonte:
    """Uma fonte candidata do catálogo."""

    id: str
    nome: str
    url: str
    licenca: str
    status_licenca: StatusLicenca
    cobertura_brasileirao: str
    temporadas: str
    campos_essenciais: tuple[str, ...]
    campos_complementares: tuple[str, ...]
    riscos: tuple[str, ...]
    decisao: Decisao
    mapeamento: Mapping[str, str]
    url_termos: str | None = None
    data_verificacao: str | None = None
    verificador: str | None = None
    justificativa: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogoFontes:
    """Conjunto validado de fontes candidatas."""

    versao: str
    fontes: tuple[Fonte, ...]

    def buscar(self, id_fonte: str) -> Fonte:
        for fonte in self.fontes:
            if fonte.id == id_fonte:
                return fonte
        raise KeyError(f"fonte não encontrada: {id_fonte}")

    def fonte_selecionada(self) -> Fonte | None:
        for fonte in self.fontes:
            if fonte.decisao is Decisao.SELECIONADA:
                return fonte
        return None


def verificar_licenca(fonte: Fonte) -> None:
    """Rejeita licença 'verificada' sem url_termos, data_verificacao e verificador."""
    if fonte.status_licenca is not StatusLicenca.VERIFICADA:
        return
    evidencias = {
        "url_termos": fonte.url_termos,
        "data_verificacao": fonte.data_verificacao,
        "verificador": fonte.verificador,
    }
    faltantes = [nome for nome, valor in evidencias.items() if not valor]
    if faltantes:
        raise CatalogoInvalido(
            f"fonte '{fonte.id}': licença 'verificada' sem evidência: {', '.join(faltantes)}"
        )


def validar_selecao(catalogo: CatalogoFontes) -> None:
    """Exige, para a fonte principal, licença verificada e justificativa documentada."""
    selecionadas = [f for f in catalogo.fontes if f.decisao is Decisao.SELECIONADA]
    if len(selecionadas) > 1:
        ids = ", ".join(f.id for f in selecionadas)
        raise CatalogoInvalido(f"apenas uma fonte pode ser 'selecionada'; encontradas: {ids}")
    for fonte in selecionadas:
        if fonte.status_licenca is not StatusLicenca.VERIFICADA:
            raise CatalogoInvalido(
                f"fonte '{fonte.id}': seleção exige licença verificada "
                f"(status atual: {fonte.status_licenca.value})"
            )
        if not fonte.justificativa:
            raise CatalogoInvalido(f"fonte '{fonte.id}': seleção exige justificativa")


def carregar_catalogo(caminho: str | Path) -> CatalogoFontes:
    """Lê o TOML do catálogo, valida o schema e as regras de licença e seleção."""
    arquivo = Path(caminho)
    try:
        with arquivo.open("rb") as origem:
            dados = tomllib.load(origem)
    except FileNotFoundError as erro:
        raise CatalogoInvalido(f"catálogo não encontrado: {arquivo}") from erro
    except tomllib.TOMLDecodeError as erro:
        raise CatalogoInvalido(f"TOML inválido em {arquivo}: {erro}") from erro
    return construir_catalogo(dados)


def construir_catalogo(dados: Mapping[str, Any]) -> CatalogoFontes:
    """Valida um dicionário já lido do TOML e devolve o catálogo."""
    tabela = dados.get("catalogo")
    if not isinstance(tabela, dict):
        raise CatalogoInvalido("tabela [catalogo] ausente")
    versao = _texto(tabela, "versao", "[catalogo]")

    brutas = dados.get("fontes")
    if not isinstance(brutas, list) or not brutas:
        raise CatalogoInvalido("'fontes' deve ser uma lista não vazia de tabelas [[fontes]]")
    fontes = tuple(_construir_fonte(bruta, indice) for indice, bruta in enumerate(brutas, 1))

    ids = [fonte.id for fonte in fontes]
    duplicados = sorted({id_ for id_ in ids if ids.count(id_) > 1})
    if duplicados:
        raise CatalogoInvalido(f"identificadores de fonte duplicados: {', '.join(duplicados)}")

    catalogo = CatalogoFontes(versao=versao, fontes=fontes)
    for fonte in fontes:
        verificar_licenca(fonte)
    validar_selecao(catalogo)
    return catalogo


def _construir_fonte(bruta: Any, indice: int) -> Fonte:
    if not isinstance(bruta, dict):
        raise CatalogoInvalido(f"fonte #{indice}: deve ser uma tabela [[fontes]]")
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS_FONTE if campo not in bruta]
    if ausentes:
        raise CatalogoInvalido(
            f"fonte #{indice}: campos obrigatórios ausentes: {', '.join(ausentes)}"
        )
    id_fonte = _texto(bruta, "id", f"fonte #{indice}")
    contexto = f"fonte '{id_fonte}'"
    return Fonte(
        id=id_fonte,
        nome=_texto(bruta, "nome", contexto),
        url=_texto(bruta, "url", contexto),
        licenca=_texto(bruta, "licenca", contexto),
        status_licenca=_enum(StatusLicenca, bruta, "status_licenca", contexto),
        cobertura_brasileirao=_texto(bruta, "cobertura_brasileirao", contexto),
        temporadas=_texto(bruta, "temporadas", contexto),
        campos_essenciais=_lista_textos(bruta, "campos_essenciais", contexto),
        campos_complementares=_lista_textos(
            bruta, "campos_complementares", contexto, vazia_permitida=True
        ),
        riscos=_lista_textos(bruta, "riscos", contexto),
        decisao=_enum(Decisao, bruta, "decisao", contexto),
        mapeamento=_mapeamento(bruta, contexto),
        url_termos=_opcional(bruta, "url_termos", contexto),
        data_verificacao=_opcional(bruta, "data_verificacao", contexto),
        verificador=_opcional(bruta, "verificador", contexto),
        justificativa=_opcional(bruta, "justificativa", contexto),
    )


def _texto(dados: Mapping[str, Any], campo: str, contexto: str) -> str:
    valor = dados.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise CatalogoInvalido(f"{contexto}: campo '{campo}' deve ser texto não vazio")
    return valor


def _opcional(dados: Mapping[str, Any], campo: str, contexto: str) -> str | None:
    valor = dados.get(campo)
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise CatalogoInvalido(f"{contexto}: campo '{campo}' deve ser texto")
    return valor.strip() or None


def _lista_textos(
    dados: Mapping[str, Any], campo: str, contexto: str, *, vazia_permitida: bool = False
) -> tuple[str, ...]:
    valor = dados.get(campo)
    if not isinstance(valor, list) or not all(
        isinstance(item, str) and item.strip() for item in valor
    ):
        raise CatalogoInvalido(f"{contexto}: '{campo}' deve ser lista de textos")
    if not valor and not vazia_permitida:
        raise CatalogoInvalido(f"{contexto}: '{campo}' não pode ser vazio")
    return tuple(valor)


def _enum[E: StrEnum](tipo: type[E], dados: Mapping[str, Any], campo: str, contexto: str) -> E:
    valor = _texto(dados, campo, contexto)
    try:
        return tipo(valor)
    except ValueError as erro:
        aceitos = ", ".join(membro.value for membro in tipo)
        raise CatalogoInvalido(
            f"{contexto}: '{campo}' inválido '{valor}'; valores aceitos: {aceitos}"
        ) from erro


def _mapeamento(dados: Mapping[str, Any], contexto: str) -> dict[str, str]:
    valor = dados.get("mapeamento")
    if not isinstance(valor, dict):
        raise CatalogoInvalido(f"{contexto}: 'mapeamento' deve ser uma tabela")
    desconhecidos = sorted(set(valor) - set(CAMPOS_PRD))
    if desconhecidos:
        raise CatalogoInvalido(
            f"{contexto}: campos de mapeamento desconhecidos: {', '.join(desconhecidos)}"
        )
    faltantes = [campo for campo in CAMPOS_PRD if campo not in valor]
    if faltantes:
        raise CatalogoInvalido(f"{contexto}: mapeamento sem campos do PRD: {', '.join(faltantes)}")
    for campo, coluna in valor.items():
        if not isinstance(coluna, str) or not coluna.strip():
            raise CatalogoInvalido(f"{contexto}: mapeamento de '{campo}' deve ser texto não vazio")
    return dict(valor)
