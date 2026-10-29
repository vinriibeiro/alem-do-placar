"""Dados públicos da Central de Consulta (arquivos JSON estáticos).

A central roda inteiramente no navegador: as estatísticas são calculadas em JavaScript a partir
das partidas, e as explicações vêm de ``config/central_conhecimento.yaml``. Este módulo apenas
monta os JSON a partir dos arquivos do projeto; nada é estimado e não há chamada a serviços pagos.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from evaluation.nomes import ATRIBUTOS, MODELOS, nome_atributo, nome_modelo

ARQUIVOS = ("partidas", "modelo", "destaques", "escudos", "conhecimento", "contexto", "sugestoes")


def _ler_partidas(raiz: Path) -> tuple[list[str], list[list]]:
    proc = raiz / "data" / "processed"
    p = pd.read_parquet(proc / "fato_partidas.parquet")
    t = pd.read_parquet(proc / "dim_temporadas.parquet")
    e = pd.read_parquet(proc / "dim_equipes.parquet")
    nomes = dict(zip(e["equipe_id"], e["nome_padronizado"], strict=True))
    p = p.merge(t[["temporada_id", "ano"]], on="temporada_id").sort_values(
        ["data_partida", "partida_id"]
    )
    equipes = sorted(set(nomes.values()))
    indice = {n: i for i, n in enumerate(equipes)}
    linhas = [
        [
            int(r.ano),
            str(pd.Timestamp(r.data_partida).date()),
            indice[nomes[r.equipe_mandante_id]],
            indice[nomes[r.equipe_visitante_id]],
            int(r.gols_mandante),
            int(r.gols_visitante),
        ]
        for r in p.itertuples()
    ]
    return equipes, linhas


def _ler_modelo(raiz: Path) -> dict[str, Any]:
    pasta = raiz / "data" / "predictions"
    meta = json.loads((pasta / "modelagem" / "metadados.json").read_text(encoding="utf-8"))
    metricas = json.loads((pasta / "modelagem" / "metricas.json").read_text(encoding="utf-8"))
    imp = pd.read_csv(pasta / "cientifica" / "importancias.csv").sort_values(
        "delta_mae_media", ascending=False
    )
    prev = pd.read_parquet(pasta / "modelagem" / "previsoes.parquet").sort_values(
        ["equipe", "data_referencia"]
    )

    def _m(fase: str, modelo: str) -> dict | None:
        return next(
            (
                r
                for r in metricas
                if r["fase"] == fase and r["modelo"] == modelo and str(r["temporada"]) == "todas"
            ),
            None,
        )

    comparacao = []
    for codigo in MODELOS:
        val = _m("validacao", codigo)
        if not val:
            continue
        teste = _m("holdout", codigo)
        comparacao.append(
            {
                "codigo": codigo,
                "nome": nome_modelo(codigo),
                "tipo": MODELOS[codigo][1],
                "mae_validacao": round(val["mae"], 3),
                "rmse_validacao": round(val["rmse"], 3),
                "mae_teste": round(teste["mae"], 3) if teste else None,
                "rmse_teste": round(teste["rmse"], 3) if teste else None,
                "selecionado": codigo == meta["modelo_selecionado"],
            }
        )
    selecionado = _m("holdout", meta["modelo_selecionado"]) or {}
    referencia = _m("holdout", "M00_media_recente_5") or {}
    previsoes = [
        [
            r.equipe,
            str(pd.Timestamp(r.data_referencia).date()),
            round(float(r.previsao), 3),
            round(float(r.limite_inferior), 3),
            round(float(r.limite_superior), 3),
            None if pd.isna(r.alvo) else round(float(r.alvo), 3),
        ]
        for r in prev.itertuples()
    ]
    return {
        "modelo": meta["modelo_selecionado"],
        "modelo_nome": nome_modelo(meta["modelo_selecionado"]),
        "versao": meta["versao"],
        "corte_treino": meta["corte_treino"],
        "anos_validacao": meta.get("anos_validacao", []),
        "ano_teste": meta.get("ano_holdout"),
        "n_teste": meta.get("n_holdout"),
        "mae_teste": round(selecionado.get("mae", 0), 3),
        "rmse_teste": round(selecionado.get("rmse", 0), 3),
        "mae_referencia_teste": round(referencia.get("mae", 0), 3),
        "cobertura": round(float(meta.get("cobertura_holdout") or 0), 4),
        "comparacao": comparacao,
        "importancias": [
            {
                "codigo": r.atributo,
                "nome": nome_atributo(r.atributo),
                "descricao": ATRIBUTOS.get(r.atributo, ("", ""))[1],
                "delta_mae": round(float(r.delta_mae_media), 4),
            }
            for r in imp.itertuples()
        ],
        "previsoes": previsoes,
    }


def _ler_csv(caminho: Path) -> list[dict[str, str]]:
    if not caminho.is_file():
        return []
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _destaques(raiz: Path) -> list[dict[str, Any]]:
    return [
        {
            "ano": int(r["ano"]),
            "categoria": r["categoria"],
            "jogador": r["jogador"],
            "clube": r["clube"],
            "gols": int(r["gols"]) if r["gols"] else None,
            "foto": r["foto_url"] or None,
            "credito": " · ".join(x for x in (r["foto_autor"], r["foto_licenca"]) if x)
            if r["foto_url"]
            else None,
            "fonte": r["fonte"],
        }
        for r in _ler_csv(raiz / "config" / "destaques.csv")
    ]


def _fatos(equipes: list[str], partidas: list[list], modelo: dict[str, Any]) -> dict[str, str]:
    """Valores reais usados nos textos da base de conhecimento ({chave} no YAML)."""
    anos = sorted({p[0] for p in partidas})
    melhor_ml = min(
        (c for c in modelo["comparacao"] if c["tipo"] == "Machine Learning"),
        key=lambda c: c["mae_validacao"],
    )
    ref = next(c for c in modelo["comparacao"] if c["codigo"] == "M00_media_recente_5")

    def br(v: float, casas: int = 3) -> str:
        return f"{v:.{casas}f}".replace(".", ",")

    return {
        "n_partidas": f"{len(partidas):,}".replace(",", "."),
        "n_equipes": str(len(equipes)),
        "ano_inicial": str(anos[0]),
        "ano_final": str(anos[-1]),
        "n_temporadas": str(len(anos)),
        "modelo_nome": modelo["modelo_nome"],
        "mae_teste": br(modelo["mae_teste"]),
        "rmse_teste": br(modelo["rmse_teste"]),
        "mae_referencia_teste": br(modelo["mae_referencia_teste"]),
        "mae_validacao_melhor": br(melhor_ml["mae_validacao"]),
        "mae_validacao_referencia": br(ref["mae_validacao"]),
        "cobertura": br(modelo["cobertura"] * 100, 1) + "%",
        "corte_treino": modelo["corte_treino"],
        "n_teste": str(modelo["n_teste"]),
        "n_modelos": str(len(modelo["comparacao"])),
        "mae_5_jogos": br(modelo["mae_teste"] * 5, 1),
    }


def _conhecimento(raiz: Path, fatos: dict[str, str]) -> list[dict[str, Any]]:
    dados = yaml.safe_load(
        (raiz / "config" / "central_conhecimento.yaml").read_text(encoding="utf-8")
    )
    saida = []
    for item in dados["itens"]:
        texto = item["resposta"].strip()
        faltam = set(re.findall(r"\{(\w+)\}", texto)) - set(fatos)
        if faltam:
            raise ValueError(f"fatos ausentes no item {item['id']}: {sorted(faltam)}")
        saida.append({**item, "resposta": texto.format(**fatos)})
    return saida


def montar(raiz: Path, config: dict[str, str] | None = None) -> dict[str, Any]:
    """Todos os arquivos da central, como objetos prontos para ``json.dumps``."""
    raiz = Path(raiz)
    equipes, partidas = _ler_partidas(raiz)
    modelo = _ler_modelo(raiz)
    fatos = _fatos(equipes, partidas, modelo)
    conhecimento = _conhecimento(raiz, fatos)
    escudos = {
        r["equipe"]: r["escudo_url"]
        for r in _ler_csv(raiz / "config" / "escudos.csv")
        if r["escudo_url"]
    }
    anos = sorted({p[0] for p in partidas})
    sugestoes = [p for item in conhecimento if item.get("sugerir") for p in item["perguntas"][:1]]
    return {
        "partidas": {
            "equipes": equipes,
            "colunas": ["ano", "data", "mandante", "visitante", "gm", "gv"],
            "partidas": partidas,
        },
        "modelo": modelo,
        "destaques": _destaques(raiz),
        "escudos": escudos,
        "conhecimento": conhecimento,
        "contexto": {
            "anos": anos,
            "equipes": equipes,
            "partidas": len(partidas),
            "temporadas": len(anos),
            "periodo": f"{anos[0]}–{anos[-1]}",
            "ultima_partida": max(p[1] for p in partidas),
            "mae_global": modelo["mae_teste"],
            "mae_baseline": modelo["mae_referencia_teste"],
            "cobertura": modelo["cobertura"],
            "modelo": modelo["modelo_nome"],
            "base": {"periodo": f"{anos[0]}–{anos[-1]}"},
        },
        "sugestoes": {"sugestoes": sugestoes},
        "config": config or {"powerbi_embed_url": "", "repo_url": "", "versao": "0.1.0"},
    }
