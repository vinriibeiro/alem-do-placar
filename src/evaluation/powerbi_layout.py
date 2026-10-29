"""Layout PBIR do relatório Além do Placar: tema, cabeçalho, navegação e as sete páginas.

Canvas 1280x720. Faixa do cabeçalho em 0–72, filete amarelo em 72–76, navegação em 82–114,
conteúdo em 122–688 e rodapé em 694–718, com margem lateral de 16 px e espaçamento de 12 px.
As cores vêm dos tokens compartilhados com o site (``dashboard/assets/tema_tokens.json``).
"""

from __future__ import annotations

import hashlib
from typing import Any

from evaluation.nomes import ALVO

FATO = "fato_desempenho_equipes"
SCHEMA_PAGINA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"

LARGURA, ALTURA = 1280, 720
MARGEM, ESPACO = 16, 12
TOPO, FIM = 122, 688
UTIL = LARGURA - 2 * MARGEM  # 1248

TOKENS_PADRAO = {
    "cor-primaria": "#075e45",
    "cor-primaria-100": "#e3f1eb",
    "cor-destaque": "#15966a",
    "cor-destaque-700": "#0e7a55",
    "cor-amarelo": "#f3c84b",
    "cor-fundo": "#f3f5f4",
    "cor-superficie": "#ffffff",
    "cor-borda": "#dde3e1",
    "cor-borda-forte": "#c3ccc9",
    "cor-texto": "#202b29",
    "cor-texto-suave": "#55625f",
    "cor-sucesso": "#1a7f4b",
    "cor-alerta": "#9a6700",
    "cor-erro": "#b42318",
    "serie-1": "#075e45",
    "serie-2": "#15966a",
    "serie-3": "#f3c84b",
    "serie-4": "#202b29",
    "serie-5": "#7fb8a4",
    "serie-6": "#b98f1c",
}
FONTE = "Segoe UI"
FONTE_TITULO = "Segoe UI Semibold"
FONTE_VALOR = "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"
CINZA_LIMITE = "#AEB8B5"
# Silhueta neutra (SVG embutido) para destaques sem foto com licença livre.
SEM_FOTO = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
    "<rect width='64' height='64' rx='10' fill='%23E3F1EB'/><circle cx='32' cy='24' r='11' "
    "fill='%2315966A'/><path d='M12 56c2-12 10-18 20-18s18 6 20 18z' fill='%2315966A'/></svg>"
)


def _cor(tokens: dict[str, str], nome: str) -> str:
    return tokens.get(nome) or TOKENS_PADRAO[nome]


def construir_tema(tokens: dict[str, str]) -> dict[str, Any]:
    """Tema JSON do Power BI a partir dos tokens de design."""
    c = lambda n: _cor(tokens, n)  # noqa: E731
    serie = [c(f"serie-{i}") for i in range(1, 7)]
    solido = lambda hexa: {"solid": {"color": hexa}}  # noqa: E731
    return {
        "name": "AlemDoPlacar",
        "dataColors": serie + ["#a8d5c2", "#f8dd8f", "#5b6b67", "#3fb58a"],
        "background": c("cor-superficie"),
        "foreground": c("cor-texto"),
        "tableAccent": c("cor-destaque"),
        "good": c("cor-sucesso"),
        "neutral": c("cor-amarelo"),
        "bad": c("cor-erro"),
        "maximum": c("cor-destaque"),
        "center": c("cor-amarelo"),
        "minimum": c("cor-erro"),
        "null": c("cor-borda-forte"),
        "textClasses": {
            "callout": {"fontSize": 28, "fontFace": FONTE_TITULO, "color": c("cor-primaria")},
            "title": {"fontSize": 12, "fontFace": FONTE_TITULO, "color": c("cor-texto")},
            "header": {"fontSize": 11, "fontFace": FONTE_TITULO, "color": c("cor-texto")},
            "label": {"fontSize": 10, "fontFace": FONTE, "color": c("cor-texto-suave")},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "title": [
                        {
                            "show": True,
                            "fontColor": solido(c("cor-texto")),
                            "fontSize": 12,
                            "fontFamily": FONTE_TITULO,
                        }
                    ],
                    "background": [
                        {"show": True, "color": solido(c("cor-superficie")), "transparency": 0}
                    ],
                    "border": [
                        {"show": True, "color": solido(c("cor-borda")), "radius": 8, "width": 1}
                    ],
                    "dropShadow": [{"show": False}],
                }
            },
            "page": {
                "*": {"background": [{"color": solido(c("cor-fundo")), "transparency": 0}]},
            },
        },
    }


# --- Primitivas PBIR -------------------------------------------------------------------------

ROTULOS = {
    "nome_padronizado": "Equipe",
    "equipe": "Equipe",
    "escudo": " ",
    "ano": "Temporada",
    "temporada": "Temporada",
    "data_referencia": "Data",
    "previsao": "Previsão",
    "limite_inferior": "Limite inferior",
    "limite_superior": "Limite superior",
    "resultado_equipe": "Resultado",
    "variavel": "Variável",
    "nome": " ",
    "tipo": "Tipo",
    "mae_validacao": "MAE validação",
    "rmse_validacao": "RMSE validação",
    "mae_teste": "MAE teste 2025",
    "rmse_teste": "RMSE teste 2025",
    "diferenca_referencia": "vs. referência",
    "selecionado": "Escolhido",
    "imagem": " ",
    "detalhe": " ",
    "Posição": "Pos.",
    "Zona": "Zona",
    "Pontos (temporada)": "P",
    "Jogos (temporada)": "J",
    "Vitórias (temporada)": "V",
    "Empates (temporada)": "E",
    "Derrotas (temporada)": "D",
    "Saldo (temporada)": "SG",
    "Aproveitamento (temporada)": "Aprov.",
    "Média recente": "Últimos 5 jogos",
    "Média 10 jogos": "Últimos 10 jogos",
    "Média prevista": "Previsto",
    "Média observada": "Real",
    "Limite inferior": "Limite inferior (90%)",
    "Limite superior": "Limite superior (90%)",
    "Importância": "Aumento do erro",
    "MAE do modelo": "Erro médio absoluto (MAE)",
    "RMSE do modelo": "RMSE",
    "Volatilidade de pontos": "Oscilação",
    "Gols por jogo": "Gols marcados/jogo",
    "Gols sofridos por jogo": "Gols sofridos/jogo",
}


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


def _campo(ref: tuple[str, str, str]) -> dict:
    tabela, campo, tipo = ref
    return {tipo: {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": campo}}


def _projecao(ref: tuple[str, str, str]) -> dict:
    tabela, campo, _ = ref
    proj = {"field": _campo(ref), "queryRef": f"{tabela}.{campo}", "nativeQueryRef": campo}
    if campo in ROTULOS:
        proj["displayName"] = ROTULOS[campo]
    return proj


def _envelope(pos: tuple[int, int, int, int], visual: dict, chave: str | None = None) -> dict:
    x, y, largura, altura = pos
    env = {"position": {"x": x, "y": y, "width": largura, "height": altura}, "visual": visual}
    if chave:
        env["chave"] = chave
    return env


def _respiro(cima: int, baixo: int, esq: int, dir_: int) -> list[dict]:
    return [
        {
            "properties": {
                "top": _lit(f"{cima}D"),
                "bottom": _lit(f"{baixo}D"),
                "left": _lit(f"{esq}D"),
                "right": _lit(f"{dir_}D"),
            }
        }
    ]


class Estilo:
    """Cores resolvidas dos tokens."""

    def __init__(self, tokens: dict[str, str]) -> None:
        self.primaria = _cor(tokens, "cor-primaria")
        self.destaque = _cor(tokens, "cor-destaque")
        self.destaque_escuro = _cor(tokens, "cor-destaque-700")
        self.amarelo = _cor(tokens, "cor-amarelo")
        self.superficie = _cor(tokens, "cor-superficie")
        self.fundo = _cor(tokens, "cor-fundo")
        self.borda = _cor(tokens, "cor-borda")
        self.texto = _cor(tokens, "cor-texto")
        self.suave = _cor(tokens, "cor-texto-suave")
        self.alerta = _cor(tokens, "cor-alerta")
        self.claro = _cor(tokens, "cor-primaria-100")


def _contexto(est: Estilo, fundo: str | None, borda: bool, cor_borda: str | None = None) -> dict:
    """Fundo, borda e sombra do contêiner. ``borda=False`` desliga a borda herdada do tema."""
    return {
        "background": [
            {
                "properties": {
                    "show": _lit("true" if fundo else "false"),
                    "color": _solido(fundo or est.superficie),
                    "transparency": _lit("0D"),
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": _lit("true" if borda else "false"),
                    "color": _solido(cor_borda or est.borda),
                    "radius": _lit("8D" if borda else "0D"),
                    "width": _lit("1D"),
                }
            }
        ],
        "dropShadow": [{"properties": {"show": _lit("false")}}],
    }


def caixa_texto(
    est: Estilo,
    pos: tuple[int, int, int, int],
    paragrafos: list[dict],
    fundo: str | None = None,
    borda: bool = False,
    respiro: tuple[int, int, int, int] = (8, 8, 12, 12),
    cor_borda: str | None = None,
) -> dict:
    """Caixa de texto. Cada parágrafo é um dict com ``texto`` (ou ``trechos``: lista de dicts),
    ``tamanho``, ``cor``, ``negrito``, ``url`` e ``alinhar``."""
    blocos = []
    for p in paragrafos:
        execucoes = []
        for t in p.get("trechos") or [p]:
            estilo = {
                "fontFamily": FONTE,
                "fontSize": f"{t.get('tamanho', p.get('tamanho', 12))}px",
                "color": t.get("cor", p.get("cor", est.texto)),
            }
            if t.get("negrito", p.get("negrito")):
                estilo["fontWeight"] = "bold"
            if t.get("url"):
                estilo["textDecoration"] = "underline"
            execucao: dict[str, Any] = {"value": t["texto"], "textStyle": estilo}
            if t.get("url"):
                execucao["url"] = t["url"]
            execucoes.append(execucao)
        bloco: dict[str, Any] = {"textRuns": execucoes}
        if p.get("alinhar"):
            bloco["horizontalTextAlignment"] = p["alinhar"]
        blocos.append(bloco)
    contexto = _contexto(est, fundo, borda, cor_borda)
    contexto["padding"] = _respiro(*respiro)
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
    tamanho_titulo: int = 12,
    respiro: int = 8,
    ordenar: tuple[str, str, str] | None = None,
    crescente: bool = False,
    chave: str | None = None,
) -> dict:
    estado = {p: {"projections": [_projecao(r) for r in refs]} for p, refs in papeis.items()}
    consulta: dict[str, Any] = {"queryState": estado}
    if ordenar:
        consulta["sortDefinition"] = {
            "sort": [
                {"field": _campo(ordenar), "direction": "Ascending" if crescente else "Descending"}
            ],
            "isDefaultSort": True,
        }
    v: dict[str, Any] = {"visualType": tipo, "query": consulta}
    if objetos:
        v["objects"] = objetos
    contexto = _contexto(est, est.superficie, True)
    contexto["title"] = [
        {
            "properties": {
                "show": _lit("true"),
                "text": _lit(f"'{titulo}'"),
                "titleWrap": _lit("true"),
                "fontSize": _lit(f"{tamanho_titulo}D"),
                "fontFamily": _lit(f"'{FONTE_TITULO}'"),
                "fontColor": _solido(est.texto),
            }
        }
    ]
    contexto["subTitle"] = [{"properties": {"show": _lit("false")}}]
    contexto["padding"] = _respiro(respiro, respiro, respiro + 2, respiro + 2)
    v["visualContainerObjects"] = contexto
    return _envelope(pos, v, chave)


def cartao(est: Estilo, pos, medida: tuple[str, str, str], titulo: str) -> dict:
    """Título no contêiner e só o valor no corpo (o rótulo da categoria repetiria o nome)."""
    objetos = {
        "labels": [
            {
                "properties": {
                    "fontFamily": _lit(FONTE_VALOR),
                    "fontSize": _lit("26D"),
                    "color": _solido(est.primaria),
                }
            }
        ],
        "categoryLabels": [{"properties": {"show": _lit("false")}}],
    }
    return visual(est, "card", pos, {"Values": [medida]}, titulo, objetos, 11, 6)


def cartao_texto(est: Estilo, pos, medida: tuple[str, str, str], titulo: str) -> dict:
    """Cartão para medidas de texto (avisos), com fonte menor."""
    objetos = {
        "labels": [{"properties": {"fontSize": _lit("12D"), "color": _solido(est.texto)}}],
        "categoryLabels": [{"properties": {"show": _lit("false")}}],
    }
    return visual(est, "card", pos, {"Values": [medida]}, titulo, objetos, 11, 6)


def seletor(
    est: Estilo,
    pos,
    coluna: tuple[str, str, str],
    titulo: str,
    padrao: str | None = None,
    chave: str | None = None,
) -> dict:
    """Segmentação em lista suspensa. ``padrao`` é o literal Power BI pré-selecionado
    (ex.: ``"2025L"`` ou ``"'Flamengo'"``), com seleção única."""
    objetos: dict[str, Any] = {
        "data": [{"properties": {"mode": _lit("'Dropdown'")}}],
        "header": [{"properties": {"show": _lit("false")}}],
    }
    if padrao is not None:
        tabela_, campo, _ = coluna
        condicao = {
            "In": {
                "Expressions": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": campo}}
                ],
                "Values": [[{"Literal": {"Value": padrao}}]],
            }
        }
        filtro = {
            "Version": 2,
            "From": [{"Name": "s", "Entity": tabela_, "Type": 0}],
            "Where": [{"Condition": condicao}],
        }
        objetos["selection"] = [{"properties": {"singleSelect": _lit("true")}}]
        objetos["general"] = [{"properties": {"filter": {"filter": filtro}}}]
    return visual(est, "slicer", pos, {"Values": [coluna]}, titulo, objetos, 11, 6, chave=chave)


def tabela(
    est: Estilo,
    pos,
    colunas: list,
    titulo: str,
    ordenar=None,
    crescente: bool = False,
    altura_imagem: int = 22,
    chave: str | None = None,
) -> dict:
    objetos = {"grid": [{"properties": {"imageHeight": _lit(f"{altura_imagem}D")}}]}
    return visual(
        est,
        "tableEx",
        pos,
        {"Values": colunas},
        titulo,
        objetos,
        ordenar=ordenar,
        crescente=crescente,
        chave=chave,
    )


def _estilo_series(series: dict[str, dict]) -> dict:
    """Cor, espessura e traço por série de um gráfico de linhas (seletor pelo queryRef)."""
    ponto, linhas = [], []
    for query_ref, s in series.items():
        sel = {"metadata": query_ref}
        ponto.append({"properties": {"fill": _solido(s["cor"])}, "selector": sel})
        props = {
            "strokeWidth": _lit(f"{s.get('espessura', 2)}D"),
            "showMarker": _lit("false"),
            "lineStyle": _lit(f"'{s.get('traco', 'solid')}'"),
        }
        linhas.append({"properties": props, "selector": sel})
    return {"dataPoint": ponto, "lineStyles": linhas}


def navegador(est: Estilo, pos) -> dict:
    return _envelope(
        pos,
        {
            "visualType": "pageNavigator",
            "visualContainerObjects": {
                "background": [{"properties": {"show": _lit("false")}}],
                "border": [{"properties": {"show": _lit("false")}}],
                "visualHeader": [{"properties": {"show": _lit("false")}}],
            },
        },
    )


def moldura(est: Estilo, titulo: str, subtitulo: str, rodape: str, corpo: list[dict]) -> list[dict]:
    """Faixa única do cabeçalho, filete amarelo, navegação, corpo e rodapé."""
    topo = [
        caixa_texto(
            est,
            (0, 0, LARGURA, 72),
            [
                {"texto": titulo, "tamanho": 21, "cor": "#FFFFFF", "negrito": True},
                {
                    "trechos": [
                        {
                            "texto": "ALÉM DO PLACAR",
                            "tamanho": 11,
                            "cor": est.amarelo,
                            "negrito": True,
                        },
                        {"texto": f"   ·   {subtitulo}", "tamanho": 11, "cor": "#D5EBE1"},
                    ]
                },
            ],
            fundo=est.primaria,
            respiro=(8, 4, 24, 24),
        ),
        caixa_texto(
            est,
            (0, 72, LARGURA, 4),
            [{"texto": " ", "tamanho": 1}],
            fundo=est.amarelo,
            respiro=(0, 0, 0, 0),
        ),
        navegador(est, (MARGEM, 82, UTIL, 32)),
    ]
    base = [
        caixa_texto(
            est,
            (MARGEM, 694, UTIL, 24),
            [{"texto": rodape, "tamanho": 10, "cor": est.suave}],
            respiro=(3, 0, 4, 4),
        )
    ]
    return topo + corpo + base


def pagina(nome: str, visuais: list[dict], sem_filtro: list[tuple[str, str]] = ()) -> dict:
    """Página PBIR. ``sem_filtro`` lista pares (chave de origem, chave de destino) cuja
    interação de filtro é desligada (ex.: segmentação de equipe que não deve filtrar a matriz)."""
    ident = _id(nome)
    nomes = {}
    containers = []
    for i, v in enumerate(visuais):
        nome_visual = _id(ident, str(i))
        if v.get("chave"):
            nomes[v["chave"]] = nome_visual
        containers.append(
            {
                "$schema": SCHEMA_VISUAL,
                "name": nome_visual,
                "position": {**v["position"], "z": i, "tabOrder": i},
                "visual": v["visual"],
            }
        )
    corpo: dict[str, Any] = {
        "$schema": SCHEMA_PAGINA,
        "name": ident,
        "displayName": nome,
        "displayOption": "FitToPage",
        "height": ALTURA,
        "width": LARGURA,
    }
    if sem_filtro:
        corpo["visualInteractions"] = [
            {"source": nomes[a], "target": nomes[b], "type": "NoFilter"} for a, b in sem_filtro
        ]
    return {"id": ident, "pagina": corpo, "visuais": containers}


def _linha(x: int, larguras: list[int]) -> list[int]:
    xs = []
    for w in larguras:
        xs.append(x)
        x += w + ESPACO
    return xs


def _bloco(est: Estilo, titulo: str, linhas: list[str], tamanho: int = 12) -> list[dict]:
    return [{"texto": titulo, "tamanho": 14, "negrito": True, "cor": est.primaria}] + [
        {"texto": x, "tamanho": tamanho} for x in linhas
    ]


def _decimal(valor: float, casas: int) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


# --- Páginas ---------------------------------------------------------------------------------


def construir_paginas(
    meta: dict[str, Any],
    tokens: dict[str, str],
    url_central: str | None = None,
    com_escudos: bool = False,
    com_destaques: bool = False,
    url_repositorio: str | None = None,
) -> list[dict]:
    est = Estilo(tokens)
    eq = c_("dim_equipes", "nome_padronizado")
    ano = c_("dim_temporadas", "ano")
    escudo = [c_("dim_equipes", "escudo")] if com_escudos else []
    ultimo_ano = str(meta.get("ultimo_ano", "2025"))
    rodape = (
        f"Fonte: OpenFootball (CC0) · Temporadas 2018–{ultimo_ano} · "
        f"Última partida nos dados: {meta.get('ultima_partida', '—')} · "
        f"Modelo: {meta.get('modelo_nome', meta['modelo_selecionado'])} ({meta['versao']}) · "
        "Projeto Além do Placar"
    )
    mae = float(meta.get("mae_holdout") or 0)
    cobertura = meta.get("cobertura")
    rotulos = {"labels": [{"properties": {"show": _lit("true"), "fontSize": _lit("10D")}}]}

    # 1. Visão Geral ------------------------------------------------------------------------
    esq = 760
    dir_x = MARGEM + esq + ESPACO
    dir_w = UTIL - esq - ESPACO  # 476
    cards_y = TOPO + 72 + ESPACO
    meia = (dir_w - ESPACO) // 2
    alt_card = (FIM - cards_y - ESPACO) // 2
    destaques = []
    if com_destaques:
        especs = [
            ("destaque_artilheiro", "Artilheiro do campeonato"),
            ("destaque_craque", "Craque do Brasileirão (prêmio oficial)"),
            ("destaque_goleiro", "Melhor goleiro (prêmio oficial)"),
            ("destaque_ataque", "Melhor ataque"),
        ]
        for i, (tab, titulo) in enumerate(especs):
            x = dir_x + (i % 2) * (meia + ESPACO)
            y = cards_y + (i // 2) * (alt_card + ESPACO)
            destaques.append(
                tabela(
                    est,
                    (x, y, meia, alt_card),
                    [c_(tab, "imagem"), c_(tab, "nome"), c_(tab, "detalhe")],
                    titulo,
                    altura_imagem=64,
                )
            )
    geral = moldura(
        est,
        "Visão Geral",
        "Classificação e destaques da temporada escolhida",
        rodape,
        [
            tabela(
                est,
                (MARGEM, TOPO, esq, FIM - TOPO),
                [
                    *escudo,
                    m_("Posição"),
                    eq,
                    m_("Pontos (temporada)"),
                    m_("Jogos (temporada)"),
                    m_("Vitórias (temporada)"),
                    m_("Empates (temporada)"),
                    m_("Derrotas (temporada)"),
                    m_("Saldo (temporada)"),
                    m_("Aproveitamento (temporada)"),
                    m_("Zona"),
                ],
                "Classificação · critérios: pontos, vitórias, saldo de gols e gols marcados",
                ordenar=m_("Posição"),
                crescente=True,
            ),
            seletor(est, (dir_x, TOPO, 180, 72), ano, "Temporada", padrao=f"{ultimo_ano}L"),
            cartao_texto(
                est,
                (dir_x + 192, TOPO, dir_w - 192, 72),
                m_("Aviso temporada"),
                "Sobre esta tabela",
            ),
            *destaques,
        ],
    )

    # 2. Tendências -------------------------------------------------------------------------
    col = 400
    tendencias = moldura(
        est,
        "Tendências",
        "Médias móveis de pontos e aproveitamento por equipe e temporada",
        rodape,
        [
            seletor(est, (MARGEM, TOPO, 194, 72), ano, "Temporada"),
            seletor(
                est,
                (MARGEM + 206, TOPO, 194, 72),
                eq,
                "Equipe",
                padrao="'Flamengo'",
                chave="equipe",
            ),
            visual(
                est,
                "lineChart",
                (MARGEM, TOPO + 84, col, 236),
                {
                    "Category": [c_("analitico", "data_referencia")],
                    "Y": [m_("Média recente"), m_("Média 10 jogos")],
                },
                "Média móvel de pontos da equipe escolhida",
                objetos=_estilo_series(
                    {
                        f"{FATO}.Média recente": {"cor": est.destaque, "espessura": 2},
                        f"{FATO}.Média 10 jogos": {"cor": est.amarelo, "espessura": 3},
                    }
                ),
            ),
            visual(
                est,
                "clusteredBarChart",
                (MARGEM, TOPO + 324, col, FIM - (TOPO + 324)),
                {"Category": [eq], "Y": [m_("Média recente")]},
                "Média dos últimos 5 jogos, todas as equipes",
                ordenar=m_("Média recente"),
                chave="barras",
            ),
            visual(
                est,
                "pivotTable",
                (MARGEM + col + ESPACO, TOPO, UTIL - col - ESPACO, FIM - TOPO),
                {"Rows": [eq], "Columns": [ano], "Values": [m_("Aproveitamento")]},
                "Aproveitamento por equipe e temporada",
                chave="matriz",
            ),
        ],
    )

    # 3. Estatísticas -----------------------------------------------------------------------
    meio = (UTIL - ESPACO) // 2
    y_a = TOPO + 84
    alt = (FIM - y_a - ESPACO) // 2
    estatisticas = moldura(
        est,
        "Estatísticas",
        "Resultados, pontos por jogo, dispersão e regularidade",
        rodape,
        [
            seletor(est, (MARGEM, TOPO, 220, 72), ano, "Temporada", padrao=f"{ultimo_ano}L"),
            caixa_texto(
                est,
                (MARGEM + 232, TOPO, UTIL - 232, 72),
                [
                    {
                        "texto": "Cada partida gera um resultado para cada equipe; por isso vitórias e derrotas "
                        "têm a mesma proporção. Pontos por jogo = pontos ÷ partidas disputadas.",
                        "tamanho": 12,
                        "cor": est.suave,
                    }
                ],
                fundo=est.superficie,
                borda=True,
            ),
            visual(
                est,
                "clusteredColumnChart",
                (MARGEM, y_a, meio, alt),
                {"Category": [c_(FATO, "resultado_equipe")], "Y": [m_("% dos resultados")]},
                "Distribuição de resultados",
                objetos=rotulos,
            ),
            visual(
                est,
                "lineClusteredColumnComboChart",
                (MARGEM + meio + ESPACO, y_a, meio, alt),
                {"Category": [eq], "Y": [m_("Pontos por jogo")], "Y2": [m_("Média do campeonato")]},
                "Pontos por jogo por equipe e média do campeonato",
                ordenar=m_("Pontos por jogo"),
            ),
            visual(
                est,
                "scatterChart",
                (MARGEM, y_a + alt + ESPACO, meio, alt),
                {"Category": [eq], "X": [m_("Saldo de gols")], "Y": [m_("Pontos totais")]},
                "Saldo de gols × pontos por equipe",
            ),
            tabela(
                est,
                (MARGEM + meio + ESPACO, y_a + alt + ESPACO, meio, alt),
                [
                    *escudo,
                    eq,
                    m_("Pontos por jogo"),
                    m_("Volatilidade de pontos"),
                    m_("Gols por jogo"),
                    m_("Gols sofridos por jogo"),
                ],
                "Regularidade e gols por equipe",
                ordenar=m_("Pontos por jogo"),
            ),
        ],
    )

    # 4. Modelos ----------------------------------------------------------------------------
    texto_w = 380
    dx = MARGEM + texto_w + ESPACO
    dw = UTIL - texto_w - ESPACO  # 856
    gw = (dw - ESPACO) // 2
    pergunta = lambda t: {"texto": t, "tamanho": 13, "negrito": True, "cor": est.primaria}  # noqa: E731
    resposta = lambda t: {"texto": t, "tamanho": 11}  # noqa: E731
    explicacao = [
        pergunta("O que estamos prevendo?"),
        resposta(f"{ALVO[0]} de cada equipe, calculada logo após cada partida."),
        pergunta("Como a previsão é feita?"),
        resposta(
            "Com 12 informações do desempenho recente: médias de pontos e de saldo de gols em "
            "3, 5 e 10 jogos, oscilação, desempenho em casa e fora, jogos disputados e dias de descanso."
        ),
        pergunta("Quais modelos foram testados?"),
        resposta(
            "Duas referências simples (média dos últimos 5 jogos e média histórica) e três modelos de "
            "Machine Learning: Regressão Ridge, Random Forest e Gradient Boosting."
        ),
        pergunta("Qual foi o escolhido?"),
        resposta(
            "A Regressão Ridge: teve o menor erro médio e o menor RMSE na validação de 2022 a 2024 e "
            "confirmou o ganho no teste com 2025, dados que ela nunca viu."
        ),
        pergunta("Qual é a margem de erro?"),
        resposta(
            f"Em média, {_decimal(mae, 2)} ponto por jogo. Se o modelo prevê 1,6 ponto por jogo "
            f"(8 pontos em 5 jogos), o resultado real costuma ficar a cerca de {_decimal(mae * 5, 1)} "
            "pontos disso, para mais ou para menos."
        ),
        {
            "texto": "Quanto menor o erro, mais perto da realidade. A importância de uma variável mostra "
            "associação com a previsão, não causa.",
            "tamanho": 10,
            "cor": est.suave,
        },
    ]
    modelos = moldura(
        est,
        "Modelos",
        "Como as previsões são feitas e quão bem elas funcionam",
        rodape,
        [
            caixa_texto(
                est,
                (MARGEM, TOPO, texto_w, FIM - TOPO),
                explicacao,
                fundo=est.superficie,
                borda=True,
                respiro=(12, 12, 16, 16),
            ),
            visual(
                est,
                "clusteredBarChart",
                (dx, TOPO, gw, 200),
                {"Category": [c_("comparacao_modelos", "nome")], "Y": [m_("MAE do modelo")]},
                "Erro médio absoluto na validação (menor é melhor)",
                ordenar=m_("MAE do modelo"),
                crescente=True,
                objetos=rotulos,
            ),
            visual(
                est,
                "clusteredBarChart",
                (dx + gw + ESPACO, TOPO, gw, 200),
                {"Category": [c_("comparacao_modelos", "nome")], "Y": [m_("RMSE do modelo")]},
                "RMSE na validação (pesa mais os erros grandes)",
                ordenar=m_("RMSE do modelo"),
                crescente=True,
                objetos=rotulos,
            ),
            tabela(
                est,
                (dx, TOPO + 212, dw, 160),
                [
                    c_("comparacao_modelos", c)
                    for c in (
                        "nome",
                        "tipo",
                        "mae_validacao",
                        "rmse_validacao",
                        "mae_teste",
                        "rmse_teste",
                        "diferenca_referencia",
                        "selecionado",
                    )
                ],
                "Comparação dos modelos (referência = média dos últimos 5 jogos)",
                ordenar=c_("comparacao_modelos", "mae_validacao"),
                crescente=True,
            ),
            visual(
                est,
                "clusteredBarChart",
                (dx, TOPO + 384, dw, FIM - (TOPO + 384)),
                {"Category": [c_("importancias", "variavel")], "Y": [m_("Importância")]},
                "O que mais pesa na previsão (quanto o erro aumenta sem cada informação)",
                ordenar=m_("Importância"),
            ),
        ],
    )

    # 5. Previsões --------------------------------------------------------------------------
    prev_w = 800
    faixa = "Faixa empírica de 90%"
    if cobertura:
        faixa += f" (cobertura observada no teste de 2025: {_decimal(float(cobertura) * 100, 1)}%)"
    previsoes = moldura(
        est,
        "Previsões",
        "Média de pontos prevista para os próximos 5 jogos · teste com 2025",
        rodape,
        [
            seletor(est, (MARGEM, TOPO, 300, 72), eq, "Equipe", padrao="'Flamengo'"),
            caixa_texto(
                est,
                (MARGEM + 312, TOPO, prev_w - 312, 72),
                [
                    {
                        "texto": "As previsões são estimativas calculadas a partir dos dados disponíveis. "
                        "Os resultados reais podem ser diferentes.",
                        "tamanho": 11,
                        "negrito": True,
                        "cor": est.alerta,
                    },
                    {"texto": faixa + ".", "tamanho": 10, "cor": est.suave},
                ],
                fundo="#FFF8E1",
                borda=True,
                cor_borda="#F3D98A",
            ),
            visual(
                est,
                "lineChart",
                (MARGEM, TOPO + 84, prev_w, 384),
                {
                    "Category": [c_("previsoes", "data_referencia")],
                    "Y": [
                        m_("Média prevista"),
                        m_("Média observada"),
                        m_("Limite inferior"),
                        m_("Limite superior"),
                    ],
                },
                "Previsto, real e faixa de incerteza",
                objetos=_estilo_series(
                    {
                        f"{FATO}.Média prevista": {"cor": est.primaria, "espessura": 3},
                        f"{FATO}.Média observada": {"cor": est.amarelo, "espessura": 2},
                        f"{FATO}.Limite inferior": {
                            "cor": CINZA_LIMITE,
                            "espessura": 1,
                            "traco": "dashed",
                        },
                        f"{FATO}.Limite superior": {
                            "cor": CINZA_LIMITE,
                            "espessura": 1,
                            "traco": "dashed",
                        },
                    }
                ),
            ),
            cartao(
                est,
                (MARGEM, TOPO + 472, 258, FIM - (TOPO + 472)),
                m_("Média prevista"),
                "Média prevista",
            ),
            cartao(
                est,
                (MARGEM + 270, TOPO + 472, 258, FIM - (TOPO + 472)),
                m_("Média observada"),
                "Média real",
            ),
            cartao(
                est,
                (MARGEM + 540, TOPO + 472, prev_w - 540, FIM - (TOPO + 472)),
                m_("Erro absoluto médio"),
                "Erro médio desta equipe",
            ),
            tabela(
                est,
                (MARGEM + prev_w + ESPACO, TOPO, UTIL - prev_w - ESPACO, FIM - TOPO),
                [
                    c_("previsoes", c)
                    for c in ("data_referencia", "previsao", "limite_inferior", "limite_superior")
                ],
                "Previsões e faixa por data",
            ),
        ],
    )

    # 6. Central de Consulta ----------------------------------------------------------------
    temas = [
        (
            "Campeonato",
            ["Qual equipe teve o melhor ataque em 2025?", "Como funciona a classificação?"],
        ),
        (
            "Indicadores",
            ["O que é saldo médio de gols?", "Como interpretar o gráfico de tendências?"],
        ),
        ("Modelos", ["O que significa MAE?", "Qual algoritmo apresentou o menor erro?"]),
        ("Previsões", ["Como o modelo calcula as previsões?", "Por que as previsões podem errar?"]),
        ("Dados", ["Quais dados foram utilizados?", "Qual é a diferença entre treino e teste?"]),
        (
            "Metodologia",
            ["Como foi feita a validação dos modelos?", "Quais são as limitações do projeto?"],
        ),
    ]
    tw = (UTIL - 2 * ESPACO) // 3
    th = (FIM - (TOPO + 212) - ESPACO) // 2
    caixas_temas = []
    for i, (titulo, perguntas) in enumerate(temas):
        x = MARGEM + (i % 3) * (tw + ESPACO)
        y = TOPO + 212 + (i // 3) * (th + ESPACO)
        caixas_temas.append(
            caixa_texto(
                est,
                (x, y, tw, th),
                [{"texto": titulo, "tamanho": 14, "negrito": True, "cor": est.primaria}]
                + [{"texto": f"“{p}”", "tamanho": 12} for p in perguntas],
                fundo=est.superficie,
                borda=True,
                respiro=(12, 12, 16, 16),
            )
        )
    if url_central:
        acesso = [
            {
                "texto": "Abrir a Central de Consulta",
                "tamanho": 18,
                "negrito": True,
                "cor": "#FFFFFF",
            },
            {"texto": "Abre em uma nova aba do navegador.", "tamanho": 11, "cor": "#D5EBE1"},
            {
                "texto": "Acessar a central  →",
                "tamanho": 15,
                "negrito": True,
                "cor": est.amarelo,
                "url": url_central,
            },
        ]
    else:
        acesso = [
            {"texto": "Central de Consulta", "tamanho": 18, "negrito": True, "cor": "#FFFFFF"},
            {
                "texto": "O endereço público será exibido aqui após a publicação.",
                "tamanho": 12,
                "cor": "#D5EBE1",
            },
        ]
    central = moldura(
        est,
        "Central de Consulta",
        "Respostas sobre o campeonato, os dados e os modelos deste projeto",
        rodape,
        [
            caixa_texto(
                est,
                (MARGEM, TOPO, 820, 200),
                [
                    {
                        "texto": "Tire suas dúvidas sobre o Brasileirão e o projeto",
                        "tamanho": 20,
                        "negrito": True,
                        "cor": est.primaria,
                    },
                    {
                        "texto": "Pesquise em português sobre classificação, estatísticas das equipes, indicadores, "
                        "modelos, métricas e limitações. As respostas vêm dos dados e da documentação do "
                        "projeto, sempre com a origem indicada.",
                        "tamanho": 13,
                    },
                    {
                        "texto": "Gratuita e sem inteligência artificial paga: funciona com uma base de conhecimento "
                        "e estatísticas calculadas a partir das partidas. Perguntas fora do tema são recusadas "
                        "e nada é inventado.",
                        "tamanho": 12,
                        "cor": est.suave,
                    },
                ],
                fundo=est.superficie,
                borda=True,
                respiro=(14, 12, 18, 18),
            ),
            caixa_texto(
                est,
                (MARGEM + 832, TOPO, UTIL - 832, 200),
                acesso,
                fundo=est.primaria,
                respiro=(18, 12, 20, 20),
            ),
            *caixas_temas,
        ],
    )

    # 7. Metodologia ------------------------------------------------------------------------
    n_cards = 5 if cobertura else 4
    larg = (UTIL - (n_cards - 1) * ESPACO) // n_cards
    xs = _linha(MARGEM, [larg] * n_cards)
    cards = [
        cartao(est, (xs[0], TOPO, larg, 88), m_("Partidas"), "Partidas analisadas"),
        cartao(est, (xs[1], TOPO, larg, 88), m_("Modelos avaliados"), "Modelos comparados"),
        cartao(
            est, (xs[2], TOPO, larg, 88), m_("MAE global selecionado"), "Erro médio (MAE) no teste"
        ),
        cartao(est, (xs[3], TOPO, larg, 88), m_("RMSE global selecionado"), "RMSE no teste"),
    ]
    if cobertura:
        cards.append(
            cartao(
                est,
                (xs[4], TOPO, larg, 88),
                m_("Cobertura do intervalo"),
                "Cobertura da faixa de 90%",
            )
        )
    y1 = TOPO + 100
    cw = (UTIL - 2 * ESPACO) // 3
    alt_col = 218
    etapas = [
        "Coleta",
        "Limpeza",
        "Exploração",
        "Atributos",
        "Treino",
        "Validação",
        "Teste",
        "Previsões",
    ]
    ew = (UTIL - 7 * 8) // 8
    y2 = y1 + alt_col + ESPACO
    passos = [
        caixa_texto(
            est,
            (MARGEM + i * (ew + 8), y2, ew, 44),
            [
                {
                    "texto": f"{i + 1} · {e}",
                    "tamanho": 12,
                    "negrito": True,
                    "cor": "#FFFFFF",
                    "alinhar": "center",
                }
            ],
            fundo=est.destaque_escuro if i % 2 == 0 else est.primaria,
            respiro=(12, 4, 4, 4),
        )
        for i, e in enumerate(etapas)
    ]
    y3 = y2 + 44 + ESPACO
    explorar = [
        {
            "texto": "Explore o projeto por dentro",
            "tamanho": 15,
            "negrito": True,
            "cor": est.primaria,
        },
        {
            "texto": "O código, a documentação, a metodologia completa e o dicionário de dados ficam no "
            "repositório público do projeto.",
            "tamanho": 12,
        },
    ]
    links = []
    if url_repositorio:
        links.append({"texto": "Acessar o GitHub", "url": url_repositorio})
    if url_central:
        links.append({"texto": "Abrir a Central de Consulta", "url": url_central})
    if links:
        trechos = []
        for i, link in enumerate(links):
            if i:
                trechos.append({"texto": "     ", "tamanho": 12})
            trechos.append({**link, "tamanho": 12, "negrito": True, "cor": est.destaque_escuro})
        explorar.append({"trechos": trechos})
    else:
        explorar.append(
            {
                "texto": "Os links serão exibidos após a publicação do repositório.",
                "tamanho": 11,
                "cor": est.suave,
            }
        )
    colunas_texto = [
        (
            "Sobre o projeto",
            [
                "Estudamos se o desempenho recente de uma equipe ajuda a antecipar os próximos jogos.",
                "O dashboard mostra classificação, tendências e estatísticas, e compara previsões com o que aconteceu.",
                "As previsões ajudam a entender tendências; não são apostas nem certezas.",
            ],
        ),
        (
            "Origem e preparação dos dados",
            [
                f"OpenFootball (licença CC0): Brasileirão Série A de 2018 a {ultimo_ano}, 380 partidas por temporada.",
                "Nomes de clubes padronizados, datas e placares validados; duplicidades e placares inválidos são barrados.",
                "Atributos calculados só com jogos já encerrados; atualização manual ao fim de cada temporada.",
            ],
        ),
        (
            "Cuidados metodológicos",
            [
                "Treino, validação (2022–2024) e teste (2025) separados no tempo, sem dados do futuro.",
                "Todo modelo é comparado com uma referência simples; só vale o ganho que supera essa referência.",
                "Uma competição e poucos jogos por equipe limitam a generalização; importância não é causa.",
            ],
        ),
    ]
    metodologia = moldura(
        est,
        "Metodologia",
        "Como o projeto foi construído, explicado para quem nunca estudou Ciência de Dados",
        rodape,
        cards
        + [
            caixa_texto(
                est,
                (MARGEM + i * (cw + ESPACO), y1, cw, alt_col),
                _bloco(est, titulo, linhas),
                fundo=est.superficie,
                borda=True,
                respiro=(12, 12, 16, 16),
            )
            for i, (titulo, linhas) in enumerate(colunas_texto)
        ]
        + passos
        + [
            caixa_texto(
                est,
                (MARGEM, y3, UTIL, FIM - y3),
                explorar,
                fundo=est.claro,
                borda=True,
                cor_borda=est.claro,
                respiro=(12, 10, 18, 18),
            )
        ],
    )

    return [
        pagina("Visão Geral", geral),
        pagina("Tendências", tendencias, [("equipe", "barras"), ("equipe", "matriz")]),
        pagina("Estatísticas", estatisticas),
        pagina("Modelos", modelos),
        pagina("Previsões", previsoes),
        pagina("Central de Consulta", central),
        pagina("Metodologia", metodologia),
    ]
