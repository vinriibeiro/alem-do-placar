"""Layout PBIR do relatório Além do Placar (F3): tema, cabeçalho, navegação e as sete páginas.

Canvas 1280x720. Cabeçalho em 0–64, navegação em 68–104, conteúdo em 112–692 e rodapé em
698–718, com margem lateral de 16 px e espaçamento de 12 px. Todas as cores vêm de tokens
compartilhados com o site (``dashboard/assets/tema_tokens.json``).
"""

from __future__ import annotations

import hashlib
from typing import Any

FATO = "fato_desempenho_equipes"
SCHEMA_PAGINA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"

LARGURA, ALTURA = 1280, 720
MARGEM, ESPACO = 16, 12
TOPO_CONTEUDO, FIM_CONTEUDO = 112, 692
LARGURA_UTIL = LARGURA - 2 * MARGEM  # 1248

TOKENS_PADRAO = {
    "cor-primaria": "#0b2545",
    "cor-primaria-100": "#e6edf6",
    "cor-destaque": "#0f8f68",
    "cor-destaque-700": "#0b6f50",
    "cor-fundo": "#f6f8fa",
    "cor-superficie": "#ffffff",
    "cor-borda": "#e1e7ee",
    "cor-borda-forte": "#c5cfda",
    "cor-texto": "#14212e",
    "cor-texto-suave": "#4f5f70",
    "cor-sucesso": "#1a7f4b",
    "cor-alerta": "#9a6700",
    "cor-erro": "#b42318",
    "serie-1": "#0b2545",
    "serie-2": "#0f8f68",
    "serie-3": "#e0a526",
    "serie-4": "#5b8def",
    "serie-5": "#c2410c",
    "serie-6": "#7a8ca3",
}
FONTE = "Segoe UI"
FONTE_TITULO = "Segoe UI Semibold"


def _cor(tokens: dict[str, str], nome: str) -> str:
    return tokens.get(nome) or TOKENS_PADRAO[nome]


def construir_tema(tokens: dict[str, str]) -> dict[str, Any]:
    """Tema JSON do Power BI a partir dos tokens de design."""
    c = lambda n: _cor(tokens, n)  # noqa: E731
    serie = [c(f"serie-{i}") for i in range(1, 7)]
    solido = lambda hexa: {"solid": {"color": hexa}}  # noqa: E731
    return {
        "name": "AlemDoPlacar",
        "dataColors": serie + ["#9fe3cb", "#f4c978", "#a9c1f5", "#e8a27c"],
        "background": c("cor-superficie"),
        "foreground": c("cor-texto"),
        "tableAccent": c("cor-destaque"),
        "good": c("cor-sucesso"),
        "neutral": serie[2],
        "bad": c("cor-erro"),
        "maximum": c("cor-destaque"),
        "center": serie[2],
        "minimum": c("cor-erro"),
        "null": c("cor-borda-forte"),
        "textClasses": {
            "callout": {"fontSize": 28, "fontFace": FONTE_TITULO, "color": c("cor-primaria")},
            "title": {"fontSize": 13, "fontFace": FONTE_TITULO, "color": c("cor-primaria")},
            "header": {"fontSize": 12, "fontFace": FONTE_TITULO, "color": c("cor-primaria")},
            "label": {"fontSize": 11, "fontFace": FONTE, "color": c("cor-texto-suave")},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "title": [
                        {
                            "show": True,
                            "fontColor": solido(c("cor-primaria")),
                            "fontSize": 13,
                            "fontFamily": FONTE_TITULO,
                        }
                    ],
                    "background": [
                        {"show": True, "color": solido(c("cor-superficie")), "transparency": 0}
                    ],
                    "border": [{"show": True, "color": solido(c("cor-borda")), "radius": 8}],
                }
            },
            "page": {
                "*": {
                    "background": [{"color": solido(c("cor-fundo")), "transparency": 0}],
                }
            },
        },
    }


# --- Primitivas PBIR -------------------------------------------------------------------------


def _id(*partes: str) -> str:
    """Identificador hexadecimal de 20 caracteres, estável entre execuções."""
    return hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()[:20]


def _lit(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def _solido(hexa: str) -> dict:
    return {"solid": {"color": _lit(f"'{hexa}'")}}


def c_(tabela: str, campo: str) -> tuple[str, str, str]:
    return (tabela, campo, "Column")


def m_(nome: str) -> tuple[str, str, str]:
    return (FATO, nome, "Measure")


ROTULOS = {
    "nome_padronizado": "Equipe",
    "equipe": "Equipe",
    "escudo": "Escudo",
    "ano": "Temporada",
    "temporada": "Temporada",
    "data_referencia": "Data",
    "previsao": "Previsão",
    "limite_inferior": "Limite inferior",
    "limite_superior": "Limite superior",
    "fase": "Fase",
    "modelo": "Modelo",
    "mae": "MAE",
    "rmse": "RMSE",
    "vies": "Viés",
    "atributo": "Variável",
    "mando_campo": "Mando",
    "pontos": "Pontos no jogo",
}


def _campo(ref: tuple[str, str, str]) -> dict:
    tabela, campo, tipo = ref
    return {tipo: {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": campo}}


def _projecao(ref: tuple[str, str, str]) -> dict:
    tabela, campo, _ = ref
    proj = {"field": _campo(ref), "queryRef": f"{tabela}.{campo}", "nativeQueryRef": campo}
    if campo in ROTULOS:
        proj["displayName"] = ROTULOS[campo]
    return proj


def _envelope(pos: tuple[int, int, int, int], visual: dict) -> dict:
    x, y, largura, altura = pos
    return {"position": {"x": x, "y": y, "width": largura, "height": altura}, "visual": visual}


class Estilo:
    """Cores e fontes resolvidas dos tokens."""

    def __init__(self, tokens: dict[str, str]) -> None:
        self.t = tokens
        self.primaria = _cor(tokens, "cor-primaria")
        self.destaque = _cor(tokens, "cor-destaque")
        self.destaque_escuro = _cor(tokens, "cor-destaque-700")
        self.superficie = _cor(tokens, "cor-superficie")
        self.borda = _cor(tokens, "cor-borda")
        self.texto = _cor(tokens, "cor-texto")
        self.suave = _cor(tokens, "cor-texto-suave")
        self.alerta = _cor(tokens, "cor-alerta")
        self.claro = _cor(tokens, "cor-primaria-100")


def _fundo(est: Estilo, cor: str | None, borda: bool) -> dict:
    objetos: dict[str, Any] = {
        "background": [
            {
                "properties": {
                    "show": _lit("true"),
                    "color": _solido(cor or est.superficie),
                    "transparency": _lit("0D"),
                }
            }
        ]
    }
    if borda:
        objetos["border"] = [
            {
                "properties": {
                    "show": _lit("true"),
                    "color": _solido(est.borda),
                    "radius": _lit("8D"),
                }
            }
        ]
    return objetos


def caixa_texto(
    est: Estilo,
    pos: tuple[int, int, int, int],
    paragrafos: list[dict],
    fundo: str | None = None,
    borda: bool = False,
    respiro: tuple[int, int, int, int] = (8, 8, 12, 12),
) -> dict:
    """``paragrafos``: dicts com ``texto``, ``tamanho``, ``cor``, ``negrito``, ``url``, ``alinhar``.

    ``respiro`` é o espaçamento interno (cima, baixo, esquerda, direita) em px.
    """
    blocos = []
    for p in paragrafos:
        estilo = {
            "fontFamily": FONTE,
            "fontSize": f"{p.get('tamanho', 12)}px",
            "color": p.get("cor", est.texto),
        }
        if p.get("negrito"):
            estilo["fontWeight"] = "bold"
        if p.get("url"):
            estilo["textDecoration"] = "underline"
        execucao: dict[str, Any] = {"value": p["texto"], "textStyle": estilo}
        if p.get("url"):
            execucao["url"] = p["url"]
        bloco: dict[str, Any] = {"textRuns": [execucao]}
        if p.get("alinhar"):
            bloco["horizontalTextAlignment"] = p["alinhar"]
        blocos.append(bloco)
    contexto = (
        _fundo(est, fundo, borda)
        if (fundo or borda)
        else {"background": [{"properties": {"show": _lit("false")}}]}
    )
    cima, baixo, esq, dir_ = respiro
    contexto["padding"] = [
        {
            "properties": {
                "top": _lit(f"{cima}D"),
                "bottom": _lit(f"{baixo}D"),
                "left": _lit(f"{esq}D"),
                "right": _lit(f"{dir_}D"),
            }
        }
    ]
    contexto["visualHeader"] = [{"properties": {"show": _lit("false")}}]
    visual: dict[str, Any] = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": blocos}}]},
        "visualContainerObjects": contexto,
    }
    return _envelope(pos, visual)


def visual(
    est: Estilo,
    tipo: str,
    pos: tuple[int, int, int, int],
    papeis: dict[str, list],
    titulo: str,
    objetos: dict | None = None,
    tamanho_titulo: int = 13,
    respiro: int = 8,
    ordenar: tuple[str, str, str] | None = None,
) -> dict:
    estado = {p: {"projections": [_projecao(r) for r in refs]} for p, refs in papeis.items()}
    consulta: dict[str, Any] = {"queryState": estado}
    if ordenar:
        consulta["sortDefinition"] = {
            "sort": [{"field": _campo(ordenar), "direction": "Descending"}],
            "isDefaultSort": True,
        }
    v: dict[str, Any] = {"visualType": tipo, "query": consulta}
    if objetos:
        v["objects"] = objetos
    contexto_visual = _fundo(est, None, True)
    contexto_visual["title"] = [
        {
            "properties": {
                "show": _lit("true"),
                "text": _lit(f"'{titulo}'"),
                "fontSize": _lit(f"{tamanho_titulo}D"),
                "fontColor": _solido(est.primaria),
            }
        }
    ]
    contexto_visual["padding"] = [
        {"properties": {lado: _lit(f"{respiro}D") for lado in ("top", "bottom", "left", "right")}}
    ]
    v["visualContainerObjects"] = contexto_visual
    return _envelope(pos, v)


def cartao(est: Estilo, pos, medida: tuple[str, str, str], titulo: str) -> dict:
    """Título no contêiner e só o valor no corpo (o rótulo da categoria repetiria o nome)."""
    objetos = {
        "labels": [{"properties": {"fontSize": _lit("22D"), "color": _solido(est.primaria)}}],
        "categoryLabels": [{"properties": {"show": _lit("false")}}],
    }
    return visual(est, "card", pos, {"Values": [medida]}, titulo, objetos, 11, 6)


def seletor(est: Estilo, pos, coluna: tuple[str, str, str], titulo: str) -> dict:
    objetos = {
        "data": [{"properties": {"mode": _lit("'Dropdown'")}}],
        "header": [{"properties": {"show": _lit("false")}}],
    }
    return visual(est, "slicer", pos, {"Values": [coluna]}, titulo, objetos, 11, 6)


def tabela(est: Estilo, pos, colunas: list, titulo: str, ordenar=None) -> dict:
    objetos = {"grid": [{"properties": {"imageHeight": _lit("22D")}}]}
    return visual(est, "tableEx", pos, {"Values": colunas}, titulo, objetos, ordenar=ordenar)


def navegador(est: Estilo, pos) -> dict:
    return _envelope(
        pos,
        {
            "visualType": "pageNavigator",
            "visualContainerObjects": {
                "background": [{"properties": {"show": _lit("false")}}],
                "visualHeader": [{"properties": {"show": _lit("false")}}],
            },
        },
    )


def cabecalho_e_rodape(est: Estilo, titulo: str, subtitulo: str, rodape: str) -> tuple[list, list]:
    topo = [
        caixa_texto(
            est,
            (0, 0, 900, 64),
            [
                {"texto": titulo, "tamanho": 26, "cor": "#FFFFFF", "negrito": True},
                {"texto": subtitulo, "tamanho": 13, "cor": "#9FE3CB"},
            ],
            fundo=est.primaria,
            respiro=(6, 4, 24, 12),
        ),
        caixa_texto(
            est,
            (900, 0, LARGURA - 900, 64),
            [
                {
                    "texto": "ALÉM DO PLACAR",
                    "tamanho": 16,
                    "cor": "#FFFFFF",
                    "negrito": True,
                    "alinhar": "right",
                },
                {
                    "texto": "Inteligência esportiva · Brasileirão",
                    "tamanho": 12,
                    "cor": "#9FE3CB",
                    "alinhar": "right",
                },
            ],
            fundo=est.primaria,
            respiro=(10, 4, 12, 24),
        ),
        navegador(est, (MARGEM, 68, LARGURA_UTIL, 36)),
    ]
    base = [
        caixa_texto(
            est,
            (MARGEM, 698, LARGURA_UTIL, 20),
            [{"texto": rodape, "tamanho": 10, "cor": est.suave}],
        )
    ]
    return topo, base


def pagina(nome: str, visuais: list[dict]) -> dict:
    ident = _id(nome)
    containers = [
        {
            "$schema": SCHEMA_VISUAL,
            "name": _id(ident, str(i)),
            "position": {**v["position"], "z": i, "tabOrder": i},
            "visual": v["visual"],
        }
        for i, v in enumerate(visuais)
    ]
    corpo = {
        "$schema": SCHEMA_PAGINA,
        "name": ident,
        "displayName": nome,
        "displayOption": "FitToPage",
        "height": ALTURA,
        "width": LARGURA,
    }
    return {"id": ident, "pagina": corpo, "visuais": containers}


# --- Páginas ---------------------------------------------------------------------------------


def _linha(x: int, larguras: list[int]) -> list[int]:
    """Posições x consecutivas com espaçamento fixo."""
    xs = []
    for w in larguras:
        xs.append(x)
        x += w + ESPACO
    return xs


def construir_paginas(
    meta: dict[str, Any], tokens: dict[str, str], url_assistente: str, com_escudos: bool = False
) -> list[dict]:
    est = Estilo(tokens)
    eq = c_("dim_equipes", "nome_padronizado")
    escudo = [c_("dim_equipes", "escudo")] if com_escudos else []
    ano = c_("dim_temporadas", "ano")
    modelo = meta["modelo_selecionado"]
    rodape = (
        f"Fonte: OpenFootball (CC0), 2018–2025 · Modelo {modelo} {meta['versao']} · "
        f"Corte de treino {meta['corte_treino']} · Previsões são estimativas retrospectivas."
    )
    larg5 = (LARGURA_UTIL - 4 * ESPACO) // 5  # 240
    larg4 = (LARGURA_UTIL - 3 * ESPACO) // 4  # 303
    topo_kpi, alt_kpi = TOPO_CONTEUDO, 96

    def moldura(titulo: str, sub: str, corpo: list[dict]) -> list[dict]:
        topo, base = cabecalho_e_rodape(est, titulo, sub, rodape)
        return topo + corpo + base

    # 1. Visão Geral ------------------------------------------------------------------------
    xs = _linha(MARGEM, [larg5] * 5)
    kpis = [
        cartao(est, (xs[0], topo_kpi, larg5, alt_kpi), m_("Partidas"), "Partidas"),
        cartao(est, (xs[1], topo_kpi, larg5, alt_kpi), m_("Temporadas"), "Temporadas"),
        cartao(est, (xs[2], topo_kpi, larg5, alt_kpi), m_("Gols por jogo"), "Gols por jogo"),
        cartao(
            est,
            (xs[3], topo_kpi, larg5, alt_kpi),
            m_("Vitórias do mandante"),
            "Vitórias do mandante",
        ),
        cartao(
            est,
            (xs[4], topo_kpi, larg5, alt_kpi),
            m_("MAE global selecionado"),
            "MAE do modelo (holdout)",
        ),
    ]
    y2 = topo_kpi + alt_kpi + ESPACO  # 208
    geral = moldura(
        "Visão Geral",
        "Brasileirão Série A 2018–2025 · panorama de partidas, gols e desempenho",
        kpis
        + [
            seletor(est, (MARGEM, y2, 300, 72), ano, "Temporada"),
            seletor(est, (MARGEM + 312, y2, 300, 72), eq, "Equipe"),
            visual(
                est,
                "lineChart",
                (MARGEM + 624, y2, 624, 200),
                {"Category": [ano], "Y": [m_("Gols por jogo")]},
                "Gols por jogo por temporada",
            ),
            visual(
                est,
                "clusteredBarChart",
                (MARGEM, y2 + 84, 612, FIM_CONTEUDO - (y2 + 84)),
                {"Category": [eq], "Y": [m_("Pontos totais")]},
                "Pontos por equipe",
                ordenar=m_("Pontos totais"),
            ),
            tabela(
                est,
                (MARGEM + 624, y2 + 212, 624, FIM_CONTEUDO - (y2 + 212)),
                [
                    *escudo,
                    eq,
                    m_("Posição"),
                    m_("Pontos totais"),
                    m_("Vitórias"),
                    m_("Saldo de gols"),
                    m_("Aproveitamento"),
                ],
                "Classificação (filtrada pela temporada)",
                ordenar=m_("Pontos totais"),
            ),
        ],
    )

    # 2. Tendências -------------------------------------------------------------------------
    esq = 400
    tendencias = moldura(
        "Tendências",
        "Médias móveis de pontos e aproveitamento por equipe e temporada",
        [
            seletor(est, (MARGEM, TOPO_CONTEUDO, 194, 72), ano, "Temporada"),
            seletor(est, (MARGEM + 206, TOPO_CONTEUDO, 194, 72), eq, "Equipe (escolha uma)"),
            visual(
                est,
                "lineChart",
                (MARGEM, TOPO_CONTEUDO + 84, esq, 228),
                {
                    "Category": [c_("analitico", "data_referencia")],
                    "Y": [m_("Média 3 jogos"), m_("Média recente"), m_("Média 10 jogos")],
                },
                "Média móvel de pontos (3, 5 e 10 jogos)",
            ),
            visual(
                est,
                "clusteredBarChart",
                (MARGEM, TOPO_CONTEUDO + 324, esq, FIM_CONTEUDO - (TOPO_CONTEUDO + 324)),
                {"Category": [eq], "Y": [m_("Média recente")]},
                "Média recente (5 jogos) por equipe",
                ordenar=m_("Média recente"),
            ),
            visual(
                est,
                "pivotTable",
                (MARGEM + esq + ESPACO, TOPO_CONTEUDO, LARGURA_UTIL - esq - ESPACO, 580),
                {"Rows": [eq], "Columns": [ano], "Values": [m_("Aproveitamento")]},
                "Aproveitamento por equipe e temporada",
            ),
        ],
    )

    # 3. Estatística ------------------------------------------------------------------------
    meio = (LARGURA_UTIL - ESPACO) // 2  # 618
    alt_meia = (FIM_CONTEUDO - TOPO_CONTEUDO - 84 - ESPACO) // 2
    y_a = TOPO_CONTEUDO + 84
    estatistica = moldura(
        "Estatística",
        "Distribuição de resultados, mando de campo, dispersão e volatilidade",
        [
            seletor(est, (MARGEM, TOPO_CONTEUDO, 300, 72), ano, "Temporada"),
            seletor(est, (MARGEM + 312, TOPO_CONTEUDO, 300, 72), eq, "Equipe"),
            visual(
                est,
                "clusteredColumnChart",
                (MARGEM, y_a, meio, alt_meia),
                {"Category": [c_(FATO, "pontos")], "Y": [m_("Observações de equipe")]},
                "Distribuição de resultados (0, 1 e 3 pontos)",
            ),
            visual(
                est,
                "clusteredColumnChart",
                (MARGEM + meio + ESPACO, y_a, meio, alt_meia),
                {"Category": [c_(FATO, "mando_campo")], "Y": [m_("Pontos por jogo")]},
                "Pontos por jogo: mandante × visitante",
            ),
            visual(
                est,
                "scatterChart",
                (MARGEM, y_a + alt_meia + ESPACO, meio, alt_meia),
                {"Category": [eq], "X": [m_("Saldo de gols")], "Y": [m_("Pontos totais")]},
                "Saldo de gols × pontos por equipe",
            ),
            tabela(
                est,
                (MARGEM + meio + ESPACO, y_a + alt_meia + ESPACO, meio, alt_meia),
                [
                    *escudo,
                    eq,
                    m_("Pontos por jogo"),
                    m_("Volatilidade de pontos"),
                    m_("Gols por jogo"),
                    m_("Gols sofridos por jogo"),
                ],
                "Volatilidade e gols por equipe",
                ordenar=m_("Pontos por jogo"),
            ),
        ],
    )

    # 4. Laboratório de Modelos -------------------------------------------------------------
    xs = _linha(MARGEM, [larg4] * 4)
    lab_w = 600
    imp_x = MARGEM + lab_w + ESPACO
    graf_w = (lab_w - ESPACO) // 2
    y_g = topo_kpi + alt_kpi + ESPACO
    alt_g = 220
    lab = moldura(
        "Laboratório de Modelos",
        "Baseline contra modelos de Machine Learning: MAE, RMSE e importância das variáveis",
        [
            cartao(
                est,
                (xs[0], topo_kpi, larg4, alt_kpi),
                m_("MAE global selecionado"),
                "MAE do modelo (holdout)",
            ),
            cartao(
                est,
                (xs[1], topo_kpi, larg4, alt_kpi),
                m_("MAE global baseline"),
                "MAE do baseline (holdout)",
            ),
            cartao(
                est,
                (xs[2], topo_kpi, larg4, alt_kpi),
                m_("Modelo selecionado"),
                "Modelo selecionado",
            ),
            cartao(
                est, (xs[3], topo_kpi, larg4, alt_kpi), m_("Corte de treino"), "Corte de treino"
            ),
            visual(
                est,
                "clusteredColumnChart",
                (MARGEM, y_g, graf_w, alt_g),
                {
                    "Category": [c_("metricas", "modelo")],
                    "Y": [m_("MAE validação"), m_("MAE holdout")],
                },
                "MAE por modelo",
            ),
            visual(
                est,
                "clusteredColumnChart",
                (MARGEM + graf_w + ESPACO, y_g, graf_w, alt_g),
                {
                    "Category": [c_("metricas", "modelo")],
                    "Y": [m_("RMSE validação"), m_("RMSE holdout")],
                },
                "RMSE por modelo",
            ),
            visual(
                est,
                "tableEx",
                (MARGEM, y_g + alt_g + ESPACO, lab_w, FIM_CONTEUDO - (y_g + alt_g + ESPACO)),
                {
                    "Values": [
                        c_("metricas", c)
                        for c in ("fase", "modelo", "temporada", "mae", "rmse", "vies")
                    ]
                },
                "Métricas por modelo, fase e temporada",
            ),
            visual(
                est,
                "clusteredBarChart",
                (imp_x, y_g, LARGURA_UTIL - lab_w - ESPACO, FIM_CONTEUDO - y_g),
                {"Category": [c_("importancias", "atributo")], "Y": [m_("Importância")]},
                "Importância por permutação (aumento do MAE)",
                ordenar=m_("Importância"),
            ),
        ],
    )

    # 5. Previsões --------------------------------------------------------------------------
    prev_w = 800
    tab_x = MARGEM + prev_w + ESPACO
    previsoes = moldura(
        "Previsões",
        "Média de pontos prevista para as próximas 5 partidas · intervalo de 90% · holdout 2025",
        [
            seletor(est, (MARGEM, TOPO_CONTEUDO, 300, 72), eq, "Equipe (escolha uma)"),
            caixa_texto(
                est,
                (MARGEM + 312, TOPO_CONTEUDO, prev_w - 312, 72),
                [
                    {
                        "texto": "Previsões retrospectivas, não certezas.",
                        "tamanho": 12,
                        "negrito": True,
                        "cor": est.alerta,
                    },
                    {
                        "texto": "A linha prevista deve ser lida junto com o intervalo de 90% e com o erro médio do modelo.",
                        "tamanho": 11,
                        "cor": est.suave,
                    },
                ],
                fundo="#FFF6E0",
                borda=True,
            ),
            visual(
                est,
                "lineChart",
                (MARGEM, TOPO_CONTEUDO + 84, prev_w, 384),
                {
                    "Category": [c_("previsoes", "data_referencia")],
                    "Y": [
                        m_("Média prevista"),
                        m_("Média observada"),
                        m_("Limite inferior"),
                        m_("Limite superior"),
                    ],
                },
                "Previsto, observado e intervalo de 90%",
            ),
            cartao(
                est, (MARGEM, TOPO_CONTEUDO + 480, 260, 96), m_("Média prevista"), "Média prevista"
            ),
            cartao(
                est,
                (MARGEM + 272, TOPO_CONTEUDO + 480, 260, 96),
                m_("Média observada"),
                "Média observada",
            ),
            cartao(
                est,
                (MARGEM + 544, TOPO_CONTEUDO + 480, 256, 96),
                m_("Erro absoluto médio"),
                "Erro absoluto médio",
            ),
            visual(
                est,
                "tableEx",
                (
                    tab_x,
                    TOPO_CONTEUDO,
                    LARGURA_UTIL - prev_w - ESPACO,
                    FIM_CONTEUDO - TOPO_CONTEUDO,
                ),
                {
                    "Values": [
                        c_("previsoes", c)
                        for c in (
                            "equipe",
                            "data_referencia",
                            "previsao",
                            "limite_inferior",
                            "limite_superior",
                        )
                    ]
                },
                "Previsões e intervalos",
            ),
        ],
    )

    # 6. Assistente -------------------------------------------------------------------------
    exemplos = [
        "Qual foi a classificação de 2024?",
        "Compare Palmeiras e Flamengo em 2025.",
        "Qual a maior sequência invicta da história?",
        "Quem teve a melhor defesa em 2023?",
        "Qual é a previsão do Flamengo?",
        "Quais variáveis mais influenciaram o modelo?",
    ]
    assistente = moldura(
        "Assistente",
        "Pergunte em português e receba respostas com fonte, período e limitações",
        [
            caixa_texto(
                est,
                (MARGEM, TOPO_CONTEUDO, 700, 240),
                [
                    {
                        "texto": "Converse com os dados",
                        "tamanho": 22,
                        "negrito": True,
                        "cor": est.primaria,
                    },
                    {
                        "texto": "O assistente responde perguntas sobre classificação, confrontos, mando de campo, gols, sequências, rankings e previsões do Brasileirão. Cada resposta mostra a fonte, o período e as limitações.",
                        "tamanho": 14,
                    },
                    {
                        "texto": "Ele usa apenas os dados deste projeto e nunca inventa números.",
                        "tamanho": 14,
                        "cor": est.suave,
                    },
                ],
                fundo=est.superficie,
                borda=True,
            ),
            caixa_texto(
                est,
                (MARGEM + 712, TOPO_CONTEUDO, LARGURA_UTIL - 712, 240),
                [
                    {
                        "texto": "Abrir o assistente",
                        "tamanho": 20,
                        "negrito": True,
                        "cor": "#FFFFFF",
                    },
                    {
                        "texto": "Abre o site do projeto em uma nova aba.",
                        "tamanho": 12,
                        "cor": "#9FE3CB",
                    },
                    {
                        "texto": "Clique aqui para perguntar →",
                        "tamanho": 16,
                        "negrito": True,
                        "cor": "#FFFFFF",
                        "url": url_assistente,
                    },
                ],
                fundo=est.destaque_escuro,
            ),
            caixa_texto(
                est,
                (MARGEM, TOPO_CONTEUDO + 252, LARGURA_UTIL, FIM_CONTEUDO - (TOPO_CONTEUDO + 252)),
                [
                    {
                        "texto": "Exemplos de perguntas",
                        "tamanho": 16,
                        "negrito": True,
                        "cor": est.primaria,
                    }
                ]
                + [{"texto": f"•  {e}", "tamanho": 14} for e in exemplos],
                fundo=est.superficie,
                borda=True,
            ),
        ],
    )

    # 7. Metodologia ------------------------------------------------------------------------
    def bloco(titulo: str, linhas: list[str]) -> list[dict]:
        return [{"texto": titulo, "tamanho": 15, "negrito": True, "cor": est.primaria}] + [
            {"texto": f"•  {x}", "tamanho": 12} for x in linhas
        ]

    alt_b = (FIM_CONTEUDO - TOPO_CONTEUDO - ESPACO) // 2
    y_b = TOPO_CONTEUDO + alt_b + ESPACO
    metodologia = moldura(
        "Metodologia",
        "De onde vêm os dados, como o modelo foi avaliado e quais são os limites",
        [
            caixa_texto(
                est,
                (MARGEM, TOPO_CONTEUDO, meio, alt_b),
                bloco(
                    "Dados",
                    [
                        "Fonte: OpenFootball, licença CC0 verificada.",
                        "Brasileirão Série A, temporadas 2018 a 2025.",
                        "3.040 partidas, 380 por temporada, 20 clubes por temporada.",
                        "2026 está fora do escopo.",
                    ],
                ),
                fundo=est.superficie,
                borda=True,
            ),
            caixa_texto(
                est,
                (MARGEM + meio + ESPACO, TOPO_CONTEUDO, meio, alt_b),
                bloco(
                    "Modelo",
                    [
                        f"Modelo selecionado: {modelo}, versão {meta['versao']}.",
                        "Alvo: média de pontos nas próximas 5 partidas.",
                        "Validação temporal com janela expansiva; holdout exclusivo de 2025.",
                        "Baseline: média das últimas 5 partidas. Métricas: MAE e RMSE.",
                    ],
                ),
                fundo=est.superficie,
                borda=True,
            ),
            caixa_texto(
                est,
                (MARGEM, y_b, meio, alt_b),
                bloco(
                    "Como ler as previsões",
                    [
                        "Previsões são retrospectivas e têm margem de erro.",
                        "O intervalo de 90% é empírico e sem garantia estatística.",
                        "Não são certezas nem recomendação de aposta.",
                        f"Corte de treino: {meta['corte_treino']}.",
                    ],
                ),
                fundo=est.superficie,
                borda=True,
            ),
            caixa_texto(
                est,
                (MARGEM + meio + ESPACO, y_b, meio, alt_b),
                bloco(
                    "Limitações",
                    [
                        "Dados observacionais e uma única competição.",
                        "Um holdout temporal e poucas observações por equipe.",
                        "Importância das variáveis é preditiva, não causal.",
                        "Sem xG: hipóteses sobre métricas avançadas não foram avaliadas.",
                    ],
                ),
                fundo=est.superficie,
                borda=True,
            ),
        ],
    )

    return [
        pagina("Visão Geral", geral),
        pagina("Tendências", tendencias),
        pagina("Estatística", estatistica),
        pagina("Laboratório de Modelos", lab),
        pagina("Previsões", previsoes),
        pagina("Assistente", assistente),
        pagina("Metodologia", metodologia),
    ]
