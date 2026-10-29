"""Gera o site estático (início, dashboard, Central de Consulta e metodologia) em ``site/``.

Uso:
    python scripts/build_site.py [--saida site] [--powerbi-url URL] [--repo-url URL]

O resultado é só HTML, CSS, JavaScript e JSON: pode ser publicado no GitHub Pages ou no
Cloudflare Pages sem servidor e sem custo. Nada é publicado automaticamente.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from api import central  # noqa: E402
from api.paginas import FIGURAS, Paginas  # noqa: E402

ESTATICO = RAIZ / "src" / "api" / "static"
HOSTS_EMBED = ("https://app.powerbi.com/", "https://app.fabric.microsoft.com/")
# GitHub Pages não envia cabeçalhos de segurança: a política vai em uma meta tag.
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data: https://upload.wikimedia.org "
    "https://thumb.wikimedia.org; connect-src 'self'; "
    "frame-src https://app.powerbi.com https://app.fabric.microsoft.com; object-src 'none'; "
    "base-uri 'none'; form-action 'self'"
)
ARQUIVOS = {
    "inicio": "index.html",
    "dashboard": "dashboard.html",
    "consulta": "consulta.html",
    "metodologia": "metodologia.html",
}


def construir(saida: Path, powerbi_url: str = "", repo_url: str = "") -> Path:
    if powerbi_url and not powerbi_url.startswith(HOSTS_EMBED):
        raise SystemExit(
            "--powerbi-url deve ser um endereço de inserção do Power BI (app.powerbi.com)."
        )
    if repo_url and not repo_url.startswith("https://"):
        raise SystemExit("--repo-url deve começar com https://")
    if saida.exists():
        if not (saida / "index.html").is_file():
            raise SystemExit(f"Recusado: {saida} existe e não parece um site gerado.")
        shutil.rmtree(saida)
    saida.mkdir(parents=True)
    paginas = Paginas(RAIZ)
    meta_csp = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
    for nome, arquivo in ARQUIVOS.items():
        html = paginas.html[nome].replace(
            '<meta charset="utf-8">\n', '<meta charset="utf-8">\n' + meta_csp, 1
        )
        (saida / arquivo).write_text(html, encoding="utf-8")
    (saida / "404.html").write_text(paginas.html["inicio"], encoding="utf-8")
    shutil.copytree(ESTATICO, saida / "static", ignore=shutil.ignore_patterns("__pycache__"))
    figuras = saida / "figuras"
    figuras.mkdir()
    for nome in FIGURAS:
        origem = RAIZ / "data" / "predictions" / "cientifica" / nome
        if origem.is_file():
            shutil.copy2(origem, figuras / nome)
    dados = saida / "dados"
    dados.mkdir()
    config = {"powerbi_embed_url": powerbi_url, "repo_url": repo_url, "versao": "0.1.0"}
    for nome, valor in central.montar(RAIZ, config).items():
        (dados / f"{nome}.json").write_text(
            json.dumps(valor, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
    (saida / ".nojekyll").write_text("", encoding="utf-8")
    return saida


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--saida", type=Path, default=RAIZ / "site")
    ap.add_argument("--powerbi-url", default="")
    ap.add_argument("--repo-url", default="")
    args = ap.parse_args(argv)
    destino = construir(args.saida, args.powerbi_url.strip(), args.repo_url.strip())
    total = sum(f.stat().st_size for f in destino.rglob("*") if f.is_file())
    print(f"{destino} ({total / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
