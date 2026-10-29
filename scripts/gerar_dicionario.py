"""Gera docs/dicionario_de_dados.md a partir das fontes do projeto (nomes, esquemas e medidas).

Uso: python scripts/gerar_dicionario.py
"""

import sys
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from evaluation.nomes import ALVO, ATRIBUTOS, METRICAS  # noqa: E402
from evaluation.powerbi import MEDIDAS_DAX  # noqa: E402
from evaluation.powerbi_layout import ROTULOS  # noqa: E402

SAIDA = RAIZ / "docs" / "dicionario_de_dados.md"

COLUNAS = {
    "dim_equipes": {
        "equipe_id": ("Identificador da equipe", "Hash estável do nome padronizado."),
        "nome": ("Nome", "Nome da equipe após a padronização."),
        "nome_padronizado": ("Equipe", "Nome único do clube usado em todo o projeto."),
    },
    "dim_temporadas": {
        "temporada_id": ("Identificador da temporada", "Hash estável do ano e da competição."),
        "ano": ("Temporada", "Ano da temporada."),
        "competicao": ("Competição", "Brasileiro Série A."),
    },
    "fato_partidas": {
        "partida_id": (
            "Identificador da partida",
            "SHA-256 de temporada, data, mandante e visitante.",
        ),
        "data_partida": ("Data", "Data da partida."),
        "temporada_id": ("Temporada", "Chave para dim_temporadas."),
        "equipe_mandante_id": ("Mandante", "Chave da equipe que jogou em casa."),
        "equipe_visitante_id": ("Visitante", "Chave da equipe visitante."),
        "gols_mandante": ("Gols do mandante", "Placar final do mandante."),
        "gols_visitante": ("Gols do visitante", "Placar final do visitante."),
        "resultado": ("Resultado", "H (mandante venceu), D (empate) ou A (visitante venceu)."),
    },
    "fato_desempenho_equipes": {
        "partida_id": ("Identificador da partida", "Chave para fato_partidas."),
        "equipe_id": ("Equipe", "Chave para dim_equipes."),
        "pontos": ("Pontos no jogo", "3 vitória, 1 empate, 0 derrota."),
        "gols_pro": ("Gols marcados", "Gols da equipe na partida."),
        "gols_contra": ("Gols sofridos", "Gols do adversário na partida."),
        "saldo_gols": ("Saldo de gols", "gols_pro − gols_contra."),
        "mando_campo": ("Mando", "mandante ou visitante."),
        "rodada": ("Rodada", "Rodada da partida na temporada."),
    },
}
ORIGEM_COLUNAS = "OpenFootball (CC0), padronizado em src/processing"
DESCRICAO_MEDIDAS = {
    "Partidas": "Quantidade de partidas distintas no filtro.",
    "Pontos totais": "Soma dos pontos das equipes no filtro.",
    "Pontos por jogo": "Pontos ÷ jogos disputados.",
    "Aproveitamento": "Pontos ÷ (3 × jogos).",
    "Vitórias do mandante": "Vitórias em casa ÷ jogos em casa.",
    "Posição": "Posição na temporada: pontos, vitórias, saldo e gols marcados; vazio sem uma única temporada.",
    "Zona": "Faixa da tabela pela posição (1–4, 5–6, 7–12, 17–20).",
    "Pontos (temporada)": "Pontos, só quando há uma única temporada no filtro.",
    "Média do campeonato": "Pontos por jogo de todas as equipes no filtro de temporada.",
    "% dos resultados": "Participação de cada resultado (Derrota, Empate, Vitória) no total.",
    "Volatilidade de pontos": "Desvio-padrão populacional dos pontos por jogo.",
    "Média prevista": "Média das previsões do modelo no filtro.",
    "Média observada": "Média do alvo real nas mesmas datas das previsões.",
    "Erro absoluto médio": "Média de |previsto − real| no filtro.",
    "MAE global selecionado": "MAE do modelo selecionado no teste de 2025, todas as equipes.",
    "MAE global baseline": "MAE da média dos últimos 5 jogos no teste de 2025.",
    "Importância": "Aumento médio do MAE ao embaralhar a variável no teste (permutação).",
}


def _tabela(linhas: list[list[str]], cabecalho: list[str]) -> str:
    texto = "| " + " | ".join(cabecalho) + " |\n|" + "---|" * len(cabecalho) + "\n"
    for linha in linhas:
        texto += "| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in linha) + " |\n"
    return texto


def main() -> None:
    partes = [
        "# Dicionário de dados\n",
        "Gerado por `scripts/gerar_dicionario.py` a partir de `src/evaluation/nomes.py`, dos esquemas "
        "Parquet e das medidas do gerador do Power BI. Para regras de cálculo detalhadas dos atributos, "
        "veja também `docs/data_dictionary.md`.\n",
        "## 1. Tabelas de dados\n",
    ]
    for tabela, colunas in COLUNAS.items():
        esquema = {
            c.name: str(c.type)
            for c in pq.read_schema(RAIZ / "data" / "processed" / f"{tabela}.parquet")
        }
        linhas = [
            [f"`{c}`", amigavel, esquema.get(c, "—"), desc, "—", ORIGEM_COLUNAS]
            for c, (amigavel, desc) in colunas.items()
        ]
        partes.append(
            f"### {tabela}\n\n"
            + _tabela(
                linhas, ["Nome original", "Nome amigável", "Tipo", "Descrição", "Fórmula", "Origem"]
            )
        )
    partes.append(
        "## 2. Atributos do modelo\n\nTodos calculados por equipe e temporada, em ordem cronológica, incluindo o jogo de referência.\n"
    )
    linhas = [
        [
            f"`{c}`",
            amigavel,
            "inteiro" if c in {"jogos_acumulados", "mando"} else "decimal",
            desc,
            desc.split(":")[0],
            "src/features/temporais.py",
        ]
        for c, (amigavel, desc) in ATRIBUTOS.items()
    ]
    partes.append(
        _tabela(
            linhas, ["Nome original", "Nome amigável", "Tipo", "Descrição", "Fórmula", "Origem"]
        )
    )
    partes.append(
        "## 3. Alvo\n\n"
        + _tabela(
            [
                [
                    "`media_pontos_futuros_5`",
                    ALVO[0],
                    "decimal (0 a 3)",
                    ALVO[1],
                    "soma dos pontos dos 5 jogos seguintes ÷ 5",
                    "src/features/temporais.py",
                ]
            ],
            ["Nome original", "Nome amigável", "Tipo", "Descrição", "Fórmula", "Origem"],
        )
    )
    partes.append(
        "## 4. Indicadores do dashboard (medidas DAX)\n\nNomes exibidos no relatório entre parênteses quando diferentes.\n"
    )
    linhas = []
    for nome, dax, formato in MEDIDAS_DAX:
        exibido = ROTULOS.get(nome, nome)
        linhas.append(
            [
                f"`{nome}`",
                exibido,
                formato or "texto",
                DESCRICAO_MEDIDAS.get(nome, ""),
                f"`{dax}`",
                "src/evaluation/powerbi.py",
            ]
        )
    partes.append(
        _tabela(
            linhas,
            ["Nome original", "Nome amigável", "Formato", "Descrição", "Fórmula DAX", "Origem"],
        )
    )
    partes.append(
        "## 5. Métricas de avaliação\n\n"
        + _tabela(
            [
                [
                    f"`{c}`",
                    amigavel,
                    "decimal",
                    desc,
                    {
                        "mae": "média de |previsto − real|",
                        "rmse": "raiz da média de (previsto − real)²",
                        "vies": "média de (previsto − real)",
                    }[c],
                    "src/models/backtesting.py",
                ]
                for c, (amigavel, desc) in METRICAS.items()
            ],
            ["Nome original", "Nome amigável", "Tipo", "Descrição", "Fórmula", "Origem"],
        )
    )
    partes.append(
        "## 6. Destaques individuais (`config/destaques.csv`)\n\n"
        + _tabela(
            [
                [
                    "`categoria`",
                    "Destaque",
                    "texto",
                    "artilheiro, craque (Prêmio Brasileirão) ou goleiro (Prêmio Brasileirão).",
                    "—",
                    "Wikipédia (pt), caixa de informações da temporada",
                ],
                [
                    "`gols`",
                    "Gols",
                    "inteiro",
                    "Gols do artilheiro na temporada.",
                    "—",
                    "Wikipédia (pt)",
                ],
                [
                    "`foto_url`",
                    "Foto",
                    "URL",
                    "Imagem principal do artigo do jogador, só com licença livre.",
                    "—",
                    "Wikimedia Commons",
                ],
                [
                    "`foto_licenca`, `foto_autor`",
                    "Crédito",
                    "texto",
                    "Licença e autor da foto, exibidos no crédito.",
                    "—",
                    "Wikimedia Commons",
                ],
            ],
            ["Nome original", "Nome amigável", "Tipo", "Descrição", "Fórmula", "Origem"],
        )
    )
    SAIDA.write_text("\n".join(partes), encoding="utf-8")
    print(SAIDA)


if __name__ == "__main__":
    main()
