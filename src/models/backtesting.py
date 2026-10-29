"""Modelos e backtesting temporal com horizonte purgado (T006; PRD 6.2, 7.2 e 7.3).

Cada treino usa somente linhas cuja data de referência e cujo fim do alvo são estritamente
anteriores à primeira data do teste. O holdout não participa da seleção. Modelos são
persistidos apenas por joblib, e somente objetos criados por este módulo; pickles externos
nunca são carregados.
"""

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from features.temporais import ALVO, FEATURES, FIM_ALVO, HORIZONTE_ALVO

SEED = 42
VERSAO = "T006-1.0"
ANOS_VALIDACAO = (2022, 2023, 2024)
ANO_HOLDOUT = 2025
LIMITE_PREVISAO = (0.0, 3.0)
MELHORA_MINIMA = 0.02
PIORA_MAXIMA_ANUAL = 0.10
QUANTIL_INTERVALO = 0.90
MINIMO_TREINO = 20
MEDIA_RECENTE = "media_pontos_5"
BASELINE = "M00_media_recente_5"
BASELINE_HISTORICO = "B01_media_historica_treino"
MODELOS_ML = ("M01_ridge", "M02_random_forest", "M03_hist_gradient_boosting")
MODELOS = (BASELINE, *MODELOS_ML)
CHAVES_PREVISAO = ("equipe", "temporada", "data_referencia", "partida_id")
COLUNAS_OBRIGATORIAS = ("partida_id", "equipe", "temporada", "data_referencia", "pontos")
COLUNAS_PREVISAO = (
    "equipe",
    "temporada",
    "data_referencia",
    "partida_id",
    "alvo",
    "previsao",
    "modelo",
    "versao_modelo",
    "data_corte_treino",
    "horizonte",
    "limite_inferior",
    "limite_superior",
)


class _Baseline:
    """Marca os baselines, que recebem o quadro completo em vez de apenas as FEATURES."""


class _MediaRecente(_Baseline):
    """M00: média de pontos das últimas 5 partidas; sem valor, usa a média de pontos do treino."""

    def __init__(self, media_treino: float) -> None:
        self.media_treino = media_treino

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return X[MEDIA_RECENTE].fillna(self.media_treino).to_numpy(dtype=float)


class _MediaHistorica(_Baseline):
    """Referência adicional (H02): média do alvo no treino, constante."""

    def __init__(self, media_treino: float) -> None:
        self.media_treino = media_treino

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.media_treino)


def executar_backtest(
    dataset: pd.DataFrame,
    anos_validacao: tuple[int, ...] = ANOS_VALIDACAO,
    ano_holdout: int = ANO_HOLDOUT,
    pasta_saida: Path | None = None,
) -> dict[str, Any]:
    """Valida os modelos por temporada, escolhe um deles e ajusta o escolhido para o holdout.

    ``dataset`` é a saída de ``features.temporais.gerar_atributos``. Temporadas posteriores ao
    holdout não são processadas. Se ``pasta_saida`` for informada, os arquivos são gravados.
    """
    anos = tuple(int(ano) for ano in anos_validacao)
    if ano_holdout > 2025:
        raise ValueError("holdout fora do período aprovado: 2026 não é processado")
    if not anos or max(anos) >= ano_holdout:
        raise ValueError("anos de validação devem existir e ser anteriores ao holdout")
    _conferir_colunas(dataset)
    elegiveis = _elegiveis(dataset[dataset["temporada"] <= ano_holdout])

    validacao, tamanhos = _validar(elegiveis, anos)
    erros = validacao.assign(abs_erro=(validacao["previsao"] - validacao["alvo"]).abs())
    mae_por_ano = erros.groupby(["modelo", "temporada"])["abs_erro"].mean().unstack("temporada")
    escolhido, motivo = _selecionar(mae_por_ano)

    teste = _teste(elegiveis, ano_holdout)
    inicio = teste["data_referencia"].min()
    treino_final = _treino_ate(elegiveis[elegiveis["temporada"] < ano_holdout], inicio)
    _conferir_treino(treino_final, inicio)
    ajustes = {nome: _ajustar(nome, treino_final) for nome in dict.fromkeys((escolhido, BASELINE))}
    holdout = pd.concat(
        [_previsoes(teste, _predizer(m, teste), nome, "holdout") for nome, m in ajustes.items()],
        ignore_index=True,
    )

    # Intervalo empírico: quantil dos erros absolutos da validação do modelo escolhido.
    q = float(np.quantile(erros.loc[erros["modelo"] == escolhido, "abs_erro"], QUANTIL_INTERVALO))
    corte = inicio.date().isoformat()
    previsoes = (
        holdout[holdout["modelo"] == escolhido]
        .assign(
            limite_inferior=lambda t: (t["previsao"] - q).clip(*LIMITE_PREVISAO),
            limite_superior=lambda t: (t["previsao"] + q).clip(*LIMITE_PREVISAO),
            versao_modelo=VERSAO,
            data_corte_treino=corte,
            horizonte=HORIZONTE_ALVO,
        )[list(COLUNAS_PREVISAO)]
        .reset_index(drop=True)
    )
    cobertura = float(
        (
            (previsoes["alvo"] >= previsoes["limite_inferior"])
            & (previsoes["alvo"] <= previsoes["limite_superior"])
        ).mean()
    )

    avaliacoes = pd.concat([validacao, holdout], ignore_index=True)
    metricas = pd.concat(
        [
            _metricas(avaliacoes, ["fase", "modelo", "temporada"]),
            _metricas(avaliacoes, ["fase", "modelo"]).assign(temporada="todas"),
        ],
        ignore_index=True,
    )
    resultado = {
        "metricas": metricas,
        "metricas_equipe": _metricas(avaliacoes, ["fase", "modelo", "temporada", "equipe"]),
        "previsoes": previsoes,
        "modelo_selecionado": escolhido,
        "modelo_ajustado": ajustes[escolhido],
        "versao": VERSAO,
        "atributos": list(FEATURES),
        "corte_treino": corte,
        "resultados_validacao": validacao,
        "metadados": {
            "versao": VERSAO,
            "modelo_selecionado": escolhido,
            "motivo_selecao": motivo,
            "seed": SEED,
            "alvo": ALVO,
            "horizonte": HORIZONTE_ALVO,
            "atributos": list(FEATURES),
            "limites_previsao": list(LIMITE_PREVISAO),
            "anos_validacao": list(anos),
            "ano_holdout": ano_holdout,
            "corte_treino": corte,
            "n_treino_validacao": {str(ano): n for ano, n in tamanhos.items()},
            "n_treino_final": len(treino_final),
            "n_holdout": len(teste),
            "mae_validacao_baseline": float(mae_por_ano.loc[BASELINE].mean()),
            "mae_validacao_selecionado": float(mae_por_ano.loc[escolhido].mean()),
            "nivel_intervalo": QUANTIL_INTERVALO,
            "quantil_erro_absoluto": q,
            "cobertura_holdout": cobertura,
        },
    }
    if pasta_saida is not None:
        resultado["caminhos"] = salvar_resultados(resultado, pasta_saida)
    return resultado


def salvar_resultados(resultado: dict[str, Any], pasta: Path | str) -> dict[str, Path]:
    """Grava métricas, previsões, modelo próprio (joblib) e metadados; devolve os caminhos."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = {
        "metricas": pasta / "metricas.json",
        "metricas_equipe": pasta / "metricas_equipe.json",
        "previsoes": pasta / "previsoes.parquet",
        "modelo": pasta / "modelo.joblib",
        "metadados": pasta / "metadados.json",
    }
    _gravar_json(caminhos["metricas"], resultado["metricas"])
    _gravar_json(caminhos["metricas_equipe"], resultado["metricas_equipe"])
    resultado["previsoes"].to_parquet(caminhos["previsoes"], index=False)
    joblib.dump(resultado["modelo_ajustado"], caminhos["modelo"])
    _gravar_json(caminhos["metadados"], resultado["metadados"])
    return caminhos


def _construir(nome: str) -> Any:
    imputador = SimpleImputer(strategy="median", keep_empty_features=True)
    if nome == "M01_ridge":
        return make_pipeline(imputador, StandardScaler(), Ridge(alpha=1.0))
    if nome == "M02_random_forest":
        regressor = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=SEED, n_jobs=1)
        return make_pipeline(imputador, regressor)
    if nome == "M03_hist_gradient_boosting":
        regressor = HistGradientBoostingRegressor(max_iter=80, max_depth=4, random_state=SEED)
        return make_pipeline(imputador, regressor)
    raise ValueError(f"modelo desconhecido: {nome}")


def _ajustar(nome: str, treino: pd.DataFrame) -> Any:
    """Ajusta um modelo somente com o treino; imputação e escala são aprendidas aqui."""
    if nome == BASELINE:
        return _MediaRecente(float(treino["pontos"].mean()))
    if nome == BASELINE_HISTORICO:
        return _MediaHistorica(float(treino[ALVO].mean()))
    with threadpool_limits(limits=1):
        return _construir(nome).fit(treino[list(FEATURES)], treino[ALVO])


def _predizer(modelo: Any, teste: pd.DataFrame) -> np.ndarray:
    entrada = teste if isinstance(modelo, _Baseline) else teste[list(FEATURES)]
    with threadpool_limits(limits=1):
        return np.clip(modelo.predict(entrada), *LIMITE_PREVISAO)


def _validar(elegiveis: pd.DataFrame, anos: tuple[int, ...]) -> tuple[pd.DataFrame, dict]:
    linhas = []
    tamanhos = {}
    for ano in anos:
        teste = _teste(elegiveis, ano)
        inicio = teste["data_referencia"].min()
        treino = _treino_ate(elegiveis, inicio)
        _conferir_treino(treino, inicio)
        tamanhos[ano] = len(treino)
        for nome in (*MODELOS, BASELINE_HISTORICO):
            linhas.append(
                _previsoes(teste, _predizer(_ajustar(nome, treino), teste), nome, "validacao")
            )
    return pd.concat(linhas, ignore_index=True), tamanhos


def _selecionar(mae_por_ano: pd.DataFrame) -> tuple[str, str]:
    """Escolhe um modelo ML só com ganho mínimo no MAE médio e sem piora anual excessiva."""
    referencia = mae_por_ano.loc[BASELINE]
    media_base = referencia.mean()
    escolhido, media_escolhida = BASELINE, media_base
    for nome in MODELOS_ML:
        erros = mae_por_ano.loc[nome]
        media = erros.mean()
        ganho = media <= media_base * (1 - MELHORA_MINIMA)
        sem_piora = bool((erros <= referencia * (1 + PIORA_MAXIMA_ANUAL)).all())
        if ganho and sem_piora and media < media_escolhida:
            escolhido, media_escolhida = nome, media
    if escolhido == BASELINE:
        return escolhido, "ganho consistente não demonstrado; baseline mantido"
    return escolhido, "ganho mínimo de 2% no MAE médio e piora anual até 10%"


def _elegiveis(base: pd.DataFrame) -> pd.DataFrame:
    """Remove linhas sem alvo ou fim do alvo, em ordem cronológica."""
    ordenado = base.dropna(subset=[ALVO, FIM_ALVO])
    return ordenado.sort_values(["data_referencia", "partida_id", "equipe"]).reset_index(drop=True)


def _teste(elegiveis: pd.DataFrame, ano: int) -> pd.DataFrame:
    teste = elegiveis[elegiveis["temporada"] == ano]
    if teste.empty:
        raise ValueError(f"sem dados elegíveis para a temporada {ano}")
    return teste


def _treino_ate(elegiveis: pd.DataFrame, inicio: pd.Timestamp) -> pd.DataFrame:
    """Linhas cuja referência e cujo fim do alvo são estritamente anteriores a ``inicio``."""
    return elegiveis[(elegiveis["data_referencia"] < inicio) & (elegiveis[FIM_ALVO] < inicio)]


def _conferir_treino(treino: pd.DataFrame, inicio: pd.Timestamp) -> None:
    if len(treino) < MINIMO_TREINO:
        raise ValueError(
            f"treino insuficiente antes de {inicio.date()}: {len(treino)} linhas "
            f"(mínimo {MINIMO_TREINO})"
        )
    if treino[FIM_ALVO].max() >= inicio:
        raise RuntimeError("vazamento: rótulo de treino alcança o período de teste")


def _previsoes(teste: pd.DataFrame, previsao: np.ndarray, modelo: str, fase: str) -> pd.DataFrame:
    base = teste[[*CHAVES_PREVISAO, ALVO]].rename(columns={ALVO: "alvo"})
    return base.assign(previsao=previsao, modelo=modelo, fase=fase)


def _metricas(avaliacoes: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """MAE, RMSE, viés (previsão menos alvo) e contagem por grupo."""
    erro = avaliacoes["previsao"] - avaliacoes["alvo"]
    tabela = avaliacoes[chaves].assign(abs_erro=erro.abs(), quadrado=erro**2, erro=erro)
    agregada = (
        tabela.groupby(chaves, sort=True)
        .agg(
            mae=("abs_erro", "mean"),
            mse=("quadrado", "mean"),
            vies=("erro", "mean"),
            n=("erro", "size"),
        )
        .reset_index()
    )
    agregada["rmse"] = np.sqrt(agregada["mse"])
    return agregada[[*chaves, "mae", "rmse", "vies", "n"]]


def _conferir_colunas(dataset: pd.DataFrame) -> None:
    if dataset.empty:
        raise ValueError("dataset vazio: nenhuma linha para backtesting")
    colunas = (*COLUNAS_OBRIGATORIAS, *FEATURES, ALVO, FIM_ALVO)
    faltantes = [c for c in colunas if c not in dataset.columns]
    if faltantes:
        raise ValueError(f"dataset sem colunas obrigatórias: {faltantes}")


def _gravar_json(caminho: Path, conteudo: Any) -> None:
    if isinstance(conteudo, pd.DataFrame):
        conteudo = conteudo.astype(object).where(conteudo.notna(), None).to_dict("records")
    texto = json.dumps(conteudo, ensure_ascii=False, indent=2, default=_jsonavel)
    caminho.write_text(texto, encoding="utf-8")


def _jsonavel(valor: Any) -> Any:
    if isinstance(valor, np.generic):
        return valor.item()
    if isinstance(valor, (pd.Timestamp, Path)):
        return str(valor)
    raise TypeError(f"tipo não serializável: {type(valor).__name__}")
