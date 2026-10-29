"""Assistente local de consultas em português (T009; PRD 9.3 a 9.5).

Sem LLM externo, sem rede e sem SQL montado a partir da pergunta. A pergunta é classificada em
intenções fechadas por palavras-chave normalizadas, e cada intenção chama uma consulta fixa sobre
arquivos locais lidos uma única vez na inicialização. Nada da pergunta é executado.
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from processing.padronizacao import normalizar_texto

NAO_CALCULAVEL = (
    "Não é possível calcular essa informação com os dados atualmente disponíveis no projeto."
)
METODO = (
    "Interpretação determinística em português, com intenções fechadas e consultas fixas sobre "
    "arquivos locais; sem LLM externo, sem rede e sem SQL gerado a partir da pergunta."
)
LIMITACAO_METODO = "consultas locais autorizadas, sem LLM externo"
LIMITACAO_XG = "xG não está disponível no projeto; nenhum valor foi estimado."
SUPORTADAS = (
    "Perguntas suportadas: erro das previsões, previsão de uma equipe, variáveis mais "
    "influentes, evolução, queda e consistência."
)
FONTE_HISTORICO = "Dataset analítico (histórico 2018–2025)"
FONTE_PREVISAO = "Previsões retrospectivas do holdout (2025)"
FONTE_IMPORTANCIA = "Importância por permutação (holdout)"
MIN_JOGOS_EVOLUCAO = 11
MIN_JOGOS_CONSISTENCIA = 2
JANELA_EVOLUCAO = 10
TOP_VARIAVEIS = 5
ARQUIVOS = {
    "hist": ("processed", "dataset_analitico.parquet"),
    "prev": ("predictions", "modelagem", "previsoes.parquet"),
    "metricas": ("predictions", "modelagem", "metricas.json"),
    "meta": ("predictions", "modelagem", "metadados.json"),
    "imp": ("predictions", "cientifica", "importancias.csv"),
}
NOMES = {
    "hist": "histórico analítico",
    "prev": "previsões",
    "metricas": "métricas",
    "meta": "metadados do modelo",
    "imp": "importâncias",
}
COLUNAS_HIST = ("equipe", "temporada", "data_referencia", "pontos", "media_pontos_5")
COLUNAS_IMP = ("atributo", "delta_mae_media", "delta_mae_desvio")
# Nomes aceitos para cada campo das previsões; ausentes ficam como NaN, nunca como zero.
ALIAS_PREV = {
    "equipe": ("equipe",),
    "data_referencia": ("data_referencia", "data_corte"),
    "previsao": ("previsao", "media_pontos_prevista", "previsto"),
    "limite_inferior": ("limite_inferior", "inferior"),
    "limite_superior": ("limite_superior", "superior"),
    "observado": ("observado", "media_pontos_futuros_5", "alvo"),
}
PALAVRAS_GENERICAS = frozenset({"clube", "clubes", "futebol", "esporte", "equipe", "temporada"})
# Radicais por intenção; a ordem define a prioridade.
RADICAIS = (
    ("importancia", ("variav", "influenc", "import", "fator")),
    ("erro", ("erro", "mae", "rmse", "precis")),
    ("consistencia", ("consisten", "estavel", "regular")),
    ("previsao", ("prev",)),
    ("evolucao", ("evolu", "tendenc", "queda", "declin", "cresc")),
)
QUEDA = ("queda", "declin", "cai")


def _tokens(texto: str) -> list[str]:
    return re.findall(r"\w+", normalizar_texto(texto).lower())


def _chave(nome: str) -> str:
    return " ".join(_tokens(nome))


def _arred(valor) -> float | None:
    return None if pd.isna(valor) else round(float(valor), 3)


def _intencao(tokens: list[str]) -> str | None:
    if "porque" in tokens or {"por", "que"} <= set(tokens):
        return "explicacao" if any(t.startswith(("model", "prev")) for t in tokens) else None
    for nome, radicais in RADICAIS:
        if any(t.startswith(r) for t in tokens for r in radicais):
            return nome
    return None


def _candidatas(texto: str, equipes: dict[str, str]) -> list[str]:
    """Equipes cujo nome completo, ou token significativo, aparece no texto."""
    alvo = " ".join(_tokens(texto))
    completas = [o for n, o in equipes.items() if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", alvo)]
    restante = alvo
    for nome, original in equipes.items():
        if original in completas:
            restante = re.sub(rf"(?<!\w){re.escape(nome)}(?!\w)", " ", restante)
    tokens = [t for t in restante.split() if len(t) >= 4 and t not in PALAVRAS_GENERICAS]
    return sorted(
        set(completas)
        | {
            o
            for n, o in equipes.items()
            if any(t in n.split() or n.replace(" ", "").endswith(t) for t in tokens)
        }
    )


def _exigir(df: pd.DataFrame, colunas: tuple[str, ...]) -> None:
    if any(c not in df.columns for c in colunas):
        raise ValueError("colunas obrigatórias ausentes")


def _ler_historico(caminho: Path) -> pd.DataFrame:
    df = pd.read_parquet(caminho)
    _exigir(df, COLUNAS_HIST)
    if df.empty:
        raise ValueError("histórico vazio")
    df = df.assign(
        equipe=df["equipe"].astype(str),
        temporada=df["temporada"].astype(int),
        data_referencia=pd.to_datetime(df["data_referencia"]),
    )
    return df.sort_values(["equipe", "temporada", "data_referencia"]).reset_index(drop=True)


def _ler_previsoes(caminho: Path) -> pd.DataFrame:
    df = pd.read_parquet(caminho)
    colunas = {
        campo: next((c for c in nomes if c in df.columns), None)
        for campo, nomes in ALIAS_PREV.items()
    }
    if any(colunas[c] is None for c in ("equipe", "data_referencia", "previsao")):
        raise ValueError("colunas obrigatórias ausentes")
    out = pd.DataFrame({campo: (df[col] if col else np.nan) for campo, col in colunas.items()})
    for campo in ("previsao", "limite_inferior", "limite_superior", "observado"):
        out[campo] = pd.to_numeric(out[campo], errors="coerce")
    out = out.assign(
        equipe=out["equipe"].astype(str),
        data_referencia=pd.to_datetime(out["data_referencia"]),
    )
    out["temporada"] = out["data_referencia"].dt.year.astype(int)
    return out.dropna(subset=["previsao"]).reset_index(drop=True)


def _ler_importancias(caminho: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho)
    _exigir(df, COLUNAS_IMP)
    if df.empty or df[list(COLUNAS_IMP)].isna().any().any():
        raise ValueError("importâncias vazias ou incompletas")
    for coluna in ("delta_mae_media", "delta_mae_desvio"):
        df[coluna] = pd.to_numeric(df[coluna], errors="raise")
        if not np.isfinite(df[coluna]).all():
            raise ValueError("importâncias não finitas")
    return df.reset_index(drop=True)


def _ler_json(caminho: Path) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        raise ValueError("JSON inesperado")
    return dados


class BaseConsultas:
    """Lê uma vez os arquivos locais e responde por intenções fechadas."""

    def __init__(self, raiz: Path) -> None:
        raiz = Path(raiz)
        self._faltas: list[str] = []
        self._hist = self._carregar(raiz, "hist", _ler_historico)
        self._prev = self._carregar(raiz, "prev", _ler_previsoes)
        self._imp = self._carregar(raiz, "imp", _ler_importancias)
        self._meta = self._carregar(raiz, "meta", _ler_json) or {}
        self._metricas = self._carregar(
            raiz, "metricas", lambda p: json.loads(p.read_text(encoding="utf-8"))
        )
        self._bases = {"hist": self._hist, "prev": self._prev, "imp": self._imp}
        if self._hist is not None:
            self._anos = sorted(int(a) for a in self._hist["temporada"].unique())
            self._equipes = {_chave(n): str(n) for n in self._hist["equipe"].unique()}
        else:
            self._anos, self._equipes = [], {}
        # intenção: (handler, bases necessárias, usa ano, usa equipe)
        self._consultas = {
            "erro": (self._erro, ("hist", "prev"), True, True),
            "previsao": (self._previsao, ("hist", "prev"), True, True),
            "importancia": (self._importancia, ("imp",), False, False),
            "explicacao": (self._explicacao, ("imp",), False, False),
            "consistencia": (self._consistencia, ("hist",), True, True),
            "evolucao": (self._evolucao, ("hist",), True, True),
        }

    def _carregar(self, raiz: Path, nome: str, leitor):
        try:
            return leitor(Path(raiz, "data", *ARQUIVOS[nome]))
        except (OSError, ValueError, KeyError, TypeError):
            self._faltas.append(NOMES[nome])
            return None

    def responder(self, pergunta: str, ano: int | None = None, equipe: str | None = None) -> dict:
        tokens = _tokens(pergunta)
        if {"xg", "expected"} & set(tokens):
            return self._resposta(
                "indisponivel",
                f"{NAO_CALCULAVEL} {LIMITACAO_XG}",
                limitacoes=[LIMITACAO_XG],
            )
        intencao = _intencao(tokens)
        if intencao is None:
            return self._resposta(
                "fora_escopo",
                f"{NAO_CALCULAVEL} A pergunta não corresponde a uma consulta autorizada.",
                limitacoes=[SUPORTADAS],
            )
        handler, bases, usa_ano, usa_equipe = self._consultas[intencao]
        if intencao in {"previsao", "erro", "importancia", "explicacao"} and any(
            not isinstance(self._meta.get(campo), str) or not self._meta[campo].strip()
            for campo in ("modelo_selecionado", "versao", "corte_treino")
        ):
            return self._resposta(
                "indisponivel",
                "Análises do modelo indisponíveis: faltam modelo, versão ou corte de treino nos "
                "metadados locais. Nenhuma previsão foi apresentada sem rastreabilidade.",
            )
        faltam = [NOMES[b] for b in bases if self._bases[b] is None]
        if faltam:
            return self._resposta(
                "indisponivel",
                f"Dados locais ausentes para esta consulta: {', '.join(faltam)}. "
                "Nenhum valor foi estimado.",
            )
        ano_ef, erro = self._resolver_ano(pergunta, ano)
        if erro:
            return erro
        if not usa_ano and ano_ef != self._meta.get("ano_holdout"):
            return self._resposta(
                "indisponivel",
                "A importância está disponível somente para o holdout de "
                f"{self._meta.get('ano_holdout')}; o ano solicitado não foi substituído.",
            )
        equipe_ef = None
        if usa_equipe:
            equipe_ef, erro = self._resolver_equipe(pergunta, equipe)
            if erro:
                return erro
        return handler(ano_ef, equipe_ef, tokens)

    def contexto(self) -> dict:
        mae = None
        rastreavel = all(
            isinstance(self._meta.get(campo), str) and self._meta[campo].strip()
            for campo in ("modelo_selecionado", "versao", "corte_treino")
        )
        if self._prev is not None and rastreavel:
            erro = (self._prev["previsao"] - self._prev["observado"]).abs().dropna()
            mae = round(float(erro.mean()), 3) if len(erro) else None
        base = {
            "status": "ok" if self._hist is not None else "indisponivel",
            "faltantes": list(self._faltas),
            "metricas": self._metricas is not None,
        }
        if self._hist is not None:
            base |= {
                "observacoes": len(self._hist),
                "periodo": f"{self._anos[0]}–{self._anos[-1]}",
            }
        metricas = self._metricas if isinstance(self._metricas, list) else []
        baseline = next(
            (
                r.get("mae")
                for r in metricas
                if r.get("fase") == "holdout"
                and r.get("modelo") == "M00_media_recente_5"
                and str(r.get("temporada")) == "todas"
            ),
            None,
        )
        return {
            "anos": self._anos,
            "equipes": sorted(self._equipes.values()),
            "mae_global": mae,
            "mae_baseline": baseline if rastreavel else None,
            "modelo": self._meta.get("modelo_selecionado"),
            "versao_modelo": self._meta.get("versao"),
            "corte_treino": self._meta.get("corte_treino"),
            "base": base,
            "cobertura": self._meta.get("cobertura_holdout") if rastreavel else None,
            "metodo": METODO,
        }

    def _resposta(self, status, texto, dados=None, fonte=None, periodo=None, limitacoes=()):
        return {
            "status": status,
            "texto": texto,
            "dados": dados or [],
            "fonte": fonte,
            "periodo": periodo,
            "modelo": self._meta.get("modelo_selecionado"),
            "versao_modelo": self._meta.get("versao"),
            "limitacoes": [LIMITACAO_METODO, *limitacoes],
        }

    def _resolver_ano(self, pergunta: str, ano: int | None):
        if not self._anos:
            return None, self._resposta("indisponivel", "Histórico local vazio ou indisponível.")
        citados = sorted({int(a) for a in re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", pergunta)})
        if len(citados) > 1:
            return None, self._resposta(
                "esclarecimento",
                "A pergunta cita mais de um ano. Escolha um ano por pergunta: "
                + ", ".join(map(str, citados))
                + ".",
            )
        escolhido = citados[0] if citados else ano
        if escolhido is None:
            return self._anos[-1], None
        if escolhido not in self._anos:
            return None, self._resposta(
                "indisponivel",
                f"O ano {escolhido} não consta nos dados disponíveis "
                f"({self._anos[0]} a {self._anos[-1]}). Nenhum outro ano foi usado no lugar.",
            )
        return escolhido, None

    def _resolver_equipe(self, pergunta: str, equipe: str | None):
        citadas = _candidatas(pergunta, self._equipes)
        vocabulario = set(
            "qual quais e o a os as um uma de do da dos das para em no na nos nas por que "
            "como quanto quantos quando tem foi foram apresenta apresentam esta estao mais menos "
            "medio media erro mae rmse modelo modelos geral global todas todos equipe equipes "
            "clube clubes previsao previsoes estimativa estimado pontos desempenho evoluiu "
            "evolucao tendencia tendencias queda declinio crescimento cresceu consistente "
            "consistencia regular regularidade estavel estabilidade ultimas ultimos partidas "
            "jogos rodada rodadas temporada temporadas ano anos historico historica recente "
            "recentes melhor pior mostre mostrar informe informar calcula calcular calculado "
            "existe existe dados futebol brasileira brasileiro brasileirao campeonato "
            "respectivo respectivas total totais cada com sem atual anterior anteriormente "
            "dez cinco tres duas dois um quatro seis sete oito nove vinte trinta".split()
        )
        nomes = {t for nome in self._equipes for t in nome.split()}
        desconhecidos = {
            t
            for t in _tokens(pergunta)
            if not t.isdigit()
            and t not in vocabulario
            and t not in nomes
            and not any(
                len(t) >= 4 and nome.replace(" ", "").endswith(t)
                for nome, original in self._equipes.items()
                if original in citadas
            )
        }
        if desconhecidos:
            return None, self._resposta(
                "esclarecimento",
                "Não consegui identificar com segurança o clube ou o escopo da pergunta. "
                "Escolha uma equipe da lista ou use uma pergunta de exemplo.",
            )
        mencao = re.search(
            r"\b(?:do|da|de|para o|para a|para)\s+(.+?)(?:\s+em\s+\d{4}|[?!.]|$)",
            normalizar_texto(pergunta).lower(),
        )
        genericos = {
            "modelo",
            "todas as equipes",
            "previsao",
            "previsoes",
            "pontos",
            "dados",
            "queda",
            "crescimento",
            "evolucao",
            "consistencia",
        }
        if not citadas and mencao and mencao[1].strip() not in genericos:
            return None, self._resposta(
                "esclarecimento",
                "Não reconheci a equipe citada. Escolha uma equipe da lista; "
                "nenhum outro filtro foi aplicado.",
            )
        if equipe and not _candidatas(equipe, self._equipes):
            return None, self._resposta(
                "indisponivel", "A equipe selecionada não está no catálogo."
            )
        for texto in (pergunta, equipe or ""):
            candidatas = _candidatas(texto, self._equipes)
            if len(candidatas) == 1:
                return candidatas[0], None
            if candidatas:
                return None, self._resposta(
                    "esclarecimento",
                    "Mais de uma equipe corresponde a esse nome: "
                    + ", ".join(candidatas)
                    + ". Informe o nome completo.",
                )
        return None, None

    @staticmethod
    def _periodo(ano: int, datas: pd.Series) -> str:
        if datas.empty:
            return str(ano)
        return f"{ano}: de {datas.min():%d/%m/%Y} a {datas.max():%d/%m/%Y}"

    def _previsoes(self, ano: int, equipe: str | None = None) -> pd.DataFrame:
        p = self._prev[self._prev["temporada"] == ano]
        return p if equipe is None else p[p["equipe"] == equipe]

    def _sem_previsao(self, ano: int, equipe: str | None) -> dict:
        disponiveis = ", ".join(str(a) for a in sorted(self._prev["temporada"].unique()))
        alvo = f"para {equipe} " if equipe else ""
        return self._resposta(
            "sem_dados",
            f"Não há previsão retrospectiva {alvo}em {ano}. "
            f"Anos com previsões retrospectivas: {disponiveis}.",
            fonte=FONTE_PREVISAO,
        )

    def _erro(self, ano: int, equipe: str | None, _tokens_) -> dict:
        if self._prev["observado"].notna().sum() == 0:
            return self._resposta(
                "indisponivel", "Os valores observados não estão disponíveis nas previsões."
            )
        p = self._previsoes(ano, equipe).dropna(subset=["previsao", "observado"])
        if p.empty:
            return self._sem_previsao(ano, equipe)
        erro = p["previsao"] - p["observado"]
        mae, rmse, vies = erro.abs().mean(), np.sqrt((erro**2).mean()), erro.mean()
        escopo = (
            f"da equipe {equipe}"
            if equipe
            else "geral, de todas as equipes (não é o erro individual de um clube)"
        )
        dados = [
            {
                "escopo": equipe or "geral",
                "mae": _arred(mae),
                "rmse": _arred(rmse),
                "vies": _arred(vies),
                "n": len(p),
            }
        ]
        texto = (
            f"Erro {escopo} nas previsões retrospectivas de {ano}: MAE de {mae:.3f} pontos, "
            f"RMSE de {rmse:.3f} pontos e viés médio de {vies:+.3f} (previsão menos observado), "
            f"em {len(p)} previsões."
        )
        return self._resposta(
            "ok",
            texto,
            dados,
            FONTE_PREVISAO,
            self._periodo(ano, p["data_referencia"]),
            ["Erros de previsões passadas (retrospectivas), não de previsões atuais."],
        )

    def _previsao(self, ano: int, equipe: str | None, _tokens_) -> dict:
        if equipe is None:
            return self._resposta(
                "esclarecimento",
                "Informe a equipe para consultar a previsão, por exemplo: "
                "'Qual é a previsão do Flamengo?'.",
            )
        p = self._previsoes(ano, equipe)
        if p.empty:
            return self._sem_previsao(ano, equipe)
        r = p.sort_values("data_referencia").iloc[-1]
        inf, sup, obs = r["limite_inferior"], r["limite_superior"], r["observado"]
        faixa = (
            f"faixa de {inf:.2f} a {sup:.2f}"
            if pd.notna(inf) and pd.notna(sup)
            else "faixa indisponível"
        )
        texto = (
            f"Previsão retrospectiva de {ano} para {equipe}: média estimada de "
            f"{r['previsao']:.2f} pontos nas próximas 5 partidas ({faixa}), com data de "
            f"referência em {r['data_referencia']:%d/%m/%Y}. Não é previsão atual nem de 2026."
        )
        texto += f" Corte exclusivo do treino: {self._meta['corte_treino']}."
        if pd.notna(obs):
            texto += f" Resultado observado nesse horizonte: média de {obs:.2f} pontos."
        dados = [
            {
                "equipe": equipe,
                "data_referencia": r["data_referencia"].date().isoformat(),
                "previsao": _arred(r["previsao"]),
                "limite_inferior": _arred(inf),
                "limite_superior": _arred(sup),
                "observado": _arred(obs),
            }
        ]
        return self._resposta(
            "ok",
            texto,
            dados,
            FONTE_PREVISAO,
            self._periodo(ano, p["data_referencia"]),
            ["Previsão estatística, não certeza nem recomendação; intervalo empírico."],
        )

    def _importancia(self, _ano, _equipe, _tokens_, prefixo: str = "") -> dict:
        top = self._imp.sort_values("delta_mae_media", ascending=False).head(TOP_VARIAVEIS)
        dados = [
            {
                "posicao": i,
                "atributo": r["atributo"],
                "delta_mae_media": _arred(r["delta_mae_media"]),
                "delta_mae_desvio": _arred(r["delta_mae_desvio"]),
            }
            for i, (_, r) in enumerate(top.iterrows(), 1)
        ]
        lista = "; ".join(
            f"{d['posicao']}. {d['atributo']} ({d['delta_mae_media']:+.3f})" for d in dados
        )
        holdout = self._meta.get("ano_holdout", "holdout")
        texto = (
            f"{prefixo}Variáveis com maior importância preditiva global (aumento médio do MAE "
            f"ao embaralhar cada uma no holdout de {holdout}): {lista}. Medida global, "
            "preditiva e exploratória: não indica causa nem explica uma previsão individual."
        )
        return self._resposta(
            "ok",
            texto,
            dados,
            FONTE_IMPORTANCIA,
            f"holdout {holdout}",
            ["Importância não é causalidade; variáveis correlacionadas dividem a importância."],
        )

    def _explicacao(self, ano, equipe, tokens) -> dict:
        return self._importancia(
            ano,
            equipe,
            tokens,
            "Não há explicação causal nem individual disponível para previsões. ",
        )

    def _consistencia(self, ano: int, equipe: str | None, _tokens_) -> dict:
        h = self._hist[self._hist["temporada"] == ano]
        linhas = [
            {"equipe": nome, "jogos": len(g), "desvio_pontos": _arred(g.std(ddof=0))}
            for nome, g in h.groupby("equipe")["pontos"]
            if len(g) >= MIN_JOGOS_CONSISTENCIA
        ]
        linhas.sort(key=lambda r: r["desvio_pontos"])
        if equipe:
            linhas = [r for r in linhas if r["equipe"] == equipe]
        periodo = self._periodo(ano, h["data_referencia"])
        if not linhas:
            return self._resposta(
                "sem_dados",
                f"Não há jogos suficientes de {equipe or 'nenhuma equipe'} em {ano} para medir "
                "consistência.",
                fonte=FONTE_HISTORICO,
                periodo=periodo,
            )
        if equipe:
            r = linhas[0]
            texto = (
                f"{equipe} em {ano}: desvio-padrão dos pontos por jogo de "
                f"{r['desvio_pontos']:.3f} em {r['jogos']} jogos (ddof=0)."
            )
        else:
            r = linhas[0]
            texto = (
                f"Ranking exploratório de consistência em {ano} (menor desvio-padrão dos pontos "
                f"por jogo, ddof=0): 1º {r['equipe']} ({r['desvio_pontos']:.3f}, "
                f"{r['jogos']} jogos)."
            )
        return self._resposta(
            "ok",
            texto,
            linhas,
            FONTE_HISTORICO,
            periodo,
            [
                "Ranking exploratório, não oficial; diferenças pequenas não são "
                "evidência estatística."
            ],
        )

    def _evolucao(self, ano: int, equipe: str | None, tokens: list[str]) -> dict:
        h = self._hist[self._hist["temporada"] == ano]
        linhas, insuficientes = [], []
        for nome, g in h.groupby("equipe"):
            if equipe and nome != equipe:
                continue
            medias = g["media_pontos_5"]
            if (
                len(g) < MIN_JOGOS_EVOLUCAO
                or pd.isna(medias.iloc[-1])
                or pd.isna(medias.iloc[-1 - JANELA_EVOLUCAO])
            ):
                insuficientes.append(nome)
                continue
            atual, anterior = medias.iloc[-1], medias.iloc[-1 - JANELA_EVOLUCAO]
            linhas.append(
                {
                    "equipe": nome,
                    "media_atual": _arred(atual),
                    "media_anterior": _arred(anterior),
                    "variacao": _arred(atual - anterior),
                    "jogos": len(g),
                }
            )
        periodo = self._periodo(ano, h["data_referencia"])
        limitacoes = [
            "Compara janelas de 10 partidas definidas pelo projeto; "
            "não é ranking oficial de rodadas.",
            "Descreve variação recente, não explica causas.",
        ]
        if not linhas:
            if insuficientes:
                return self._resposta(
                    "insuficiente",
                    f"Dados insuficientes em {ano}: são necessárias {MIN_JOGOS_EVOLUCAO} partidas "
                    "concluídas por equipe para comparar com as 10 anteriores "
                    f"({', '.join(sorted(insuficientes))}).",
                    fonte=FONTE_HISTORICO,
                    periodo=periodo,
                )
            return self._resposta(
                "sem_dados",
                f"Não há dados de {equipe} em {ano}." if equipe else f"Não há dados em {ano}.",
                fonte=FONTE_HISTORICO,
                periodo=periodo,
            )
        queda = any(t.startswith(QUEDA) for t in tokens)
        linhas.sort(key=lambda r: r["variacao"], reverse=not queda)
        if queda:
            linhas = [r for r in linhas if r["variacao"] < 0]
            if linhas:
                lista = "; ".join(f"{r['equipe']} ({r['variacao']:+.3f})" for r in linhas)
                texto = f"Equipes com queda em {ano} (média de 5 partidas): {lista}."
            else:
                texto = f"Nenhuma equipe apresentou queda em {ano} nessa comparação."
        else:
            top = linhas[0]
            texto = (
                f"Maior evolução em {ano}: {top['equipe']} ({top['variacao']:+.3f} pontos na "
                "média de 5 partidas, em relação às 10 partidas anteriores)."
            )
        return self._resposta("ok", texto, linhas, FONTE_HISTORICO, periodo, limitacoes)
