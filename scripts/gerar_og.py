"""Gera a imagem Open Graph (1200x630) e o JSON de tokens de design a partir de tokens.css.

Uso: python scripts/gerar_og.py
Saídas: src/api/static/img/og.png e dashboard/assets/tema_tokens.json
"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
TOKENS = RAIZ / "src" / "api" / "static" / "css" / "tokens.css"


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


def gerar_og(t: dict[str, str]) -> Path:
    saida = RAIZ / "src" / "api" / "static" / "img" / "og.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=t["cor-primaria"])
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 630)
    ax.axis("off")
    ax.plot([600, 600], [0, 630], color="white", alpha=0.07, lw=3)
    ax.add_patch(Circle((600, 315), 150, fill=False, ec="white", alpha=0.07, lw=3))
    ax.add_patch(Circle((1010, 470), 220, color=t["cor-destaque"], alpha=0.35))
    ax.text(80, 420, "BRASILEIRÃO SÉRIE A · 2018–2025", color="#f3c84b", fontsize=17, weight="bold")
    ax.text(80, 320, "Além do Placar", color="white", fontsize=64, weight="bold")
    ax.text(
        80,
        235,
        "Dados, estatística e IA para entender\no que faz um time evoluir, cair ou surpreender.",
        color="#d6e2f0",
        fontsize=24,
        linespacing=1.5,
    )
    ax.text(
        80,
        80,
        "Dashboard · Assistente em português · Metodologia aberta",
        color="white",
        fontsize=18,
    )
    fig.savefig(saida, facecolor=fig.get_facecolor())
    plt.close(fig)
    return saida


if __name__ == "__main__":
    tokens = ler_tokens()
    print(gerar_json(tokens))
    print(gerar_og(tokens))
