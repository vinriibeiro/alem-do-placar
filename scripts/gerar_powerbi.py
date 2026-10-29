"""Regenera o projeto Power BI versionado em dashboard/powerbi/AlemDoPlacar.

Exemplos:
    python scripts/gerar_powerbi.py
    python scripts/gerar_powerbi.py --fonte web \
        --url-base https://raw.githubusercontent.com/USUARIO/alem-do-placar/main/data \
        --url-assistente https://SEU-SITE/assistente

A pasta de saída é recriada. Só é apagada se já contiver AlemDoPlacar.pbip (projeto gerado antes).
"""

import argparse
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from evaluation.powerbi import URL_ASSISTENTE, gerar_projeto  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--fonte", choices=("local", "web"), default="local")
    ap.add_argument("--url-base", help="URL https da pasta data/ (exigida com --fonte web)")
    ap.add_argument("--url-assistente", default=URL_ASSISTENTE)
    args = ap.parse_args(argv)

    saida = RAIZ / "dashboard" / "powerbi" / "AlemDoPlacar"
    if saida.exists():
        if not (saida / "AlemDoPlacar.pbip").is_file():
            sys.exit(f"Recusado: {saida} existe e não parece um projeto gerado.")
        shutil.rmtree(saida)
    pbip = gerar_projeto(
        saida,
        RAIZ / "data" / "processed",
        RAIZ / "data" / "predictions" / "modelagem",
        RAIZ / "data" / "predictions" / "cientifica",
        RAIZ / "dashboard" / "powerbi" / "template",
        fonte_dados=args.fonte,
        url_base_dados=args.url_base,
        url_assistente=args.url_assistente,
        tokens=RAIZ / "dashboard" / "assets" / "tema_tokens.json",
    )
    print(pbip)


if __name__ == "__main__":
    main()
