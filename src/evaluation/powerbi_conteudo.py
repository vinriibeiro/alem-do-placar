"""Conteúdo derivado para o relatório: comparação de modelos, destaques e metadados de exibição.

Tudo vem de arquivos do projeto: métricas do backtesting, partidas processadas e
``config/destaques.csv`` (Wikipédia, prêmios oficiais e artilharia). Nada é estimado.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from evaluation.nomes import MODELOS, nome_modelo
from evaluation.powerbi_layout import SEM_FOTO

MODELO_REFERENCIA = "M00_media_recente_5"
CATEGORIAS = ("artilheiro", "craque", "goleiro")
COLUNAS_DESTAQUE = {
    "ano": "int64",
    "nome": "string",
    "clube": "string",
    "imagem": "string",
    "escudo": "string",
    "detalhe": "string",
    "credito": "string",
}
COLUNAS_COMPARACAO = {
    "ordem": "int64",
    "modelo": "string",
    "nome": "string",
    "tipo": "string",
    "mae_validacao": "double",
    "rmse_validacao": "double",
    "mae_teste": "double",
    "rmse_teste": "double",
    "diferenca_referencia": "string",
    "selecionado": "string",
}


def _decimal(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def comparacao_modelos(metricas: list[dict[str, Any]], selecionado: str) -> list[dict[str, Any]]:
    """Uma linha por modelo: validação (todas as temporadas) e teste de 2025, quando houver."""

    def _busca(fase: str, modelo: str) -> dict | None:
        return next(
            (
                r
                for r in metricas
                if r["fase"] == fase and r["modelo"] == modelo and str(r["temporada"]) == "todas"
            ),
            None,
        )

    modelos = [m for m in MODELOS if _busca("validacao", m)]
    modelos += sorted({r["modelo"] for r in metricas if r["fase"] == "validacao"} - set(modelos))
    referencia = _busca("validacao", MODELO_REFERENCIA)
    linhas = []
    for ordem, modelo in enumerate(modelos, start=1):
        val = _busca("validacao", modelo)
        teste = _busca("holdout", modelo)
        if modelo == MODELO_REFERENCIA or not referencia:
            diferenca = "referência"
        else:
            pct = (val["mae"] - referencia["mae"]) / referencia["mae"] * 100
            diferenca = f"{pct:+.1f}% no MAE".replace(".", ",")
        linhas.append(
            {
                "ordem": ordem,
                "modelo": modelo,
                "nome": nome_modelo(modelo),
                "tipo": MODELOS.get(modelo, ("", "Outro"))[1] or "Outro",
                "mae_validacao": round(val["mae"], 3),
                "rmse_validacao": round(val["rmse"], 3),
                "mae_teste": round(teste["mae"], 3) if teste else None,
                "rmse_teste": round(teste["rmse"], 3) if teste else None,
                "diferenca_referencia": diferenca,
                "selecionado": "Sim" if modelo == selecionado else "",
            }
        )
    return linhas


def estatisticas_temporada(pasta_processados: Path) -> pd.DataFrame:
    """Gols marcados, sofridos e jogos por equipe e temporada, a partir das tabelas processadas."""
    try:
        fato = pd.read_parquet(pasta_processados / "fato_desempenho_equipes.parquet")
        partidas = pd.read_parquet(pasta_processados / "fato_partidas.parquet")
        temporadas = pd.read_parquet(pasta_processados / "dim_temporadas.parquet")
        equipes = pd.read_parquet(pasta_processados / "dim_equipes.parquet")
    except (OSError, ValueError):
        return pd.DataFrame(columns=["ano", "equipe", "jogos", "gols_pro", "gols_contra"])
    base = (
        fato.merge(partidas[["partida_id", "temporada_id"]], on="partida_id")
        .merge(temporadas[["temporada_id", "ano"]], on="temporada_id")
        .merge(equipes[["equipe_id", "nome_padronizado"]], on="equipe_id")
    )
    return (
        base.groupby(["ano", "nome_padronizado"])
        .agg(
            jogos=("partida_id", "count"),
            gols_pro=("gols_pro", "sum"),
            gols_contra=("gols_contra", "sum"),
        )
        .reset_index()
        .rename(columns={"nome_padronizado": "equipe"})
    )


def meta_exibicao(pasta_processados: Path) -> dict[str, str]:
    """Último ano e data da última partida nos dados (para rodapé e textos)."""
    try:
        partidas = pd.read_parquet(pasta_processados / "fato_partidas.parquet")
        temporadas = pd.read_parquet(pasta_processados / "dim_temporadas.parquet")
    except (OSError, ValueError):
        return {}
    if partidas.empty or temporadas.empty:
        return {}
    ultima = pd.to_datetime(partidas["data_partida"]).max()
    return {"ultimo_ano": str(int(temporadas["ano"].max())), "ultima_partida": f"{ultima:%d/%m/%Y}"}


def _ler_destaques(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def destaques(
    caminho_csv: Path, estat: pd.DataFrame, escudos: dict[str, str]
) -> dict[str, list[dict[str, Any]]]:
    """Linhas das quatro tabelas de destaque, por temporada presente nos dados."""
    anos = sorted(int(a) for a in estat["ano"].unique())
    registros = _ler_destaques(caminho_csv)
    tabelas: dict[str, list[dict[str, Any]]] = {
        f"destaque_{c}": [] for c in (*CATEGORIAS, "ataque")
    }
    for ano in anos:
        do_ano = estat[estat["ano"] == ano]
        for categoria in CATEGORIAS:
            linhas = [r for r in registros if int(r["ano"]) == ano and r["categoria"] == categoria]
            if not linhas:
                tabelas[f"destaque_{categoria}"].append(
                    {
                        "ano": ano,
                        "nome": "Não informado na fonte",
                        "clube": "",
                        "imagem": SEM_FOTO,
                        "escudo": SEM_FOTO,
                        "detalhe": "A fonte consultada não registra este destaque na temporada.",
                        "credito": "",
                    }
                )
                continue
            for r in linhas:
                clube = r["clube"]
                if categoria == "artilheiro":
                    detalhe = f"{r['gols']} gols · {clube}"
                    if len(linhas) > 1:
                        detalhe += " (empatado)"
                elif categoria == "craque":
                    detalhe = f"{clube} · Prêmio Brasileirão (CBF)"
                else:
                    time = do_ano[do_ano["equipe"] == clube]
                    if time.empty:
                        detalhe = f"{clube} · Prêmio Brasileirão (CBF)"
                    else:
                        t = time.iloc[0]
                        detalhe = (
                            f"{clube} · o clube sofreu {int(t.gols_contra)} gols em {int(t.jogos)} jogos "
                            f"({_decimal(t.gols_contra / t.jogos)} por jogo)"
                        )
                credito = (
                    f"Foto: {r['foto_autor'] or 'autor na Wikimedia'} · {r['foto_licenca']} · Wikimedia Commons"
                    if r["foto_url"]
                    else "Sem foto com licença livre disponível."
                )
                tabelas[f"destaque_{categoria}"].append(
                    {
                        "ano": ano,
                        "nome": r["jogador"],
                        "clube": clube,
                        "imagem": r["foto_url"] or SEM_FOTO,
                        "escudo": escudos.get(clube, SEM_FOTO),
                        "detalhe": detalhe,
                        "credito": credito,
                    }
                )
        melhor = do_ano[do_ano["gols_pro"] == do_ano["gols_pro"].max()]
        for t in melhor.itertuples():
            tabelas["destaque_ataque"].append(
                {
                    "ano": ano,
                    "nome": t.equipe,
                    "clube": t.equipe,
                    "imagem": escudos.get(t.equipe, SEM_FOTO),
                    "escudo": escudos.get(t.equipe, SEM_FOTO),
                    "detalhe": f"{int(t.gols_pro)} gols em {int(t.jogos)} jogos ({_decimal(t.gols_pro / t.jogos)} por jogo)",
                    "credito": "Calculado a partir das partidas (OpenFootball).",
                }
            )
    return tabelas
