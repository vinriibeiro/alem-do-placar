"""Obtém as URLs dos escudos dos clubes na Wikipédia (imagem principal do artigo) e grava
config/escudos.csv. Executar só quando entrar um clube novo; o CSV é versionado e revisado.

Uso: python scripts/obter_escudos.py

Os escudos são marcas registradas dos clubes. O projeto apenas aponta para as imagens hospedadas
pela Wikimedia, para identificação visual, sem fins comerciais e sem redistribuir os arquivos.
"""

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "config" / "escudos.csv"
API = "https://pt.wikipedia.org/w/api.php"
AGENTE = "AlemDoPlacar/0.1 (projeto de portfolio; github.com/vinriibeiro)"
TAMANHO = 96

ARTIGOS = {
    "América Mineiro": "América Futebol Clube (Minas Gerais)",
    "Athletico Paranaense": "Club Athletico Paranaense",
    "Atlético Goianiense": "Atlético Clube Goianiense",
    "Atlético Mineiro": "Clube Atlético Mineiro",
    "Avaí SC": "Avaí Futebol Clube",
    "Botafogo FR": "Botafogo de Futebol e Regatas",
    "CR Vasco da Gama": "Club de Regatas Vasco da Gama",
    "CSA AL": "Centro Sportivo Alagoano",
    "Ceará SC": "Ceará Sporting Club",
    "Chapecoense": "Associação Chapecoense de Futebol",
    "Coritiba FBC": "Coritiba Foot Ball Club",
    "Criciúma EC": "Criciúma Esporte Clube",
    "Cruzeiro EC": "Cruzeiro Esporte Clube",
    "Cuiabá EC": "Cuiabá Esporte Clube",
    "EC Bahia": "Esporte Clube Bahia",
    "EC Juventude": "Esporte Clube Juventude",
    "EC Vitória": "Esporte Clube Vitória",
    "Flamengo": "Clube de Regatas do Flamengo",
    "Fluminense FC": "Fluminense Football Club",
    "Fortaleza EC": "Fortaleza Esporte Clube",
    "Goiás EC": "Goiás Esporte Clube",
    "Grêmio": "Grêmio Foot-Ball Porto Alegrense",
    "Mirassol FC": "Mirassol Futebol Clube",
    "Paraná Clube": "Paraná Clube",
    "RB Bragantino": "Red Bull Bragantino",
    "SC Corinthians Paulista": "Sport Club Corinthians Paulista",
    "SC Internacional": "Sport Club Internacional",
    "SC Recife": "Sport Club do Recife",
    "SE Palmeiras": "Sociedade Esportiva Palmeiras",
    "Santos FC": "Santos Futebol Clube",
    "São Paulo FC": "São Paulo Futebol Clube",
}


def consultar(titulos: list[str]) -> dict:
    params = {
        "action": "query",
        "format": "json",
        "redirects": "1",
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": str(TAMANHO),
        "titles": "|".join(titulos),
    }
    req = urllib.request.Request(
        f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": AGENTE}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))["query"]


def main() -> int:
    q = consultar(list(ARTIGOS.values()))
    destino = {t: t for t in ARTIGOS.values()}
    for passo in q.get("normalized", []) + q.get("redirects", []):
        for origem, alvo in destino.items():
            if alvo == passo["from"]:
                destino[origem] = passo["to"]
    por_titulo = {p["title"]: p for p in q["pages"].values()}
    linhas, faltas = [], []
    for equipe, artigo in ARTIGOS.items():
        pagina = por_titulo.get(destino[artigo], {})
        url = pagina.get("thumbnail", {}).get("source", "").split("?")[0]
        if not url:
            faltas.append(equipe)
        linhas.append({"equipe": equipe, "artigo": destino[artigo], "escudo_url": url})
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["equipe", "artigo", "escudo_url"])
        w.writeheader()
        w.writerows(linhas)
    for linha in linhas:
        print(f"{linha['equipe']:<25} {linha['escudo_url'].rsplit('/', 1)[-1] or 'SEM IMAGEM'}")
    if faltas:
        print("Sem imagem:", ", ".join(faltas))
    return 1 if faltas else 0


if __name__ == "__main__":
    sys.exit(main())
