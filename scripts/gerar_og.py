"""Gera a imagem Open Graph (1200x630) e o JSON de tokens de design a partir de tokens.css.

Uso: python scripts/gerar_og.py
Saídas: src/api/static/img/og.png e dashboard/assets/tema_tokens.json

A logo do Brasileirão vem de src/api/static/img/brasileirao-branco.svg e é desenhada em branco
com a biblioteca opcional ``svgpath2mpl`` (pip install svgpath2mpl). Sem ela, a imagem sai sem a logo.
"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, PathPatch  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
TOKENS = RAIZ / "src" / "api" / "static" / "css" / "tokens.css"
LOGO = RAIZ / "src" / "api" / "static" / "img" / "brasileirao-branco.svg"


def ler_tokens() -> dict[str, str]:
    texto = TOKENS.read_text(encoding="utf-8")
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", texto))


def gerar_json(t: dict[str, str]) -> Path:
    saida = RAIZ / "dashboard" / "assets" / "tema_tokens.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "fonte": "src/api/static/css/tokens.css",
        "cores": t,
        "serie": [t[f"serie-{i}"] for i in range(1, 7)],
        "tipografia": {"familia": "Inter", "alternativa": "Segoe UI"},
    }
    saida.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return saida


def _logo(ax, x: float, y_base: float, altura: float) -> None:
    """Desenha a logo branca com a base em ``y_base`` e a altura dada (eixo em pixels)."""
    try:
        from svgpath2mpl import parse_path
    except ImportError:
        return
    d = re.search(r'<path d="([^"]+)"', LOGO.read_text(encoding="utf-8")).group(1)
    caminho = parse_path(d)
    vb_x, vb_y, vb_a = 100, 60, 1090
    escala = altura / vb_a
    # O SVG tem o eixo y para baixo; o eixo do gráfico tem y para cima.
    transf = Affine2D().translate(-vb_x, -(vb_y + vb_a)).scale(escala, -escala).translate(x, y_base)
    ax.add_patch(
        PathPatch(caminho, transform=transf + ax.transData, fc="white", ec="none", zorder=5)
    )


def gerar_og(t: dict[str, str]) -> Path:
    saida = RAIZ / "src" / "api" / "static" / "img" / "og.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=t["cor-primaria"])
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 630)
    ax.axis("off")
    ax.plot([600, 600], [0, 630], color="white", alpha=0.06, lw=3)
    ax.add_patch(Circle((600, 315), 150, fill=False, ec="white", alpha=0.06, lw=3))
    ax.add_patch(Circle((1010, 470), 240, color=t["cor-destaque"], alpha=0.30))
    ax.add_patch(plt.Rectangle((0, 0), 1200, 12, color="#f3c84b"))
    _logo(ax, 790, 70, 440)
    ax.text(80, 470, "BRASILEIRÃO SÉRIE A · 2018–2025", color="#f3c84b", fontsize=17, weight="bold")
    ax.text(80, 385, "Além do Placar", color="white", fontsize=52, weight="bold")
    ax.text(
        80,
        345,
        "Dados, estatística e Machine Learning para\nentender o que faz um time evoluir,\ncair ou surpreender.",
        color="#d5ebe1",
        fontsize=21,
        linespacing=1.5,
        va="top",
    )
    ax.text(
        80, 60, "Dashboard · Central de Consulta · Metodologia aberta", color="white", fontsize=17
    )
    fig.savefig(saida, facecolor=fig.get_facecolor())
    plt.close(fig)
    return saida


if __name__ == "__main__":
    tokens = ler_tokens()
    print(gerar_json(tokens))
    print(gerar_og(tokens))
