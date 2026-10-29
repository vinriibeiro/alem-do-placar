"""Catálogo fechado de consultas analíticas sobre o histórico (T009 v2; PRD 9.3 e 9.4).

Cada consulta é uma função pura sobre o dataset analítico (duas linhas por partida, uma por
equipe). Não há SQL nem código derivado da pergunta: o roteador, determinístico ou o LLM,
apenas escolhe uma consulta e seus parâmetros, que são validados aqui.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import pandas as pd

from processing.padronizacao import normalizar_texto

FONTE = "Dataset analítico (OpenFootball CC0, histórico 2018–2025)"
COLUNAS = (
    "partida_id",
    "equipe",
    "adversario",
    "data_referencia",
    "temporada",
    "mando",
    "pontos",
    "gols_pro",
    "gols_contra",
)
LIM_BASE = [
    "Histórico de partidas concluídas, não previsão.",
    "Temporadas 2018–2025 do Brasileirão Série A; 2026 não consta nos dados.",
]
LIM_DESEMPATE = (
    "Classificação ordenada por pontos, vitórias, saldo e gols pró; critérios oficiais de "
    "desempate (confronto direto, cartões) não foram aplicados."
)
METRICAS = {
    "pontos": ("Pontos", False),
    "aproveitamento": ("Aproveitamento (%)", False),
    "ataque": ("Gols marcados por jogo", False),
    "defesa": ("Gols sofridos por jogo", True),
    "saldo": ("Saldo de gols", False),
    "consistencia": ("Desvio-padrão dos pontos por jogo", True),
    "vitorias": ("Vitórias", False),
}
TIPOS_SEQUENCIA = {
    "invicta": ("sem derrota", lambda p: p >= 1),
    "vitorias": ("de vitórias", lambda p: p == 3),
    "derrotas": ("de derrotas", lambda p: p == 0),
    "sem_vencer": ("sem vencer", lambda p: p <= 1),
}


class ConsultaErro(ValueError):
    """Parâmetro inválido ou dado indisponível; a mensagem é segura para o usuário."""


@dataclass
class Resultado:
    texto_base: str
    dados: list[dict]
    periodo: str
    limitacoes: list[str]
    fonte: str = FONTE
    status: str = "ok"

    def como_dict(self) -> dict:
        return {
            "status": self.status,
            "texto_base": self.texto_base,
            "dados": self.dados,
            "fonte": self.fonte,
            "periodo": self.periodo,
            "limitacoes": self.limitacoes,
        }


def catalogo_disponivel(df: pd.DataFrame | None) -> bool:
    return df is not None and all(c in df.columns for c in COLUNAS)


def _chave(nome: str) -> str:
    return " ".join(re.findall(r"\w+", normalizar_texto(str(nome)).lower()))


def _num(valor, casas: int = 2):
    return None if pd.isna(valor) else round(float(valor), casas)


def _tabela(df: pd.DataFrame) -> pd.DataFrame:
    """Classificação por equipe a partir de linhas equipe-partida."""
    g = df.groupby("equipe")
    t = pd.DataFrame(
        {
            "jogos": g.size(),
            "pontos": g["pontos"].sum(),
            "vitorias": g["pontos"].apply(lambda s: int((s == 3).sum())),
            "empates": g["pontos"].apply(lambda s: int((s == 1).sum())),
            "derrotas": g["pontos"].apply(lambda s: int((s == 0).sum())),
            "gols_pro": g["gols_pro"].sum(),
            "gols_contra": g["gols_contra"].sum(),
        }
    )
    t["saldo"] = t["gols_pro"] - t["gols_contra"]
    t["aproveitamento"] = (100 * t["pontos"] / (3 * t["jogos"])).round(1)
    t = t.sort_values(["pontos", "vitorias", "saldo", "gols_pro"], ascending=False)
    t.insert(0, "posicao", range(1, len(t) + 1))
    return t.reset_index()


def _linhas(t: pd.DataFrame) -> list[dict]:
    return json.loads(t.to_json(orient="records", force_ascii=False))


class Catalogo:
    def __init__(self, hist: pd.DataFrame) -> None:
        if not catalogo_disponivel(hist):
            raise ValueError("colunas do catálogo ausentes")
        self.h = hist.copy()
        self.anos = sorted(int(a) for a in self.h["temporada"].unique())
        self.equipes = sorted(str(e) for e in self.h["equipe"].unique())
        self._chaves = {_chave(e): e for e in self.equipes}

    # ---------- resolução de parâmetros ----------
    def equipe(self, nome: str | None) -> str:
        if not nome or not str(nome).strip():
            raise ConsultaErro("Informe o nome da equipe.")
        k = _chave(nome)
        if k in self._chaves:
            return self._chaves[k]
        achadas = [
            e
            for kk, e in self._chaves.items()
            if k and re.search(rf"(?<!\w){re.escape(k)}(?!\w)", kk)
        ]
        if not achadas:
            achadas = [
                e
                for kk, e in self._chaves.items()
                if k and kk.replace(" ", "").endswith(k.replace(" ", ""))
            ]
        if len(achadas) == 1:
            return achadas[0]
        if achadas:
            raise ConsultaErro(
                "Mais de uma equipe corresponde a esse nome: " + ", ".join(achadas) + "."
            )
        raise ConsultaErro(f"Equipe não encontrada nos dados: {nome}.")

    def ano(self, ano: int | None, obrigatorio: bool = False) -> int | None:
        if ano is None:
            if obrigatorio:
                return self.anos[-1]
            return None
        try:
            ano = int(ano)
        except (TypeError, ValueError):
            raise ConsultaErro("Ano inválido.") from None
        if ano not in self.anos:
            raise ConsultaErro(
                f"O ano {ano} não consta nos dados ({self.anos[0]} a {self.anos[-1]})."
            )
        return ano

    def _recorte(self, ano: int | None, equipe: str | None = None) -> pd.DataFrame:
        d = self.h
        if ano is not None:
            d = d[d["temporada"] == ano]
        if equipe is not None:
            d = d[d["equipe"] == equipe]
        return d.sort_values("data_referencia")

    def _periodo(self, d: pd.DataFrame, ano: int | None) -> str:
        if d.empty:
            return str(ano) if ano else "sem dados"
        ini, fim = d["data_referencia"].min(), d["data_referencia"].max()
        rot = str(ano) if ano else f"{self.anos[0]}–{self.anos[-1]}"
        return f"{rot}: de {ini:%d/%m/%Y} a {fim:%d/%m/%Y}"

    # ---------- consultas ----------
    def classificacao(self, ano: int | None = None, top: int | None = None) -> dict:
        ano = self.ano(ano, True)
        d = self._recorte(ano)
        t = _tabela(d)
        completa = len(t)
        if top:
            t = t.head(max(1, min(int(top), 30)))
        lider = t.iloc[0]
        jogos_min = int(d.groupby("equipe").size().min())
        texto = (
            f"Classificação calculada de {ano}: {lider['equipe']} lidera com {int(lider['pontos'])} "
            f"pontos em {int(lider['jogos'])} jogos."
        )
        lim = [LIM_DESEMPATE, *LIM_BASE]
        if jogos_min < 38:
            lim.append("Temporada com menos de 38 jogos por equipe nos dados.")
        return Resultado(texto, _linhas(t), self._periodo(d, ano), lim).como_dict() | {
            "total_equipes": completa
        }

    def resumo_equipe(self, equipe: str, ano: int | None = None) -> dict:
        eq = self.equipe(equipe)
        ano = self.ano(ano)
        d = self._recorte(ano, eq)
        if d.empty:
            raise ConsultaErro(f"Não há jogos de {eq} em {ano}.")
        if ano is None:
            linhas = []
            for a in self.anos:
                da = self._recorte(a, eq)
                if da.empty:
                    continue
                t = _tabela(self._recorte(a))
                linhas.append({"temporada": a, **_linhas(t[t["equipe"] == eq])[0]})
            tot = _tabela(d).iloc[0]
            texto = (
                f"{eq} no histórico: {int(tot['jogos'])} jogos, {int(tot['vitorias'])} vitórias, "
                f"{int(tot['empates'])} empates, {int(tot['derrotas'])} derrotas, "
                f"{int(tot['pontos'])} pontos ({tot['aproveitamento']:.1f}% de aproveitamento)."
            )
            return Resultado(texto, linhas, self._periodo(d, None), LIM_BASE).como_dict()
        t = _tabela(self._recorte(ano))
        r = t[t["equipe"] == eq].iloc[0]
        texto = (
            f"{eq} em {ano}: {int(r['posicao'])}º lugar na classificação calculada, "
            f"{int(r['pontos'])} pontos, {int(r['vitorias'])}V {int(r['empates'])}E {int(r['derrotas'])}D, "
            f"saldo {int(r['saldo']):+d}, aproveitamento {r['aproveitamento']:.1f}%."
        )
        return Resultado(
            texto, _linhas(t[t["equipe"] == eq]), self._periodo(d, ano), [LIM_DESEMPATE, *LIM_BASE]
        ).como_dict()

    def comparar_equipes(self, equipe_a: str, equipe_b: str, ano: int | None = None) -> dict:
        a, b = self.equipe(equipe_a), self.equipe(equipe_b)
        if a == b:
            raise ConsultaErro("Informe duas equipes diferentes.")
        ano = self.ano(ano)
        d = self._recorte(ano)
        t = _tabela(d)
        sel = t[t["equipe"].isin([a, b])]
        if len(sel) < 2:
            raise ConsultaErro("Uma das equipes não tem jogos no período.")
        ra = sel[sel["equipe"] == a].iloc[0]
        rb = sel[sel["equipe"] == b].iloc[0]
        ref = f"em {ano}" if ano else "no histórico 2018–2025"
        texto = (
            f"{ref.capitalize()}: {a} fez {int(ra['pontos'])} pontos ({ra['aproveitamento']:.1f}%) "
            f"e {b} fez {int(rb['pontos'])} ({rb['aproveitamento']:.1f}%). "
            "Os totais acumulados dependem do número de jogos de cada equipe."
        )
        return Resultado(texto, _linhas(sel), self._periodo(d, ano), LIM_BASE).como_dict()

    def confronto_direto(self, equipe_a: str, equipe_b: str, ano: int | None = None) -> dict:
        a, b = self.equipe(equipe_a), self.equipe(equipe_b)
        if a == b:
            raise ConsultaErro("Informe duas equipes diferentes.")
        ano = self.ano(ano)
        d = self._recorte(ano, a)
        d = d[d["adversario"] == b]
        if d.empty:
            raise ConsultaErro(f"Não há confrontos entre {a} e {b} nos dados.")
        vit, emp, der = (
            int((d.pontos == 3).sum()),
            int((d.pontos == 1).sum()),
            int((d.pontos == 0).sum()),
        )
        jogos = [
            {
                "data": f"{r.data_referencia:%d/%m/%Y}",
                "mandante": a if r.mando == 1 else b,
                "placar": f"{r.gols_pro}x{r.gols_contra}"
                if r.mando == 1
                else f"{r.gols_contra}x{r.gols_pro}",
            }
            for r in d.itertuples()
        ]
        texto = (
            f"Confrontos entre {a} e {b}: {len(d)} jogos; {a} venceu {vit}, empatou {emp} e perdeu {der}. "
            f"Gols: {a} {int(d.gols_pro.sum())} x {int(d.gols_contra.sum())} {b}."
        )
        return Resultado(texto, jogos, self._periodo(d, ano), LIM_BASE).como_dict()

    def mando(self, equipe: str | None = None, ano: int | None = None) -> dict:
        eq = self.equipe(equipe) if equipe else None
        ano = self.ano(ano)
        d = self._recorte(ano, eq)
        if d.empty:
            raise ConsultaErro("Não há jogos para o filtro informado.")
        linhas = []
        for rot, m in (("mandante", 1), ("visitante", 0)):
            x = d[d["mando"] == m]
            n = len(x)
            linhas.append(
                {
                    "mando": rot,
                    "jogos": n,
                    "pontos_por_jogo": _num(x.pontos.mean()),
                    "vitorias_pct": _num(100 * (x.pontos == 3).mean(), 1),
                    "gols_pro_por_jogo": _num(x.gols_pro.mean()),
                    "gols_contra_por_jogo": _num(x.gols_contra.mean()),
                }
            )
        esc = eq or "todas as equipes"
        texto = (
            f"Desempenho de {esc}{f' em {ano}' if ano else ''}: como mandante {linhas[0]['pontos_por_jogo']} "
            f"pontos por jogo, como visitante {linhas[1]['pontos_por_jogo']}."
        )
        return Resultado(texto, linhas, self._periodo(d, ano), LIM_BASE).como_dict()

    def gols(self, ano: int | None = None) -> dict:
        ano = self.ano(ano)
        d = self._recorte(ano)
        casa = d[d["mando"] == 1]
        if casa.empty:
            raise ConsultaErro("Não há partidas para o filtro informado.")
        casa = casa.assign(total=casa.gols_pro + casa.gols_contra)
        por_ano = (
            casa.groupby("temporada")
            .agg(
                partidas=("total", "size"),
                gols_por_jogo=("total", "mean"),
                vitorias_mandante_pct=("pontos", lambda s: 100 * (s == 3).mean()),
                empates_pct=("pontos", lambda s: 100 * (s == 1).mean()),
            )
            .round(2)
            .reset_index()
        )
        dados = por_ano.to_dict("records")
        gm = casa.assign(margem=(casa.gols_pro - casa.gols_contra).abs()).nlargest(
            3, ["margem", "total"]
        )
        goleadas = [
            f"{r.equipe} {r.gols_pro}x{r.gols_contra} {r.adversario} ({r.data_referencia:%d/%m/%Y})"
            for r in gm.itertuples()
        ]
        texto = (
            f"Média de {casa.total.mean():.2f} gols por partida"
            f"{f' em {ano}' if ano else ' no histórico'}; mandante vence {100 * (casa.pontos == 3).mean():.1f}% "
            f"dos jogos. Maiores goleadas: {'; '.join(goleadas)}."
        )
        return Resultado(texto, dados, self._periodo(d, ano), LIM_BASE).como_dict()

    def sequencias(
        self, tipo: str = "invicta", equipe: str | None = None, ano: int | None = None
    ) -> dict:
        if tipo not in TIPOS_SEQUENCIA:
            raise ConsultaErro("Tipo de sequência inválido: " + ", ".join(TIPOS_SEQUENCIA) + ".")
        rot, regra = TIPOS_SEQUENCIA[tipo]
        eq = self.equipe(equipe) if equipe else None
        ano = self.ano(ano)
        d = self._recorte(ano, eq)
        if d.empty:
            raise ConsultaErro("Não há jogos para o filtro informado.")
        linhas = []
        for nome, g in d.groupby("equipe"):
            melhor = atual = 0
            fim_melhor = None
            ini_atual = None
            ini_melhor = None
            for r in g.sort_values("data_referencia").itertuples():
                if regra(r.pontos):
                    atual += 1
                    ini_atual = ini_atual if atual > 1 else r.data_referencia
                    if atual > melhor:
                        melhor, fim_melhor, ini_melhor = atual, r.data_referencia, ini_atual
                else:
                    atual = 0
            linhas.append(
                {
                    "equipe": nome,
                    "maior_sequencia": melhor,
                    "inicio": f"{ini_melhor:%d/%m/%Y}" if ini_melhor is not None else None,
                    "fim": f"{fim_melhor:%d/%m/%Y}" if fim_melhor is not None else None,
                }
            )
        linhas.sort(key=lambda x: -x["maior_sequencia"])
        linhas = linhas[:1] if eq else linhas[:5]
        topo = linhas[0]
        texto = (
            f"Maior sequência {rot}{f' em {ano}' if ano else ' no histórico'}: {topo['equipe']} com "
            f"{topo['maior_sequencia']} jogos."
        )
        lim = [
            *LIM_BASE,
            "Sequências não atravessam temporadas quando o filtro é um ano; no histórico "
            "completo seguem a ordem cronológica das partidas.",
        ]
        return Resultado(texto, linhas, self._periodo(d, ano), lim).como_dict()

    def ranking(self, metrica: str = "pontos", ano: int | None = None, top: int = 5) -> dict:
        if metrica not in METRICAS:
            raise ConsultaErro("Métrica inválida: " + ", ".join(METRICAS) + ".")
        rot, menor_melhor = METRICAS[metrica]
        ano = self.ano(ano, True)
        d = self._recorte(ano)
        t = _tabela(d).set_index("equipe")
        g = d.groupby("equipe")
        t["ataque"] = g["gols_pro"].mean().round(2)
        t["defesa"] = g["gols_contra"].mean().round(2)
        t["consistencia"] = g["pontos"].std(ddof=0).round(3)
        serie = t[metrica].sort_values(ascending=menor_melhor)
        top = max(1, min(int(top), 20))
        linhas = [
            {
                "posicao": i + 1,
                "equipe": e,
                "metrica": rot,
                "valor": _num(v, 3 if metrica == "consistencia" else 2),
            }
            for i, (e, v) in enumerate(serie.head(top).items())
        ]
        texto = f"Ranking de {ano} por {rot.lower()}: {linhas[0]['equipe']} em primeiro."
        lim = list(LIM_BASE)
        if metrica == "consistencia":
            lim.append(
                "Menor desvio-padrão dos pontos por jogo indica resultados mais regulares, não melhor desempenho."
            )
        return Resultado(texto, linhas, self._periodo(d, ano), lim).como_dict()


# ---------- metadados das consultas (usados pelo LLM e pela documentação) ----------
def _eq(desc: str = "Nome da equipe") -> dict:
    return {"type": "string", "description": desc}


ANO = {
    "type": ["integer", "null"],
    "description": "Temporada (2018–2025); null para todo o histórico",
}
DEFINICOES = {
    "classificacao": (
        "Classificação calculada de uma temporada (pontos, V/E/D, gols, aproveitamento).",
        {
            "ano": ANO,
            "top": {"type": ["integer", "null"], "description": "Quantas equipes devolver"},
        },
    ),
    "resumo_equipe": (
        "Resumo de uma equipe em uma temporada ou em todo o histórico.",
        {"equipe": _eq(), "ano": ANO},
    ),
    "comparar_equipes": (
        "Compara duas equipes lado a lado.",
        {"equipe_a": _eq(), "equipe_b": _eq(), "ano": ANO},
    ),
    "confronto_direto": (
        "Histórico de jogos entre duas equipes.",
        {"equipe_a": _eq(), "equipe_b": _eq(), "ano": ANO},
    ),
    "mando": (
        "Desempenho como mandante versus visitante, geral ou de uma equipe.",
        {
            "equipe": {"type": ["string", "null"], "description": "Equipe ou null para todas"},
            "ano": ANO,
        },
    ),
    "gols": (
        "Estatísticas de gols por temporada, vitórias do mandante e maiores goleadas.",
        {"ano": ANO},
    ),
    "sequencias": (
        "Maiores sequências (invicta, vitorias, derrotas, sem_vencer).",
        {
            "tipo": {"type": "string", "enum": list(TIPOS_SEQUENCIA)},
            "equipe": {"type": ["string", "null"]},
            "ano": ANO,
        },
    ),
    "ranking": (
        "Ranking por métrica: pontos, aproveitamento, ataque, defesa, saldo, consistencia, vitorias.",
        {
            "metrica": {"type": "string", "enum": list(METRICAS)},
            "ano": ANO,
            "top": {"type": ["integer", "null"]},
        },
    ),
}
