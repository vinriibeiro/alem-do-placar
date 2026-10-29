"""Renderização das páginas HTML (modelo base + conteúdo) e da página de Metodologia.

Tudo é gerado uma vez na inicialização. A Metodologia converte os documentos do projeto
(``model_card.md`` e ``methodology.md``), que são conteúdo confiável versionado no repositório.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify

AQUI = Path(__file__).resolve().parent
TEMPLATES = AQUI / "templates"

PAGINAS = {
    "inicio": (
        "Além do Placar — Inteligência esportiva do Brasileirão",
        "Dados, estatística e IA sobre o Campeonato Brasileiro Série A 2018–2025: dashboard, "
        "assistente em português e metodologia aberta.",
    ),
    "dashboard": (
        "Dashboard — Além do Placar",
        "Relatório interativo em Power BI com visão geral, tendências, estatística, modelos e previsões.",
    ),
    "assistente": (
        "Assistente — Além do Placar",
        "Pergunte em português sobre classificações, confrontos, gols, sequências e previsões do "
        "Brasileirão. Respostas com fonte, período e limitações.",
    ),
    "metodologia": (
        "Metodologia — Além do Placar",
        "Fontes, validação, modelo preditivo, métricas, hipóteses e limitações do projeto Além do Placar.",
    ),
}
FIGURAS = {
    "importancias.png": "Importância por permutação: aumento do erro (MAE) ao embaralhar cada variável no holdout de 2025.",
    "previsto_vs_observado.png": "Previsto contra observado no holdout de 2025, com a linha de identidade.",
    "residuos_hist.png": "Distribuição dos resíduos (previsão menos observado) no holdout de 2025.",
}


def _md(texto: str, prefixo: str) -> tuple[str, list[tuple[str, str]]]:
    md = markdown.Markdown(
        extensions=["tables", "toc", "fenced_code", "sane_lists"],
        extension_configs={
            "toc": {
                "baselevel": 2,
                "slugify": lambda v, sep: f"{prefixo}-{slugify(v, sep)}",
            }
        },
    )
    html = md.convert(texto)
    # O primeiro nível 1 vira título de seção; o sumário lista os níveis seguintes.
    itens = [
        (n["id"], n["name"])
        for raiz_t in md.toc_tokens
        for n in _achatar(raiz_t)
        if n["level"] == 3
    ]
    return html, itens


def _achatar(token: dict):
    yield token
    for filho in token.get("children", []):
        yield from _achatar(filho)


def _sem_scripts(html: str) -> str:
    return re.sub(r"<script.*?</script>", "", html, flags=re.S | re.I)


def montar_metodologia(raiz_docs: Path, figuras_existentes: set[str]) -> str:
    secoes, sumario = [], []
    for arquivo, prefixo in (("model_card.md", "modelo"), ("methodology.md", "exploratoria")):
        caminho = raiz_docs / arquivo
        if not caminho.is_file():
            continue
        html, itens = _md(caminho.read_text(encoding="utf-8"), prefixo)
        secoes.append(_sem_scripts(html))
        sumario.extend(itens)
        if prefixo == "modelo" and figuras_existentes:
            figs = "".join(
                f'<figure><img src="/figuras/{nome}" alt="{legenda}" loading="lazy">'
                f"<figcaption>{legenda}</figcaption></figure>"
                for nome, legenda in FIGURAS.items()
                if nome in figuras_existentes
            )
            secoes.append(
                f'<h2 id="figuras">Figuras da avaliação científica</h2><div class="figuras">{figs}</div>'
            )
            sumario.append(("figuras", "Figuras da avaliação científica"))
    if not secoes:
        corpo = "<p>Os documentos de metodologia não estão disponíveis nesta instalação.</p>"
    else:
        corpo = "\n".join(secoes)
    toc = "".join(f'<li><a href="#{i}">{n}</a></li>' for i, n in sumario)
    return (
        '<div class="conteiner">'
        '<div class="pagina-titulo"><h1>Metodologia</h1>'
        "<p>Como os dados foram obtidos e validados, como o modelo foi escolhido e avaliado e quais "
        "são os limites das conclusões. Conteúdo gerado dos documentos versionados do projeto.</p></div>"
        '<div class="metodologia">'
        f'<nav class="sumario" aria-label="Nesta página"><ul>{toc}</ul></nav>'
        f'<article class="prosa">{corpo}</article>'
        "</div></div>"
    )


class Paginas:
    def __init__(self, raiz: Path) -> None:
        raiz = Path(raiz)
        base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
        figuras = {
            n for n in FIGURAS if (raiz / "data" / "predictions" / "cientifica" / n).is_file()
        }
        self.figuras = figuras
        self.html: dict[str, str] = {}
        for nome, (titulo, descricao) in PAGINAS.items():
            if nome == "metodologia":
                conteudo = montar_metodologia(raiz / "docs", figuras)
            else:
                conteudo = (TEMPLATES / f"{nome}.html").read_text(encoding="utf-8")
            pagina = base
            for chave, valor in (
                ("titulo", titulo),
                ("descricao", descricao),
                ("conteudo", conteudo),
                ("script", nome if nome != "metodologia" else "comum_pagina"),
            ):
                pagina = pagina.replace("{{" + chave + "}}", valor)
            for outro in PAGINAS:
                marca = ' aria-current="page"' if outro == nome else ""
                pagina = pagina.replace("{{ativa_" + outro + "}}", marca)
            self.html[nome] = pagina
