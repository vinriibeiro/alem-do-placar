"""Explicabilidade e avaliação científica do modelo congelado (T007; PRD 7.4 e 7.6).

Consome o resultado de ``models.backtesting.executar_backtest``. O modelo ajustado vem da memória
(``resultado["modelo_ajustado"]``); nenhum joblib ou pickle externo é carregado. A avaliação usa
somente o holdout do ano de holdout. A importância por permutação reutiliza o modelo congelado,
sem treino, e não altera seleção, parâmetros ou previsões.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from threadpoolctl import threadpool_limits

from features.temporais import ALVO, FEATURES, FIM_ALVO
from models.backtesting import BASELINE, BASELINE_HISTORICO, LIMITE_PREVISAO, SEED

VERSAO_AVALIACAO = "T007-1.0"
CHAVES_JUNCAO = ("equipe", "partida_id", "data_referencia")
COLUNAS_PREVISAO = ("previsao", "limite_inferior", "limite_superior")
COLUNAS_RESULTADO = (
    "previsoes",
    "modelo_ajustado",
    "modelo_selecionado",
    "metadados",
    "atributos",
    "metricas",
    "versao",
    "corte_treino",
)
N_PIORES_ERROS = 10
TOLERANCIA = 1e-8
ATRIBUTOS_MANDO = ("mando", "media_pontos_mandante_historico", "media_pontos_visitante_historico")
ATRIBUTOS_VOLATILIDADE = (
    "desvio_pontos_5",
    "media_saldo_gols_3",
    "media_saldo_gols_5",
    "media_saldo_gols_10",
)
ENUNCIADOS = {
    "H01": "Indicadores recentes de desempenho ajudam a prever a evolução futura das equipes.",
    "H02": "Médias móveis apresentam maior capacidade preditiva que médias históricas isoladas.",
    "H03": "Diferenças entre desempenho como mandante e visitante contribuem para as previsões.",
    "H04": "Volatilidade de resultados e saldo de gols ajudam a identificar mudanças de tendência.",
    "H05": "Modelos de Machine Learning podem superar modelos estatísticos baseline.",
    "H06": "Métricas avançadas, como xG, quando disponíveis, podem oferecer ganhos adicionais.",
}
LIMITACOES = (
    "Avaliação em um único holdout temporal e uma única competição; amostra pequena por equipe.",
    "Alvos de partidas consecutivas se sobrepõem no tempo; as observações não são independentes.",
    "Não há intervalo estatístico, valor-p ou teste de significância para os erros.",
    "A importância por permutação é preditiva e exploratória: não é estudo causal nem ablação, "
    "e atributos correlacionados podem dividir a importância.",
    "Erros por equipe têm n diferente; diferenças de pontos não são ranking de mérito.",
    "xG não está disponível; H06 não é avaliável e nenhum valor foi preenchido com zero.",
    "Dados observacionais: resultados não são causais nem recomendações de apostas.",
)


def avaliar_cientificamente(
    resultado: dict[str, Any],
    dataset: pd.DataFrame,
    pasta_saida: Path | None = None,
    n_repeticoes: int = 5,
) -> dict[str, Any]:
    """Calcula resíduos, métricas por grupo, importância por permutação e hipóteses.

    ``resultado`` é a saída de ``executar_backtest``; ``dataset`` é a saída de
    ``features.temporais.gerar_atributos``. Nenhum dos dois é modificado. Se ``pasta_saida``
    for informada, relatórios, tabelas e gráficos são gravados nela.
    """
    if n_repeticoes < 1:
        raise ValueError("n_repeticoes deve ser pelo menos 1")
    _conferir_resultado(resultado)
    ano = int(resultado["metadados"]["ano_holdout"])
    selecionado = str(resultado["modelo_selecionado"])
    modelo = resultado["modelo_ajustado"]
    base = _holdout(dataset, ano)
    alinhado = _alinhar(resultado["previsoes"], base)
    prevista = _prever(modelo, alinhado, selecionado)
    if not np.allclose(prevista, alinhado["previsao"].to_numpy(dtype=float), atol=TOLERANCIA):
        raise RuntimeError("previsões recalculadas divergem das previsões do backtesting")
    residuos = _residuos(alinhado)
    importancias = _importancias(
        modelo, alinhado, selecionado, list(resultado["atributos"]), n_repeticoes
    )
    comparacao = _comparacao(resultado["metricas"], selecionado)
    resposta = {
        "resumo": {
            "versao_avaliacao": VERSAO_AVALIACAO,
            "versao": str(resultado["versao"]),
            "modelo_selecionado": selecionado,
            "ano_holdout": ano,
            "corte_treino": str(resultado["corte_treino"]),
            "periodo_holdout": {
                "inicio": _data(residuos["data_referencia"].min()),
                "fim": _data(residuos["data_referencia"].max()),
            },
            "seed": SEED,
            "n_repeticoes": n_repeticoes,
            "metricas_holdout": _agregar(residuos),
            "comparacao": comparacao,
        },
        "residuos": residuos,
        "importancias": importancias,
        "por_equipe": _por_grupo(residuos, "equipe"),
        "por_temporada": _por_grupo(residuos, "temporada"),
        "piores_erros": residuos.sort_values("erro_absoluto", ascending=False, kind="mergesort")
        .head(N_PIORES_ERROS)
        .reset_index(drop=True),
        "hipoteses": _hipoteses(comparacao, importancias, selecionado, ano),
        "limitacoes": list(LIMITACOES),
    }
    if pasta_saida is not None:
        resposta["caminhos"] = _exportar(resposta, pasta_saida)
    return resposta


def _conferir_resultado(resultado: dict[str, Any]) -> None:
    faltantes = [c for c in COLUNAS_RESULTADO if c not in resultado]
    if faltantes:
        raise ValueError(f"resultado sem chaves obrigatórias: {faltantes}")
    if "ano_holdout" not in resultado["metadados"]:
        raise ValueError("metadados sem ano_holdout")


def _holdout(dataset: pd.DataFrame, ano: int) -> pd.DataFrame:
    if dataset.empty:
        raise ValueError("dataset vazio: nenhuma linha para avaliação")
    colunas = (*CHAVES_JUNCAO, "temporada", ALVO, FIM_ALVO, *FEATURES)
    faltantes = [c for c in colunas if c not in dataset.columns]
    if faltantes:
        raise ValueError(f"dataset sem colunas obrigatórias: {faltantes}")
    base = dataset[dataset["temporada"] == ano].dropna(subset=[ALVO, FIM_ALVO])
    if base.empty:
        raise ValueError(f"sem linhas elegíveis no holdout {ano}")
    return base.copy()


def _alinhar(previsoes: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    if previsoes.empty:
        raise ValueError("previsões vazias")
    colunas = [*CHAVES_JUNCAO, *COLUNAS_PREVISAO]
    faltantes = [c for c in colunas if c not in previsoes.columns]
    if faltantes:
        raise ValueError(f"previsões sem colunas obrigatórias: {faltantes}")
    # validate garante que cada chave apareça no máximo uma vez em cada lado.
    alinhado = previsoes[colunas].merge(
        base, on=list(CHAVES_JUNCAO), how="inner", validate="one_to_one"
    )
    if len(alinhado) != len(previsoes):
        raise ValueError("chaves de previsão sem correspondência no holdout")
    return alinhado


def _prever(modelo: Any, alinhado: pd.DataFrame, selecionado: str) -> np.ndarray:
    entrada = alinhado if selecionado == BASELINE else alinhado[list(FEATURES)]
    with threadpool_limits(limits=1):
        return np.clip(modelo.predict(entrada), *LIMITE_PREVISAO).astype(float)


def _residuos(alinhado: pd.DataFrame) -> pd.DataFrame:
    residuos = (
        alinhado[["equipe", "temporada", "data_referencia", "partida_id", ALVO, *COLUNAS_PREVISAO]]
        .rename(columns={ALVO: "alvo"})
        .reset_index(drop=True)
    )
    return residuos.assign(
        residuo=lambda t: t["previsao"] - t["alvo"],
        erro_absoluto=lambda t: t["residuo"].abs(),
        dentro_intervalo=lambda t: t["alvo"].between(t["limite_inferior"], t["limite_superior"]),
    )


def _importancias(
    modelo: Any,
    alinhado: pd.DataFrame,
    selecionado: str,
    atributos: list[str],
    n_repeticoes: int,
) -> pd.DataFrame:
    """Embaralha cada atributo no holdout congelado; delta = MAE embaralhado - MAE original."""
    y = alinhado[ALVO].to_numpy(dtype=float)
    mae_original = _mae(_prever(modelo, alinhado, selecionado), y)
    gerador = np.random.default_rng(SEED)
    linhas = []
    for atributo in atributos:
        deltas = []
        for _ in range(n_repeticoes):
            embaralhado = alinhado.copy()
            ordem = gerador.permutation(len(alinhado))
            embaralhado[atributo] = alinhado[atributo].to_numpy()[ordem]
            mae = _mae(_prever(modelo, embaralhado, selecionado), y)
            deltas.append(mae - mae_original)
        linhas.append(
            {
                "atributo": atributo,
                "delta_mae_media": float(np.mean(deltas)),
                "delta_mae_desvio": float(np.std(deltas, ddof=1)) if n_repeticoes > 1 else 0.0,
            }
        )
    return pd.DataFrame(linhas).sort_values(
        "delta_mae_media", ascending=False, kind="mergesort", ignore_index=True
    )


def _comparacao(metricas: pd.DataFrame, selecionado: str) -> dict[str, Any]:
    sel = _linha_metrica(metricas, "holdout", selecionado)
    base = _linha_metrica(metricas, "holdout", BASELINE)
    if sel is None or base is None:
        raise ValueError("metricas sem linhas de holdout para o selecionado e o baseline")
    return {
        "holdout": {
            "selecionado": sel,
            "baseline": base,
            "diferenca_mae_selecionado_menos_baseline": sel["mae"] - base["mae"],
        },
        "validacao": {
            "baseline_recente": _linha_metrica(metricas, "validacao", BASELINE),
            "media_historica": _linha_metrica(metricas, "validacao", BASELINE_HISTORICO),
        },
    }


def _linha_metrica(metricas: pd.DataFrame, fase: str, modelo: str) -> dict[str, Any] | None:
    linhas = metricas[
        (metricas["fase"] == fase)
        & (metricas["modelo"] == modelo)
        & (metricas["temporada"].astype(str) == "todas")
    ]
    if linhas.empty:
        return None
    linha = linhas.iloc[0]
    return {
        "mae": float(linha["mae"]),
        "rmse": float(linha["rmse"]),
        "vies": float(linha["vies"]),
        "n": int(linha["n"]),
    }


def _hipoteses(
    comparacao: dict[str, Any], importancias: pd.DataFrame, selecionado: str, ano: int
) -> list[dict[str, str]]:
    sel = comparacao["holdout"]["selecionado"]
    base = comparacao["holdout"]["baseline"]
    validacao = comparacao["validacao"]
    melhor = selecionado != BASELINE and sel["mae"] < base["mae"]
    comparativo = (
        f"Holdout {ano}: {selecionado} MAE {sel['mae']:.6f} (n={sel['n']}) contra "
        f"{BASELINE} MAE {base['mae']:.6f}."
    )
    nota_baseline = (
        " Modelo selecionado é o baseline; atributos não usados por ele têm delta zero."
        if selecionado == BASELINE
        else ""
    )
    m00, b01 = validacao["baseline_recente"], validacao["media_historica"]
    if m00 is None or b01 is None:
        status_h02 = "nao_avaliavel"
        evidencia_h02 = "Média histórica B01 ausente na validação."
    else:
        status_h02 = _status(m00["mae"] < b01["mae"])
        evidencia_h02 = (
            f"Validação: {BASELINE} MAE {m00['mae']:.6f} contra {BASELINE_HISTORICO} MAE "
            f"{b01['mae']:.6f}. B01 é média histórica global do treino, não por clube."
        )
    return [
        _hipotese(
            "H01",
            "observado_nesta_comparacao",
            f"{comparativo} Resultado observado, sem generalização.",
        ),
        _hipotese("H02", status_h02, evidencia_h02),
        _hipotese(
            "H03",
            "nao_conclusiva",
            _deltas(importancias, ATRIBUTOS_MANDO)
            + nota_baseline
            + " Importância preditiva exploratória; não é estudo causal nem ablação.",
        ),
        _hipotese(
            "H04",
            "nao_conclusiva",
            _deltas(importancias, ATRIBUTOS_VOLATILIDADE)
            + nota_baseline
            + " Importância preditiva exploratória; não é estudo causal nem ablação.",
        ),
        _hipotese(
            "H05",
            _status(melhor),
            comparativo
            + (
                " Nenhum modelo ML foi selecionado; baseline mantido."
                if not melhor and selecionado == BASELINE
                else ""
            )
            + " Sem generalização para outras temporadas ou competições.",
        ),
        _hipotese(
            "H06",
            "nao_avaliavel",
            "xG não está disponível no dataset; valores ausentes não foram preenchidos com zeros.",
        ),
    ]


def _hipotese(identificador: str, status: str, evidencia: str) -> dict[str, str]:
    return {
        "id": identificador,
        "enunciado": ENUNCIADOS[identificador],
        "status": status,
        "evidencia": evidencia,
    }


def _status(favoravel: bool) -> str:
    return "favoravel_nesta_comparacao" if favoravel else "desfavoravel_nesta_comparacao"


def _deltas(importancias: pd.DataFrame, atributos: tuple[str, ...]) -> str:
    recorte = importancias[importancias["atributo"].isin(atributos)]
    if recorte.empty:
        return "Atributos não avaliados."
    return "; ".join(
        f"{linha.atributo}: delta MAE {linha.delta_mae_media:+.6f} "
        f"(desvio {linha.delta_mae_desvio:.6f})"
        for linha in recorte.itertuples()
    )


def _agregar(grupo: pd.DataFrame) -> dict[str, Any]:
    residuo = grupo["residuo"].to_numpy(dtype=float)
    return {
        "n": int(len(grupo)),
        "mae": float(np.mean(np.abs(residuo))),
        "rmse": float(np.sqrt(np.mean(residuo**2))),
        "vies": float(np.mean(residuo)),
        "cobertura_intervalo": float(grupo["dentro_intervalo"].mean()),
    }


def _por_grupo(residuos: pd.DataFrame, chave: str) -> pd.DataFrame:
    return pd.DataFrame(
        [{chave: nome, **_agregar(grupo)} for nome, grupo in residuos.groupby(chave, sort=True)]
    )


def _mae(previsao: np.ndarray, alvo: np.ndarray) -> float:
    return float(np.mean(np.abs(previsao - alvo)))


def _data(valor: pd.Timestamp) -> str:
    return pd.Timestamp(valor).date().isoformat()


def _exportar(resposta: dict[str, Any], pasta: Path | str) -> dict[str, Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = {
        "relatorio_json": pasta / "relatorio_cientifico.json",
        "relatorio_md": pasta / "relatorio_cientifico.md",
        "importancias": pasta / "importancias.csv",
        "residuos": pasta / "residuos.parquet",
        "grafico_residuos": pasta / "residuos_hist.png",
        "grafico_previsto_observado": pasta / "previsto_vs_observado.png",
        "grafico_importancias": pasta / "importancias.png",
    }
    resposta["importancias"].to_csv(caminhos["importancias"], index=False, encoding="utf-8")
    resposta["residuos"].to_parquet(caminhos["residuos"], index=False)
    _graficos(resposta, caminhos)
    relatorio = {
        "resumo": resposta["resumo"],
        "hipoteses": resposta["hipoteses"],
        "limitacoes": resposta["limitacoes"],
        "importancias": _registros(resposta["importancias"]),
        "por_equipe": _registros(resposta["por_equipe"]),
        "por_temporada": _registros(resposta["por_temporada"]),
        "piores_erros": _registros(resposta["piores_erros"]),
    }
    caminhos["relatorio_json"].write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2, default=_jsonavel), encoding="utf-8"
    )
    caminhos["relatorio_md"].write_text(_markdown(resposta), encoding="utf-8")
    return caminhos


def _graficos(resposta: dict[str, Any], caminhos: dict[str, Path]) -> None:
    residuos = resposta["residuos"]
    importancias = resposta["importancias"]

    def residuos_hist(ax: Any) -> None:
        ax.hist(residuos["residuo"].to_numpy(), bins=30, color="#4C72B0")

    def previsto_observado(ax: Any) -> None:
        ax.scatter(residuos["alvo"], residuos["previsao"], s=12, alpha=0.6)
        ax.plot(LIMITE_PREVISAO, LIMITE_PREVISAO, linestyle="--", color="black", label="identidade")
        ax.set_xlim(LIMITE_PREVISAO)
        ax.set_ylim(LIMITE_PREVISAO)
        ax.legend()

    def barras(ax: Any) -> None:
        ax.barh(
            importancias["atributo"],
            importancias["delta_mae_media"],
            xerr=importancias["delta_mae_desvio"],
            color="#55A868",
        )
        ax.axvline(0, color="black", linewidth=0.8)
        ax.invert_yaxis()

    _figura(
        caminhos["grafico_residuos"],
        "Distribuição dos resíduos",
        ("previsão − alvo", "frequência"),
        residuos_hist,
    )
    _figura(
        caminhos["grafico_previsto_observado"],
        "Previsto versus observado",
        ("observado", "previsto"),
        previsto_observado,
    )
    _figura(
        caminhos["grafico_importancias"],
        "Importância por permutação (ΔMAE)",
        ("delta MAE", "atributo"),
        barras,
    )


def _figura(
    caminho: Path, titulo: str, rotulos: tuple[str, str], desenhar: Callable[[Any], None]
) -> None:
    # Figura sem pyplot e sem interface gráfica: canvas Agg direto, fechado após gravar.
    fig = Figure(figsize=(7, 4.5))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot()
    desenhar(ax)
    ax.set_title(titulo)
    ax.set_xlabel(rotulos[0])
    ax.set_ylabel(rotulos[1])
    fig.tight_layout()
    fig.savefig(caminho, format="png", dpi=120)
    fig.clear()


def _registros(tabela: pd.DataFrame) -> list[dict[str, Any]]:
    return tabela.astype(object).where(tabela.notna(), None).to_dict("records")


def _markdown(resposta: dict[str, Any]) -> str:
    r = resposta["resumo"]
    h = r["metricas_holdout"]
    c = r["comparacao"]
    sel, base = c["holdout"]["selecionado"], c["holdout"]["baseline"]
    val = c["validacao"]
    validacao = [
        {"modelo": nome, **linha}
        for nome, linha in (
            (BASELINE, val["baseline_recente"]),
            (BASELINE_HISTORICO, val["media_historica"]),
        )
        if linha is not None
    ]
    linhas = [
        "# Relatório científico — Além do Placar (T007)",
        "",
        f"- Versão da avaliação: {r['versao_avaliacao']}",
        f"- Versão do backtesting: {r['versao']}",
        f"- Modelo selecionado: {r['modelo_selecionado']}",
        f"- Holdout: {r['ano_holdout']}; período {r['periodo_holdout']['inicio']} a "
        f"{r['periodo_holdout']['fim']}",
        f"- Corte do treino: {r['corte_treino']}; seed {r['seed']}; "
        f"repetições de permutação: {r['n_repeticoes']}",
        "",
        "## Métricas no holdout",
        "",
        *_md_tabela([h], ["n", "mae", "rmse", "vies", "cobertura_intervalo"]),
        "## Comparação com o baseline (holdout)",
        "",
        *_md_tabela(
            [{"modelo": r["modelo_selecionado"], **sel}, {"modelo": BASELINE, **base}],
            ["modelo", "n", "mae", "rmse", "vies"],
        ),
        f"Diferença de MAE (selecionado menos baseline): "
        f"{c['holdout']['diferenca_mae_selecionado_menos_baseline']:.6f}.",
        "",
        "## Validação (média histórica disponível apenas nesta fase)",
        "",
        *_md_tabela(validacao, ["modelo", "n", "mae", "rmse", "vies"]),
        "## Importância por permutação (holdout congelado)",
        "",
        *_md_tabela(
            _registros(resposta["importancias"]),
            ["atributo", "delta_mae_media", "delta_mae_desvio"],
        ),
        "## Desempenho por equipe (sem ranking de mérito; n difere)",
        "",
        *_md_tabela(
            _registros(resposta["por_equipe"]),
            ["equipe", "n", "mae", "rmse", "vies", "cobertura_intervalo"],
        ),
        "## Desempenho por temporada",
        "",
        *_md_tabela(
            _registros(resposta["por_temporada"]),
            ["temporada", "n", "mae", "rmse", "vies", "cobertura_intervalo"],
        ),
        "## Erros extremos (maiores erros absolutos)",
        "",
        *_md_tabela(
            _registros(resposta["piores_erros"]),
            [
                "equipe",
                "data_referencia",
                "partida_id",
                "alvo",
                "previsao",
                "residuo",
                "dentro_intervalo",
            ],
        ),
        "## Hipóteses",
        "",
        *[
            f"- **{hip['id']}** ({hip['status']}): {hip['enunciado']} {hip['evidencia']}"
            for hip in resposta["hipoteses"]
        ],
        "",
        "## Limitações",
        "",
        *[f"- {texto}" for texto in LIMITACOES],
        "",
    ]
    return "\n".join(linhas)


def _md_tabela(registros: list[dict[str, Any]], colunas: list[str]) -> list[str]:
    cabecalho = "| " + " | ".join(colunas) + " |"
    separador = "|" + "|".join("---" for _ in colunas) + "|"
    corpo = ["| " + " | ".join(_formatar(linha[c]) for c in colunas) + " |" for linha in registros]
    return [cabecalho, separador, *corpo, ""]


def _formatar(valor: Any) -> str:
    if isinstance(valor, float):
        return f"{valor:.6f}"
    return str(valor)


def _jsonavel(valor: Any) -> Any:
    if isinstance(valor, np.generic):
        return valor.item()
    if isinstance(valor, (pd.Timestamp, Path)):
        return str(valor)
    raise TypeError(f"tipo não serializável: {type(valor).__name__}")
