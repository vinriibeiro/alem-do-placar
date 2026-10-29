"""Análise exploratória reproduzível sobre as tabelas Parquet da T003 (PRD 5 e T004).

Descreve gols, pontos, mando de campo, equipes e temporadas, e identifica anomalias sem
removê-las. Não há inferência causal. Os gráficos usam o backend Agg, sem interface gráfica
nem pyplot. Ausências são reportadas explicitamente; nada é preenchido silenciosamente.
"""

import json
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from processing.tabelas import PONTOS_DERROTA, PONTOS_EMPATE, PONTOS_VITORIA

TABELAS = ("dim_equipes", "dim_temporadas", "fato_partidas", "fato_desempenho_equipes")
RESULTADOS = ("H", "D", "A")
ROTULOS_RESULTADO = {
    "H": "Vitória do mandante",
    "D": "Empate",
    "A": "Vitória do visitante",
}
COLUNAS_NUCLEO = (
    "partida_id",
    "data_partida",
    "temporada",
    "equipe_mandante",
    "equipe_visitante",
    "gols_mandante",
    "gols_visitante",
    "resultado",
)
COLUNAS_BASE = (
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
    "temporada_id",
    "equipe_mandante_id",
    "equipe_visitante_id",
)

# PRD 2.2: período candidato 2015-2025. A temporada 2026 é reservada e não é analisada.
TEMPORADAS_PERMITIDAS = range(2015, 2026)
TEMPORADA_RESERVADA = 2026
# Limiar exploratório, não de exclusão: partidas com esse total de gols ou mais são listadas.
LIMITE_GOLS_EXTREMOS = 7
CASAS_DECIMAIS = 4
DPI = 120
COR_PRINCIPAL = "#1f4e79"


def carregar_base(pasta: Path) -> pd.DataFrame:
    """Lê as tabelas T003 de ``pasta`` e devolve uma linha por partida, com joins validados."""
    pasta = Path(pasta)
    tabelas: dict[str, pd.DataFrame] = {}
    for nome in TABELAS:
        caminho = pasta / f"{nome}.parquet"
        if not caminho.is_file():
            raise FileNotFoundError(f"tabela Parquet ausente: {caminho}")
        tabelas[nome] = pd.read_parquet(caminho)
    return _validar_base(_montar_base(tabelas))


def resumo_exploratorio(base: pd.DataFrame) -> dict[str, object]:
    """Resume a base em um dicionário JSON-serializável, sem remover nenhum registro."""
    _validar_base(base)
    gols_totais = base["gols_mandante"] + base["gols_visitante"]
    desempenho = _desempenho_equipes(base)
    return {
        "periodo": {
            "data_inicial": _data_iso(base["data_partida"].min()),
            "data_final": _data_iso(base["data_partida"].max()),
        },
        "temporadas": sorted(int(t) for t in base["temporada"].unique()),
        "quantidade_partidas": int(len(base)),
        "quantidade_equipes": int(
            pd.concat([base["equipe_mandante"], base["equipe_visitante"]]).nunique()
        ),
        "media_gols": {
            "mandante": _arred(base["gols_mandante"].mean()),
            "visitante": _arred(base["gols_visitante"].mean()),
            "total": _arred(gols_totais.mean()),
        },
        "distribuicao_resultados": _distribuicao(base["resultado"]),
        "por_temporada": _por_temporada(base),
        "por_mando": _linhas(_agregar(desempenho, ["mando"])),
        "por_equipe_temporada": _linhas(_agregar(desempenho, ["temporada", "equipe"])),
        "por_equipe": _linhas(_agregar(desempenho, ["equipe"])),
        "qualidade": _qualidade(base),
    }


def exportar_analise(base: pd.DataFrame, pasta_saida: Path) -> dict[str, Path]:
    """Grava ``resumo.json`` e três gráficos PNG em ``pasta_saida``; devolve os caminhos."""
    resumo = resumo_exploratorio(base)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho_resumo = pasta / "resumo.json"
    texto = json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
    caminho_resumo.write_text(texto + "\n", encoding="utf-8")
    return {
        "resumo": caminho_resumo,
        "gols_por_temporada": _grafico_gols_por_temporada(
            resumo["por_temporada"], pasta / "gols_por_temporada.png"
        ),
        "distribuicao_resultados": _grafico_distribuicao(
            resumo["distribuicao_resultados"], pasta / "distribuicao_resultados.png"
        ),
        "pontos_por_equipe": _grafico_pontos_por_equipe(
            resumo["por_equipe"], pasta / "pontos_por_equipe.png"
        ),
    }


def _montar_base(tabelas: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    equipes = tabelas["dim_equipes"]
    temporadas = tabelas["dim_temporadas"]
    partidas = tabelas["fato_partidas"]
    desempenho = tabelas["fato_desempenho_equipes"]
    if partidas.empty:
        raise ValueError("base vazia: fato_partidas não contém partidas")
    _exigir_chave_unica(equipes, "equipe_id", "dim_equipes")
    _exigir_chave_unica(temporadas, "temporada_id", "dim_temporadas")
    _exigir_chave_unica(partidas, "partida_id", "fato_partidas")
    mandos = desempenho.loc[desempenho["mando_campo"] == "mandante", ["partida_id", "rodada"]]
    _exigir_chave_unica(mandos, "partida_id", "fato_desempenho_equipes (mandante)")
    if not desempenho["partida_id"].isin(partidas["partida_id"]).all():
        raise ValueError(
            "join inválido: fato_desempenho_equipes tem partida_id ausente em fato_partidas"
        )

    dim_temporadas = temporadas.rename(columns={"ano": "temporada"})[
        ["temporada_id", "temporada", "competicao"]
    ]
    dim_mandante = equipes.rename(
        columns={"equipe_id": "equipe_mandante_id", "nome": "equipe_mandante"}
    )[["equipe_mandante_id", "equipe_mandante"]]
    dim_visitante = equipes.rename(
        columns={"equipe_id": "equipe_visitante_id", "nome": "equipe_visitante"}
    )[["equipe_visitante_id", "equipe_visitante"]]

    base = partidas.merge(mandos, on="partida_id", how="left", validate="one_to_one")
    base = _juntar(base, dim_temporadas, "temporada_id")
    base = _juntar(base, dim_mandante, "equipe_mandante_id")
    base = _juntar(base, dim_visitante, "equipe_visitante_id")
    base["rodada"] = base["rodada"].astype("Int64")
    base["data_partida"] = pd.to_datetime(base["data_partida"])
    ordenada = base.sort_values(["data_partida", "partida_id"], kind="mergesort")
    return ordenada.reset_index(drop=True)[list(COLUNAS_BASE)]


def _exigir_chave_unica(tabela: pd.DataFrame, chave: str, origem: str) -> None:
    if tabela[chave].duplicated().any():
        raise ValueError(f"chave duplicada em {origem}: {chave}")


def _juntar(base: pd.DataFrame, dimensao: pd.DataFrame, chave: str) -> pd.DataFrame:
    """Junta uma dimensão por many_to_one; chave sem correspondência gera erro, não nulo."""
    sem_correspondencia = ~base[chave].isin(dimensao[chave])
    if sem_correspondencia.any():
        raise ValueError(
            f"join inválido: {int(sem_correspondencia.sum())} linhas com {chave} "
            "sem correspondência na dimensão"
        )
    return base.merge(dimensao, on=chave, how="left", validate="many_to_one")


def _validar_base(base: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        raise ValueError("base vazia: nenhuma partida para análise exploratória")
    faltantes = [c for c in COLUNAS_NUCLEO if c not in base.columns]
    if faltantes:
        raise ValueError(f"base sem colunas obrigatórias: {faltantes}")
    if base[["gols_mandante", "gols_visitante"]].isna().any().any():
        raise ValueError("gols ausentes na base; a análise não preenche valores ausentes")
    if not base["resultado"].isin(RESULTADOS).all():
        raise ValueError("resultado fora de H, D e A")
    esperado = _resultado_esperado(base)
    divergentes = int((base["resultado"] != esperado).sum())
    if divergentes:
        raise ValueError(f"resultado inconsistente com os gols em {divergentes} partidas")
    anos = {int(a) for a in base["temporada"].unique()}
    if TEMPORADA_RESERVADA in anos:
        raise ValueError(
            "temporada 2026 é reservada para avaliação final (PRD 2.2) e não é analisada"
        )
    fora = sorted(anos - set(TEMPORADAS_PERMITIDAS))
    if fora:
        raise ValueError(f"temporadas fora do período candidato 2015-2025: {fora}")
    return base


def _resultado_esperado(base: pd.DataFrame) -> pd.Series:
    condicoes = [
        base["gols_mandante"] > base["gols_visitante"],
        base["gols_mandante"] == base["gols_visitante"],
    ]
    return pd.Series(np.select(condicoes, ["H", "D"], default="A"), index=base.index)


def _pontos(resultado: pd.Series, lado: str) -> pd.Series:
    """Pontos 3/1/0 (PRD 5.2) do lado informado ('mandante' ou 'visitante')."""
    vitoria = "H" if lado == "mandante" else "A"
    return pd.Series(
        np.select(
            [resultado == vitoria, resultado == "D"],
            [PONTOS_VITORIA, PONTOS_EMPATE],
            default=PONTOS_DERROTA,
        ),
        index=resultado.index,
    )


def _desempenho_equipes(base: pd.DataFrame) -> pd.DataFrame:
    """Duas linhas por partida, uma por equipe, com pontos e gols do ponto de vista dela."""
    partes = []
    lados = (
        ("mandante", "equipe_mandante", "gols_mandante", "gols_visitante", "H", "A"),
        ("visitante", "equipe_visitante", "gols_visitante", "gols_mandante", "A", "H"),
    )
    for lado, equipe, gols_pro, gols_contra, vitoria, derrota in lados:
        partes.append(
            pd.DataFrame(
                {
                    "temporada": base["temporada"],
                    "mando": lado,
                    "equipe": base[equipe],
                    "jogos": 1,
                    "vitorias": base["resultado"] == vitoria,
                    "empates": base["resultado"] == "D",
                    "derrotas": base["resultado"] == derrota,
                    "gols_pro": base[gols_pro],
                    "gols_contra": base[gols_contra],
                    "pontos": _pontos(base["resultado"], lado),
                }
            )
        )
    return pd.concat(partes, ignore_index=True)


def _agregar(desempenho: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    agregado = (
        desempenho.groupby(chaves, sort=True)
        .agg(
            jogos=("jogos", "sum"),
            vitorias=("vitorias", "sum"),
            empates=("empates", "sum"),
            derrotas=("derrotas", "sum"),
            gols_pro=("gols_pro", "sum"),
            gols_contra=("gols_contra", "sum"),
            pontos=("pontos", "sum"),
        )
        .reset_index()
    )
    agregado["saldo_gols"] = agregado["gols_pro"] - agregado["gols_contra"]
    return agregado


def _linhas(agregado: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {coluna: _valor(valor) for coluna, valor in linha.items()}
        for linha in agregado.to_dict("records")
    ]


def _por_temporada(base: pd.DataFrame) -> list[dict[str, object]]:
    linhas = []
    for temporada, grupo in base.groupby("temporada", sort=True):
        gols = grupo["gols_mandante"] + grupo["gols_visitante"]
        linhas.append(
            {
                "temporada": int(temporada),
                "partidas": int(len(grupo)),
                "gols_totais": int(gols.sum()),
                "media_gols": _arred(gols.mean()),
                "distribuicao_resultados": _distribuicao(grupo["resultado"]),
            }
        )
    return linhas


def _distribuicao(resultado: pd.Series) -> dict[str, dict[str, object]]:
    contagem = resultado.value_counts()
    total = len(resultado)
    return {
        r: {
            "quantidade": int(contagem.get(r, 0)),
            "proporcao": _arred(contagem.get(r, 0) / total),
        }
        for r in RESULTADOS
    }


def _qualidade(base: pd.DataFrame) -> dict[str, object]:
    gols_totais = base["gols_mandante"] + base["gols_visitante"]
    extremos = sorted(base.loc[gols_totais >= LIMITE_GOLS_EXTREMOS, "partida_id"].astype(str))
    rodadas_ausentes = int(base["rodada"].isna().sum()) if "rodada" in base else len(base)
    return {
        "partidas_duplicadas": int(base["partida_id"].duplicated().sum()),
        "confrontos_mesma_data_duplicados": int(
            base.duplicated(["data_partida", "equipe_mandante", "equipe_visitante"]).sum()
        ),
        "datas_ausentes": int(base["data_partida"].isna().sum()),
        "rodadas_ausentes": rodadas_ausentes,
        "mandante_igual_visitante": int(
            (base["equipe_mandante"] == base["equipe_visitante"]).sum()
        ),
        "placares_extremos": {
            "limite_gols_totais": LIMITE_GOLS_EXTREMOS,
            "quantidade": len(extremos),
            "partidas": extremos,
        },
    }


def _data_iso(valor: object) -> str | None:
    return None if pd.isna(valor) else pd.Timestamp(valor).date().isoformat()


def _arred(valor: object) -> float:
    return round(float(valor), CASAS_DECIMAIS)


def _valor(valor: object) -> object:
    return valor if isinstance(valor, str) else int(valor)


def _nova_figura(largura: float = 10, altura: float = 6) -> Figure:
    figura = Figure(figsize=(largura, altura), dpi=DPI)
    FigureCanvasAgg(figura)
    return figura


def _salvar(figura: Figure, destino: Path) -> Path:
    try:
        figura.tight_layout()
        figura.savefig(destino, format="png", dpi=DPI, bbox_inches="tight")
    finally:
        figura.clear()
    return destino


def _grafico_gols_por_temporada(linhas: list[dict[str, object]], destino: Path) -> Path:
    anos = [str(linha["temporada"]) for linha in linhas]
    medias = [linha["media_gols"] for linha in linhas]
    figura = _nova_figura()
    eixo = figura.subplots()
    barras = eixo.bar(anos, medias, color=COR_PRINCIPAL)
    eixo.bar_label(barras, fmt="%.2f", padding=3)
    eixo.set_title("Média de gols por partida em cada temporada", fontsize=14)
    eixo.set_xlabel("Temporada (ano)")
    eixo.set_ylabel("Gols por partida (média, em gols)")
    eixo.set_ylim(0, max(max(medias, default=0.0), 1.0) * 1.15)
    eixo.grid(axis="y", alpha=0.3)
    return _salvar(figura, destino)


def _grafico_distribuicao(distribuicao: Mapping[str, Mapping[str, object]], destino: Path) -> Path:
    quantidades = [distribuicao[r]["quantidade"] for r in RESULTADOS]
    rotulos = [f"{ROTULOS_RESULTADO[r]} ({r})" for r in RESULTADOS]
    textos = [
        f"{distribuicao[r]['quantidade']} ({distribuicao[r]['proporcao']:.1%})" for r in RESULTADOS
    ]
    figura = _nova_figura()
    eixo = figura.subplots()
    barras = eixo.bar(rotulos, quantidades, color=[COR_PRINCIPAL, "#7f7f7f", "#c55a11"])
    eixo.bar_label(barras, labels=textos, padding=3)
    eixo.set_title("Distribuição de resultados H/D/A no período", fontsize=14)
    eixo.set_xlabel("Resultado final (H = mandante vence; D = empate; A = visitante vence)")
    eixo.set_ylabel("Partidas (quantidade)")
    eixo.set_ylim(0, max(max(quantidades), 1) * 1.15)
    eixo.grid(axis="y", alpha=0.3)
    return _salvar(figura, destino)


def _grafico_pontos_por_equipe(linhas: list[dict[str, object]], destino: Path) -> Path:
    ordenadas = sorted(linhas, key=lambda linha: (-linha["pontos"], linha["equipe"]))
    nomes = [linha["equipe"] for linha in ordenadas][::-1]
    pontos = [linha["pontos"] for linha in ordenadas][::-1]
    figura = _nova_figura(altura=max(4.0, 0.45 * len(nomes) + 2))
    eixo = figura.subplots()
    barras = eixo.barh(nomes, pontos, color=COR_PRINCIPAL)
    eixo.bar_label(barras, padding=3)
    eixo.set_title("Pontos por equipe no período (regra 3/1/0)", fontsize=14)
    eixo.set_xlabel("Pontos acumulados no período (pontos)")
    eixo.set_ylabel("Equipe")
    eixo.set_xlim(0, max(max(pontos, default=0), 1) * 1.15)
    eixo.grid(axis="x", alpha=0.3)
    return _salvar(figura, destino)
