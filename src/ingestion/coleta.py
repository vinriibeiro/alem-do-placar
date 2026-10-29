"""Ingestão local de partidas a partir do fonte selecionado no catálogo (T003; PRD 3.3).

Lê um arquivo CSV local usando o mapeamento do fonte selecionado e grava uma cópia bruta em
``data/raw``. Não acessa a rede e não baixa dados.
"""

import csv
import hashlib
import os
from pathlib import Path

from ingestion.source_catalog import CAMPOS_MINIMOS_PRD, CatalogoFontes, Fonte

PLACEHOLDER = "a verificar"

CAMPOS_LIDOS = tuple(campo for campo in CAMPOS_MINIMOS_PRD if campo != "resultado")
"""Campos mínimos do PRD lidos da fonte. ``resultado`` é derivado dos gols."""


class ColetaErro(RuntimeError):
    """Fonte ausente, mapeamento pendente ou arquivo de origem inválido."""


def selecionar_fonte(catalogo: CatalogoFontes) -> Fonte:
    """Devolve a fonte selecionada; falha explicitamente se nenhuma foi escolhida."""
    fonte = catalogo.fonte_selecionada()
    if fonte is None:
        raise ColetaErro("nenhuma fonte selecionada no catálogo; coleta bloqueada")
    return fonte


def verificar_mapeamento(fonte: Fonte) -> None:
    """Recusa qualquer campo pendente, inclusive os complementares não lidos."""
    pendentes = [
        campo for campo, coluna in fonte.mapeamento.items() if PLACEHOLDER in coluna.lower()
    ]
    if pendentes:
        raise ColetaErro(
            f"fonte '{fonte.id}': mapeamento 'a verificar' nos campos: {', '.join(pendentes)}"
        )


def ler_partidas(origem: Path, fonte: Fonte) -> list[dict[str, str | None]]:
    """Lê o CSV local e devolve linhas com nomes canônicos do PRD.

    Valores vazios viram ``None``: a ausência é listada pela validação, nunca preenchida.
    """
    verificar_mapeamento(fonte)
    colunas = {campo: fonte.mapeamento[campo] for campo in CAMPOS_LIDOS}
    try:
        with origem.open(encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            cabecalho = leitor.fieldnames or []
            ausentes = sorted(
                coluna
                for campo, coluna in colunas.items()
                if campo != "rodada" and coluna not in cabecalho
            )
            if ausentes:
                raise ColetaErro(f"arquivo sem colunas mapeadas: {', '.join(ausentes)}")
            linhas = [
                {campo: _valor(linha.get(coluna)) for campo, coluna in colunas.items()}
                for linha in leitor
            ]
    except FileNotFoundError as erro:
        raise ColetaErro(f"arquivo de origem não encontrado: {origem}") from erro
    if not linhas:
        raise ColetaErro(f"arquivo sem partidas: {origem}")
    return linhas


def copiar_bruto(origem: Path, fonte: Fonte, pasta_raw: Path) -> Path:
    """Grava cópia byte a byte da origem em ``pasta_raw``, nomeada pelo hash do conteúdo."""
    try:
        conteudo = origem.read_bytes()
    except FileNotFoundError as erro:
        raise ColetaErro(f"arquivo de origem não encontrado: {origem}") from erro
    digest = hashlib.sha256(conteudo).hexdigest()
    pasta_raw.mkdir(parents=True, exist_ok=True)
    destino = pasta_raw / f"{fonte.id}_{digest[:12]}.csv"
    temporario = pasta_raw / f"{destino.name}.tmp"
    temporario.write_bytes(conteudo)
    os.replace(temporario, destino)
    return destino


def _valor(bruto: str | None) -> str | None:
    limpo = (bruto or "").strip()
    return limpo or None
