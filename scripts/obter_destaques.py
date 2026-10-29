"""Coleta os destaques individuais de cada temporada na Wikipédia e grava config/destaques.csv.

Fonte: a caixa de informações do artigo "Campeonato Brasileiro de Futebol de {ano} - Série A"
na Wikipédia em português (artilheiro com gols, Craque e Melhor Goleiro do Prêmio Brasileirão).
A foto vem da imagem principal do artigo do próprio jogador, o que garante a identidade, e só é
aceita se a licença na Wikimedia Commons for livre (Creative Commons ou domínio público).

Uso: python scripts/obter_destaques.py   (revise o CSV antes de commitar)
"""

import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "config" / "destaques.csv"
API = "https://pt.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
AGENTE = "AlemDoPlacar/0.1 (projeto de portfolio; github.com/vinriibeiro)"
ANOS = range(2018, 2026)
CAMPOS = {
    "artilheiro": r"artilheiros?",
    "craque": r"melhor_?\s?jogador",
    "goleiro": r"melhor_?\s?goleiro",
}
LIVRES = re.compile(r"^(cc[- ]|public domain|pd|domínio público|cc0|attribution)", re.I)
# Nomes de predefinições {{Futebol X}} que não batem diretamente com o nome padronizado.
CLUBES_MANUAL = {
    "atlético mineiro": "Atlético Mineiro",
    "atlético-mg": "Atlético Mineiro",
    "athletico paranaense": "Athletico Paranaense",
    "atlético-pr": "Athletico Paranaense",
    "atlético goianiense": "Atlético Goianiense",
    "bragantino": "RB Bragantino",
    "red bull bragantino": "RB Bragantino",
    "sport": "SC Recife",
    "são paulo": "São Paulo FC",
    "américa mineiro": "América Mineiro",
    "américa-mg": "América Mineiro",
    "internacional-rs": "SC Internacional",
    "internacional": "SC Internacional",
    "vitória": "EC Vitória",
    "corinthians": "SC Corinthians Paulista",
    "palmeiras": "SE Palmeiras",
    "botafogo": "Botafogo FR",
    "fluminense": "Fluminense FC",
}


def _get(url: str, params: dict) -> dict:
    """GET com pausa de cortesia e novas tentativas quando a Wikimedia limita o ritmo (429)."""
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": AGENTE}
    )
    for tentativa in range(5):
        time.sleep(1.0)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            if erro.code != 429 or tentativa == 4:
                raise
            time.sleep(5 * (tentativa + 1))
    raise RuntimeError("inalcançável")


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


def _clube(nome_predef: str, equipes: list[str]) -> str:
    chave = nome_predef.strip().lower()
    if chave in CLUBES_MANUAL:
        return CLUBES_MANUAL[chave]
    alvo = _norm(nome_predef)
    candidatos = [e for e in equipes if alvo in _norm(e) or _norm(e) in alvo]
    return candidatos[0] if len(candidatos) == 1 else ""


def _infobox(ano: int) -> tuple[str, str]:
    titulo = f"Campeonato Brasileiro de Futebol de {ano} - Série A"
    d = _get(
        API,
        {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
            "titles": titulo,
        },
    )
    pagina = d["query"]["pages"][0]
    texto = pagina["revisions"][0]["slots"]["main"]["content"]
    return pagina["title"], texto


def _valor(texto: str, padrao: str) -> str:
    """Valor do campo, incluindo linhas de continuação (empates listados com '*')."""
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        m = re.match(rf"^\s*\|\s*{padrao}\s*=\s*(.*)$", linha, re.I)
        if not m:
            continue
        partes = [m.group(1)]
        for seguinte in linhas[i + 1 :]:
            if seguinte.lstrip().startswith(("|", "}}")):
                break
            partes.append(seguinte)
        return " ".join(partes)
    return ""


def _jogadores(valor: str) -> list[tuple[str, str]]:
    """[(artigo, nome exibido, predefinição do clube)] na ordem em que aparecem."""
    padrao = r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]\s*\(\s*\{\{\s*Futebol\s+([^}|]+)"
    return [(a.strip(), (r or "").strip(), c.strip()) for a, r, c in re.findall(padrao, valor)]


def _foto(artigo: str) -> dict:
    d = _get(
        API,
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "redirects": "1",
            "prop": "pageimages",
            "piprop": "thumbnail|name",
            "pithumbsize": "160",
            "titles": artigo,
        },
    )
    pagina = d["query"]["pages"][0]
    arquivo = pagina.get("pageimage")
    miniatura = pagina.get("thumbnail", {}).get("source", "").split("?")[0]
    if not arquivo or not miniatura:
        return {"artigo": pagina.get("title", artigo)}
    info = _get(
        COMMONS,
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "extmetadata",
            "titles": f"File:{arquivo}",
        },
    )
    paginas = info["query"]["pages"]
    meta = (paginas[0].get("imageinfo") or [{}])[0].get("extmetadata", {}) if paginas else {}
    licenca = meta.get("LicenseShortName", {}).get("value", "")
    autor = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
    livre = bool(LIVRES.match(licenca))
    return {
        "artigo": pagina.get("title", artigo),
        "foto_url": miniatura if livre else "",
        "foto_licenca": licenca,
        "foto_autor": autor[:120],
        "foto_arquivo": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(arquivo)}"
        if livre
        else "",
    }


def main() -> int:
    equipes = sorted(
        pd.read_parquet(RAIZ / "data" / "processed" / "dim_equipes.parquet")["nome_padronizado"]
    )
    linhas, alertas = [], []
    for ano in ANOS:
        titulo, texto = _infobox(ano)
        fonte = "https://pt.wikipedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_"))
        for categoria, padrao in CAMPOS.items():
            valor = _valor(texto, padrao)
            jogadores = _jogadores(valor)
            if not jogadores:
                alertas.append(f"{ano} {categoria}: não encontrado")
                continue
            gols = re.search(r"(\d+)\s*gols", valor)
            for ordem, (artigo, rotulo, predef) in enumerate(jogadores, start=1):
                clube = _clube(predef, equipes)
                if not clube:
                    alertas.append(f"{ano} {categoria}: clube não mapeado '{predef}'")
                foto = _foto(artigo)
                if not foto.get("foto_url"):
                    alertas.append(f"{ano} {categoria}: sem foto livre para {artigo}")
                linhas.append(
                    {
                        "ano": ano,
                        "categoria": categoria,
                        "ordem": ordem,
                        "jogador": rotulo or re.sub(r"\s*\(.*\)$", "", artigo),
                        "artigo": foto["artigo"],
                        "clube": clube,
                        "gols": gols.group(1) if (categoria == "artilheiro" and gols) else "",
                        "foto_url": foto.get("foto_url", ""),
                        "foto_licenca": foto.get("foto_licenca", ""),
                        "foto_autor": foto.get("foto_autor", ""),
                        "foto_arquivo": foto.get("foto_arquivo", ""),
                        "fonte": fonte,
                    }
                )
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    for linha in linhas:
        print(
            f"{linha['ano']} {linha['categoria']:<10} {linha['jogador']:<28} {linha['clube']:<22} "
            f"{linha['gols']:>3} {'foto' if linha['foto_url'] else '-'} {linha['foto_licenca']}"
        )
    for a in alertas:
        print("ALERTA:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
