"""Atributos temporais e alvo de cinco partidas (T005; PRD 6.2 e 7.1).

Entrada: uma linha por partida, no formato de ``evaluation.exploratoria.carregar_base``.
Saída: duas linhas por partida (uma por equipe), com atributos calculados somente a partir
de partidas já encerradas até a data de referência. A data de referência é a data da própria
partida, tratada como o fim dela: o atributo da partida atual pode usar o seu resultado.

O alvo ``media_pontos_futuros_5`` usa somente as cinco partidas seguintes da mesma equipe e
temporada, nunca a partida atual. Horizontes incompletos viram NaN, nunca média parcial.
A coluna ``resultado`` da entrada não é usada: pontos e saldo são derivados dos gols.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from processing.tabelas import PONTOS_DERROTA, PONTOS_EMPATE, PONTOS_VITORIA

COLUNAS_ENTRADA = (
    "partida_id",
    "data_partida",
    "temporada",
    "equipe_mandante",
    "equipe_visitante",
    "gols_mandante",
    "gols_visitante",
)
CHAVES_GRUPO = ("equipe", "temporada")
JANELAS_MEDIA = (3, 5, 10)
JANELA_DESVIO = 5
HORIZONTE_ALVO = 5
MANDANTE = 1
VISITANTE = 0
SEPARADOR_DATA_FINAL = "parquet"

ALVO = "media_pontos_futuros_5"
FIM_ALVO = "fim_alvo"

# Lista explícita. Não inclui identificadores, pontos/gols da partida atual, rodada nem o alvo.
FEATURES: tuple[str, ...] = (
    "media_pontos_3",
    "media_pontos_5",
    "media_pontos_10",
    "media_saldo_gols_3",
    "media_saldo_gols_5",
    "media_saldo_gols_10",
    "desvio_pontos_5",
    "media_pontos_mandante_historico",
    "media_pontos_visitante_historico",
    "jogos_acumulados",
    "dias_descanso",
    "mando",
)

COLUNAS_CONTEXTO = (
    "partida_id",
    "equipe",
    "adversario",
    "data_referencia",
    "temporada",
    "mando",
    "pontos",
    "gols_pro",
    "gols_contra",
    "saldo_gols",
)


def gerar_atributos(base: pd.DataFrame) -> pd.DataFrame:
    """Gera duas linhas por partida, com atributos temporais e o alvo de cinco partidas.

    A saída é ordenada por data de referência, ``partida_id`` e equipe. O resultado não depende
    da ordem das linhas da entrada.
    """
    longo = _desempenho_por_equipe(_validar_entrada(base))
    longo = longo.assign(
        **{
            f"media_pontos_{janela}": _por_grupo(longo, "pontos", _media_movel, janela)
            for janela in JANELAS_MEDIA
        },
        **{
            f"media_saldo_gols_{janela}": _por_grupo(longo, "saldo_gols", _media_movel, janela)
            for janela in JANELAS_MEDIA
        },
    )
    longo["desvio_pontos_5"] = _por_grupo(longo, "pontos", _desvio, JANELA_DESVIO)
    longo["jogos_acumulados"] = longo.groupby(list(CHAVES_GRUPO), sort=False).cumcount() + 1
    longo["dias_descanso"] = (
        longo.groupby(list(CHAVES_GRUPO), sort=False)["data_referencia"].diff().dt.days
    )
    longo["media_pontos_mandante_historico"] = _media_historica_mando(longo, MANDANTE)
    longo["media_pontos_visitante_historico"] = _media_historica_mando(longo, VISITANTE)
    longo[ALVO] = _por_grupo(longo, "pontos", _media_futura, HORIZONTE_ALVO)
    longo[FIM_ALVO] = longo.groupby(list(CHAVES_GRUPO), sort=False)["data_referencia"].shift(
        -HORIZONTE_ALVO
    )

    colunas = [*COLUNAS_CONTEXTO]
    if "rodada" in longo.columns:
        colunas.append("rodada")
    colunas += [*FEATURES, ALVO, FIM_ALVO]
    return longo[list(dict.fromkeys(colunas))].reset_index(drop=True)


def exportar_dataset(dataset: pd.DataFrame, caminho: Path | str) -> Path:
    """Grava o dataset analítico em Parquet e devolve o caminho gravado."""
    caminho = Path(caminho)
    if caminho.suffix.lower() != f".{SEPARADOR_DATA_FINAL}":
        raise ValueError("o dataset analítico deve ser exportado em Parquet (.parquet)")
    faltantes = [c for c in (*COLUNAS_CONTEXTO, *FEATURES, ALVO, FIM_ALVO) if c not in dataset]
    if faltantes:
        raise ValueError(f"dataset sem colunas obrigatórias: {faltantes}")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(caminho, index=False)
    return caminho


def _validar_entrada(base: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        raise ValueError("base vazia: nenhuma partida para gerar atributos")
    faltantes = [c for c in COLUNAS_ENTRADA if c not in base.columns]
    if faltantes:
        raise ValueError(f"base sem colunas obrigatórias: {faltantes}")
    tabela = base.copy()
    if tabela["partida_id"].isna().any():
        raise ValueError("partida_id ausente na base")
    if tabela["partida_id"].duplicated().any():
        raise ValueError("partida_id duplicado na base")
    tabela["data_partida"] = _datas(tabela["data_partida"])
    tabela["equipe_mandante"] = _nomes(tabela["equipe_mandante"], "equipe_mandante")
    tabela["equipe_visitante"] = _nomes(tabela["equipe_visitante"], "equipe_visitante")
    if (tabela["equipe_mandante"] == tabela["equipe_visitante"]).any():
        raise ValueError("mandante igual ao visitante em alguma partida")
    tabela["gols_mandante"] = _inteiros(tabela["gols_mandante"], "gols_mandante", minimo=0)
    tabela["gols_visitante"] = _inteiros(tabela["gols_visitante"], "gols_visitante", minimo=0)
    tabela["temporada"] = _inteiros(tabela["temporada"], "temporada", minimo=1)
    if "rodada" in tabela.columns:
        tabela["rodada"] = pd.to_numeric(tabela["rodada"], errors="raise").astype("Int64")
    return tabela


def _datas(serie: pd.Series) -> pd.Series:
    datas = pd.to_datetime(serie, errors="coerce")
    if datas.isna().any():
        raise ValueError("data_partida ausente ou inválida na base")
    return datas


def _nomes(serie: pd.Series, campo: str) -> pd.Series:
    nomes = serie.map(lambda valor: valor.strip() if isinstance(valor, str) else None)
    if nomes.isna().any() or (nomes == "").any():
        raise ValueError(f"{campo} ausente ou vazio na base")
    return nomes


def _inteiros(serie: pd.Series, campo: str, minimo: int) -> pd.Series:
    numeros = pd.to_numeric(serie, errors="coerce")
    if numeros.isna().any() or (numeros % 1 != 0).any() or (numeros < minimo).any():
        raise ValueError(f"{campo} deve ser inteiro, preenchido e >= {minimo}")
    return numeros.astype("int64")


def _desempenho_por_equipe(base: pd.DataFrame) -> pd.DataFrame:
    """Duas linhas por partida, ordenadas por data de referência, partida e equipe."""
    longo = pd.concat(
        [_lado(base, MANDANTE), _lado(base, VISITANTE)],
        ignore_index=True,
    )
    if longo.duplicated(["equipe", "temporada", "data_referencia"]).any():
        raise ValueError("referência temporal ambígua: equipe com partidas no mesmo instante")
    return longo.sort_values(["data_referencia", "partida_id", "equipe"]).reset_index(drop=True)


def _lado(base: pd.DataFrame, mando: int) -> pd.DataFrame:
    if mando == MANDANTE:
        equipe, adversario = "equipe_mandante", "equipe_visitante"
        gols_pro, gols_contra = "gols_mandante", "gols_visitante"
    else:
        equipe, adversario = "equipe_visitante", "equipe_mandante"
        gols_pro, gols_contra = "gols_visitante", "gols_mandante"
    pro = base[gols_pro]
    contra = base[gols_contra]
    lado = pd.DataFrame(
        {
            "partida_id": base["partida_id"],
            "equipe": base[equipe],
            "adversario": base[adversario],
            "data_referencia": base["data_partida"],
            "temporada": base["temporada"],
            "mando": mando,
            "pontos": _pontos(pro, contra),
            "gols_pro": pro,
            "gols_contra": contra,
            "saldo_gols": pro - contra,
        }
    )
    if "rodada" in base.columns:
        lado["rodada"] = base["rodada"]
    return lado


def _pontos(gols_pro: pd.Series, gols_contra: pd.Series) -> pd.Series:
    """Pontos 3/1/0 (PRD 5.2) calculados a partir dos gols."""
    return pd.Series(
        np.select(
            [gols_pro > gols_contra, gols_pro == gols_contra],
            [PONTOS_VITORIA, PONTOS_EMPATE],
            default=PONTOS_DERROTA,
        ),
        index=gols_pro.index,
        dtype="int64",
    )


def _por_grupo(longo: pd.DataFrame, coluna: str, funcao, *args: int) -> pd.Series:
    """Aplica ``funcao`` a ``coluna`` separadamente em cada equipe e temporada."""
    return longo.groupby(list(CHAVES_GRUPO), sort=False)[coluna].transform(funcao, *args)


def _media_movel(serie: pd.Series, janela: int) -> pd.Series:
    """Média dos últimos ``janela`` valores, incluindo o atual; NaN sem janela completa."""
    return serie.rolling(janela, min_periods=janela).mean()


def _desvio(serie: pd.Series, janela: int) -> pd.Series:
    """Desvio-padrão amostral com ddof=0 e min_periods=1 (amostra pequena)."""
    return serie.rolling(janela, min_periods=1).std(ddof=0)


def _media_futura(serie: pd.Series, horizonte: int) -> pd.Series:
    """Média dos ``horizonte`` valores seguintes, sem incluir o atual; NaN se incompleta."""
    media_a_partir_de_i = serie.iloc[::-1].rolling(horizonte, min_periods=horizonte).mean()
    return media_a_partir_de_i.iloc[::-1].shift(-1)


def _media_historica_mando(longo: pd.DataFrame, mando: int) -> pd.Series:
    """Média de pontos em jogos como mandante ou visitante, até a data de referência.

    Inclui a partida atual quando ela tem o mesmo mando. Antes do primeiro jogo nesse mando, NaN.
    """
    chaves = [longo["equipe"], longo["temporada"]]
    pontos = longo["pontos"].where(longo["mando"] == mando)
    soma = pontos.groupby(chaves).cumsum()
    quantidade = pontos.notna().astype("int64").groupby(chaves).cumsum()
    media = soma / quantidade.where(quantidade > 0)
    return media.groupby(chaves).ffill()
