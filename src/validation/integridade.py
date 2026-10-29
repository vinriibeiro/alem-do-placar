"""Validação de integridade das partidas e do desempenho (T003; PRD 5.2 e 13.1).

Gera achados classificados como críticos ou avisos. Ausências são listadas explicitamente.
Críticos interrompem o pipeline; avisos apenas são registrados.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from processing.padronizacao import Partida, normalizar_texto

PONTOS_VALIDOS = frozenset({0, 1, 3})

CAMPOS_CRITICOS = (
    "partida_id",
    "data_partida",
    "temporada",
    "competicao",
    "mandante",
    "visitante",
    "gols_mandante",
    "gols_visitante",
)
CAMPOS_AVISO = ("rodada",)


class Severidade(StrEnum):
    CRITICO = "critico"
    AVISO = "aviso"


@dataclass(frozen=True, slots=True)
class Achado:
    """Um problema encontrado na validação."""

    severidade: Severidade
    regra: str
    mensagem: str


@dataclass(frozen=True, slots=True)
class RelatorioIntegridade:
    """Conjunto de achados da validação, separado em críticos e avisos."""

    achados: tuple[Achado, ...]

    @property
    def criticos(self) -> tuple[Achado, ...]:
        return tuple(a for a in self.achados if a.severidade is Severidade.CRITICO)

    @property
    def avisos(self) -> tuple[Achado, ...]:
        return tuple(a for a in self.achados if a.severidade is Severidade.AVISO)


class IntegridadeErro(ValueError):
    """Relatório com ao menos um achado crítico."""

    def __init__(self, relatorio: RelatorioIntegridade) -> None:
        self.relatorio = relatorio
        mensagens = "; ".join(a.mensagem for a in relatorio.criticos)
        super().__init__(f"{len(relatorio.criticos)} falha(s) crítica(s): {mensagens}")


def validar_partidas(partidas: Sequence[Partida]) -> list[Achado]:
    """Valida identificadores, ausências, equipes e gols de cada partida."""
    achados: list[Achado] = []
    contagem = Counter(p.partida_id for p in partidas if p.partida_id is not None)
    for partida_id, total in sorted(contagem.items()):
        if total > 1:
            achados.append(_critico("partida_duplicada", f"partida_id duplicado: {partida_id}"))
    for indice, partida in enumerate(partidas, 1):
        rotulo = partida.partida_id or f"linha {indice}"
        achados.extend(_ausencias(partida, rotulo))
        achados.extend(_regras_partida(partida, rotulo))
    return achados


def validar_desempenho(linhas: Sequence[Mapping[str, object]]) -> list[Achado]:
    """Valida pontos (regra 3/1/0) e as duas observações de desempenho por partida."""
    achados: list[Achado] = []
    for linha in linhas:
        if linha["pontos"] not in PONTOS_VALIDOS:
            achados.append(
                _critico(
                    "pontos_invalidos",
                    f"partida {linha['partida_id']}: pontos fora de 3/1/0: {linha['pontos']}",
                )
            )
    por_partida = Counter(linha["partida_id"] for linha in linhas)
    for partida_id, total in sorted(por_partida.items()):
        if total != 2:
            achados.append(
                _critico(
                    "observacoes_por_partida",
                    f"partida {partida_id}: {total} observações de desempenho (esperado 2)",
                )
            )
    return achados


def levantar_se_critico(relatorio: RelatorioIntegridade) -> None:
    """Interrompe com ``IntegridadeErro`` se houver qualquer achado crítico."""
    if relatorio.criticos:
        raise IntegridadeErro(relatorio)


def _ausencias(partida: Partida, rotulo: str) -> list[Achado]:
    achados = [
        _critico("ausencia", f"{rotulo}: campo '{campo}' ausente")
        for campo in CAMPOS_CRITICOS
        if getattr(partida, campo) is None
    ]
    achados.extend(
        _aviso("ausencia", f"{rotulo}: campo '{campo}' ausente")
        for campo in CAMPOS_AVISO
        if getattr(partida, campo) is None
    )
    return achados


def _regras_partida(partida: Partida, rotulo: str) -> list[Achado]:
    achados: list[Achado] = []
    if (
        partida.mandante is not None
        and partida.visitante is not None
        and normalizar_texto(partida.mandante) == normalizar_texto(partida.visitante)
    ):
        achados.append(
            _critico("mandante_igual_visitante", f"{rotulo}: mandante igual ao visitante")
        )
    for campo in ("gols_mandante", "gols_visitante"):
        valor = getattr(partida, campo)
        if valor is None:
            continue
        if isinstance(valor, bool) or not isinstance(valor, int):
            achados.append(
                _critico("gols_nao_inteiros", f"{rotulo}: {campo} não inteiro: {valor!r}")
            )
        elif valor < 0:
            achados.append(_critico("gols_negativos", f"{rotulo}: {campo} negativo: {valor}"))
    return achados


def _critico(regra: str, mensagem: str) -> Achado:
    return Achado(Severidade.CRITICO, regra, mensagem)


def _aviso(regra: str, mensagem: str) -> Achado:
    return Achado(Severidade.AVISO, regra, mensagem)
