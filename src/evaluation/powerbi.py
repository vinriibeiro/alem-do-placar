"""Gerador do projeto Power BI local (PBIP/PBIR) do Além do Placar (T008).

Copia o scaffold oficial do template, substitui as páginas e gera o modelo semântico (TMSL em
model.bim) com partições M que leem somente arquivos locais. Não executa CLI, não acessa rede e
não altera as pastas de entrada.
"""

import csv
import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

NOME = "AlemDoPlacar"
COR_TEXTO = "#17364D"
COR_DESTAQUE = "#188A8A"
URL_ASSISTENTE = "http://127.0.0.1:8765"
MODELO_BASELINE = "M00_media_recente_5"
FATO = "fato_desempenho_equipes"
SCHEMA_PAGINA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
SCHEMA_PAGINAS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"
ARQUIVOS_TEMPLATE = (
    "AlemDoPlacar.pbip",
    "AlemDoPlacar.Report/definition.pbir",
    "AlemDoPlacar.Report/definition/version.json",
    "AlemDoPlacar.Report/definition/report.json",
)
CHAVES_METADADOS = ("modelo_selecionado", "corte_treino", "versao")
COLUNAS_METRICAS = {
    "fase": "string",
    "modelo": "string",
    "temporada": "string",
    "mae": "double",
    "rmse": "double",
    "vies": "double",
    "n": "int64",
}
COLUNAS_IMPORTANCIAS = {
    "atributo": "string",
    "delta_mae_media": "double",
    "delta_mae_desvio": "double",
}
TIPO_M = {"string": "text", "double": "number", "int64": "Int64.Type"}

# Relacionamentos 1:N unidirecionais: (tabela muitos, coluna, tabela um, coluna).
RELACIONAMENTOS = [
    (FATO, "equipe_id", "dim_equipes", "equipe_id"),
    ("fato_partidas", "temporada_id", "dim_temporadas", "temporada_id"),
    (FATO, "partida_id", "fato_partidas", "partida_id"),
    ("analitico", "equipe", "dim_equipes", "nome_padronizado"),
    ("previsoes", "equipe", "dim_equipes", "nome_padronizado"),
    ("analitico", "temporada", "dim_temporadas", "ano"),
    ("previsoes", "temporada", "dim_temporadas", "ano"),
]

MEDIDAS_DAX = [
    ("Partidas", f"DISTINCTCOUNT({FATO}[partida_id])"),
    ("Observações de equipe", f"COUNTROWS({FATO})"),
    ("Gols", f"SUM({FATO}[gols_pro])"),
    ("Pontos totais", f"SUM({FATO}[pontos])"),
    ("Gols por jogo", "DIVIDE([Gols],[Partidas])"),
    ("Média prevista", "AVERAGE(previsoes[previsao])"),
    ("Média observada", "AVERAGE(previsoes[alvo])"),
    ("Média recente", "AVERAGE(analitico[media_pontos_5])"),
    ("Importância", "AVERAGE(importancias[delta_mae_media])"),
    (
        "MAE global selecionado",
        "VAR ModeloAtual = [Modelo selecionado] RETURN "
        'CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",'
        'metricas[modelo]=ModeloAtual,metricas[temporada]="todas")',
    ),
    (
        "MAE global baseline",
        f'CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",metricas[modelo]="{MODELO_BASELINE}",metricas[temporada]="todas")',
    ),
]


class ErroProjeto(ValueError):
    """Entrada ausente ou inválida, ou saída já ocupada."""


def gerar_projeto(
    pasta_saida: Path,
    pasta_processados: Path,
    pasta_modelagem: Path,
    pasta_cientifica: Path,
    template_dir: Path,
) -> Path:
    """Gera o projeto PBIP em ``pasta_saida`` e devolve o caminho do ``.pbip``.

    As pastas de entrada são somente lidas. ``pasta_saida`` deve estar ausente ou vazia.
    """
    saida_resolvida = pasta_saida.resolve()
    for entrada in (pasta_processados, pasta_modelagem, pasta_cientifica, template_dir):
        origem_resolvida = entrada.resolve()
        if saida_resolvida == origem_resolvida or origem_resolvida in saida_resolvida.parents:
            raise ErroProjeto("saída não pode estar dentro de uma pasta de entrada")
    _validar_template(template_dir)
    _validar_saida(pasta_saida)
    meta = _ler_metadados(pasta_modelagem / "metadados.json")
    tabelas = [
        _tabela_parquet(nome, pasta_processados / f"{nome}.parquet")
        for nome in ("dim_equipes", "dim_temporadas", "fato_partidas")
    ]
    tabelas.append(_tabela_parquet(FATO, pasta_processados / f"{FATO}.parquet", _medidas(meta)))
    tabelas += [
        _tabela_parquet("analitico", pasta_processados / "dataset_analitico.parquet"),
        _tabela_parquet("previsoes", pasta_modelagem / "previsoes.parquet"),
        _tabela_registros(
            "metricas", _linhas_metricas(pasta_modelagem / "metricas.json"), COLUNAS_METRICAS
        ),
        _tabela_registros(
            "importancias",
            _linhas_importancias(pasta_cientifica / "importancias.csv"),
            COLUNAS_IMPORTANCIAS,
        ),
    ]
    modelo = {
        "name": NOME,
        "compatibilityLevel": 1600,
        "model": {
            "culture": "pt-BR",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "tables": tabelas,
            "relationships": [_relacionamento(*r) for r in RELACIONAMENTOS],
        },
    }
    paginas = _paginas(meta)
    _validar_referencias(tabelas, paginas)
    shutil.copytree(template_dir, pasta_saida, dirs_exist_ok=True)
    _escrever_modelo(pasta_saida, modelo)
    _escrever_relatorio(pasta_saida, paginas)
    return pasta_saida / f"{NOME}.pbip"


# --- Entradas e validações -------------------------------------------------------------------


def _arquivo(caminho: Path) -> Path:
    if not caminho.is_file():
        raise ErroProjeto(f"arquivo obrigatório ausente: {caminho}")
    return caminho


def _ler_json(caminho: Path) -> Any:
    try:
        return json.loads(_arquivo(caminho).read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroProjeto(f"JSON inválido em {caminho}: {erro}") from erro


def _gravar_json(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validar_template(template: Path) -> None:
    for relativo in ARQUIVOS_TEMPLATE:
        _arquivo(template / relativo)
    temas = template / "AlemDoPlacar.Report/StaticResources/SharedResources/BaseThemes"
    if not any(temas.glob("*.json")):
        raise ErroProjeto("tema oficial ausente no template")


def _validar_saida(pasta: Path) -> None:
    if pasta.exists() and (not pasta.is_dir() or any(pasta.iterdir())):
        raise ErroProjeto(f"pasta de saída já contém arquivos; não será sobrescrita: {pasta}")


def _ler_metadados(caminho: Path) -> dict[str, str]:
    dados = _ler_json(caminho)
    if not isinstance(dados, dict):
        raise ErroProjeto(f"metadados.json deve conter um objeto: {caminho}")
    for chave in CHAVES_METADADOS:
        if chave not in dados:
            raise ErroProjeto(f"campo ausente em metadados.json: {chave}")
    return {
        **{chave: str(dados[chave]) for chave in CHAVES_METADADOS},
        "notas": str(dados.get("notas", dados.get("motivo_selecao", "Avaliação histórica local."))),
    }


def _numero(valor: object, origem: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as erro:
        raise ErroProjeto(f"valor numérico inválido em {origem}: {valor!r}") from erro
    if not math.isfinite(numero):
        raise ErroProjeto(f"valor não finito em {origem}: {valor!r}")
    return numero


def _linhas_metricas(caminho: Path) -> list[dict[str, Any]]:
    dados = _ler_json(caminho)
    if not isinstance(dados, list):
        raise ErroProjeto(f"metricas.json deve conter uma lista de registros: {caminho}")
    linhas = []
    for registro in dados:
        try:
            linhas.append(
                {
                    "fase": str(registro["fase"]),
                    "modelo": str(registro["modelo"]),
                    "temporada": str(registro["temporada"]),
                    "mae": _numero(registro["mae"], "metricas.json"),
                    "rmse": _numero(registro["rmse"], "metricas.json"),
                    "vies": _numero(registro["vies"], "metricas.json"),
                    "n": int(registro["n"]),
                }
            )
        except KeyError as erro:
            raise ErroProjeto(f"campo ausente em metricas.json: {erro.args[0]}") from erro
    return linhas


def _linhas_importancias(caminho: Path) -> list[dict[str, Any]]:
    with _arquivo(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltantes = set(COLUNAS_IMPORTANCIAS) - set(leitor.fieldnames or [])
        if faltantes:
            raise ErroProjeto(f"colunas ausentes em importancias.csv: {sorted(faltantes)}")
        return [
            {
                "atributo": linha["atributo"],
                "delta_mae_media": _numero(linha["delta_mae_media"], "importancias.csv"),
                "delta_mae_desvio": _numero(linha["delta_mae_desvio"], "importancias.csv"),
            }
            for linha in leitor
        ]


# --- Tabelas e modelo TMSL -------------------------------------------------------------------


def _texto_literal(valor: object) -> str:
    """Literal de texto válido em M e DAX, com aspas duplas escapadas."""
    return '"' + str(valor).replace('"', '""') + '"'


def _m_valor(valor: object) -> str:
    return _texto_literal(valor) if isinstance(valor, str) else repr(valor)


def _tipo_tmsl(tipo: pa.DataType, origem: str) -> str:
    if pa.types.is_integer(tipo):
        return "int64"
    if pa.types.is_floating(tipo):
        return "double"
    if pa.types.is_string(tipo) or pa.types.is_large_string(tipo):
        return "string"
    if pa.types.is_date(tipo) or pa.types.is_timestamp(tipo):
        return "dateTime"
    if pa.types.is_boolean(tipo):
        return "boolean"
    raise ErroProjeto(f"tipo não suportado em {origem}: {tipo}")


def _colunas_parquet(caminho: Path) -> dict[str, str]:
    esquema = pq.read_schema(str(_arquivo(caminho)))
    return {c.name: _tipo_tmsl(c.type, f"{caminho.name}.{c.name}") for c in esquema}


def _tabela(nome: str, colunas: dict[str, str], expressao: list[str], medidas: list = None) -> dict:
    return {
        "name": nome,
        "columns": [
            {"name": c, "dataType": t, "sourceColumn": c, "summarizeBy": "none"}
            for c, t in colunas.items()
        ],
        "partitions": [
            {"name": nome, "mode": "import", "source": {"type": "m", "expression": expressao}}
        ],
        "measures": medidas or [],
    }


def _tabela_parquet(nome: str, caminho: Path, medidas: list = None) -> dict:
    caminho_m = _texto_literal(caminho.resolve())
    expressao = [
        "let",
        f"    Origem = Parquet.Document(File.Contents({caminho_m}))",
        "in",
        "    Origem",
    ]
    return _tabela(nome, _colunas_parquet(caminho), expressao, medidas)


def _tabela_registros(nome: str, linhas: list[dict[str, Any]], colunas: dict[str, str]) -> dict:
    tipos = ", ".join(f"{c} = {TIPO_M[t]}" for c, t in colunas.items())
    registros = ", ".join(
        "[" + ", ".join(f"{c} = {_m_valor(linha[c])}" for c in colunas) + "]" for linha in linhas
    )
    expressao = [
        "let",
        f"    Origem = Table.FromRecords({{{registros}}}, type table [{tipos}])",
        "in",
        "    Origem",
    ]
    return _tabela(nome, colunas, expressao)


def _relacionamento(tabela_muitos: str, coluna_muitos: str, tabela_um: str, coluna_um: str) -> dict:
    return {
        "name": f"{tabela_muitos}.{coluna_muitos}-{tabela_um}.{coluna_um}",
        "fromTable": tabela_muitos,
        "fromColumn": coluna_muitos,
        "toTable": tabela_um,
        "toColumn": coluna_um,
        "fromCardinality": "many",
        "toCardinality": "one",
        "crossFilteringBehavior": "oneDirection",
    }


def _medidas(meta: dict[str, str]) -> list[dict[str, str]]:
    constantes = [
        ("Modelo selecionado", meta["modelo_selecionado"]),
        ("Corte de treino", meta["corte_treino"]),
        ("Versão do modelo", meta["versao"]),
        ("Notas do modelo", meta["notas"]),
    ]
    return [{"name": n, "expression": _texto_literal(v)} for n, v in constantes] + [
        {"name": n, "expression": dax} for n, dax in MEDIDAS_DAX
    ]


# --- Páginas PBIR ---------------------------------------------------------------------------


def _id(*partes: str) -> str:
    """Identificador hexadecimal de 20 caracteres, estável entre execuções."""
    return hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()[:20]


def _c(tabela: str, campo: str) -> tuple[str, str, str]:
    return (tabela, campo, "Column")


def _m(nome: str) -> tuple[str, str, str]:
    return (FATO, nome, "Measure")


def _lit(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def _projecao(ref: tuple[str, str, str]) -> dict:
    tabela, campo, tipo = ref
    return {
        "field": {tipo: {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": campo}},
        "queryRef": f"{tabela}.{campo}",
        "nativeQueryRef": campo,
    }


def _envelope(pos: tuple[int, int, int, int], visual: dict) -> dict:
    x, y, largura, altura = pos
    return {"position": {"x": x, "y": y, "width": largura, "height": altura}, "visual": visual}


def _caixa_texto(pos, linhas: list[str], tamanho: str = "14px", cor: str = COR_TEXTO) -> dict:
    estilo = {"fontFamily": "Segoe UI", "fontSize": tamanho, "color": cor}
    paragrafos = [{"textRuns": [{"value": linha, "textStyle": estilo}]} for linha in linhas]
    visual = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": paragrafos}}]},
    }
    return _envelope(pos, visual)


def _titulo(texto: str) -> dict:
    return _caixa_texto((20, 20, 1240, 60), [texto], "24px")


def _visual(tipo: str, pos, papeis: dict[str, list], titulo: str) -> dict:
    estado = {p: {"projections": [_projecao(r) for r in refs]} for p, refs in papeis.items()}
    visual = {"visualType": tipo, "query": {"queryState": estado}}
    visual["visualContainerObjects"] = {
        "title": [
            {
                "properties": {
                    "show": _lit("true"),
                    "text": _lit(f"'{titulo}'"),
                    "fontSize": _lit("16D"),
                    "fontColor": {"solid": {"color": _lit(f"'{COR_TEXTO}'")}},
                }
            }
        ],
        "background": [{"properties": {"show": _lit("false")}}],
        "padding": [
            {"properties": {lado: _lit("8D") for lado in ("top", "bottom", "left", "right")}}
        ],
    }
    return _envelope(pos, visual)


def _pagina(nome: str, visuais: list[dict]) -> dict:
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
    pagina = {
        "$schema": SCHEMA_PAGINA,
        "name": ident,
        "displayName": nome,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
    }
    return {"id": ident, "pagina": pagina, "visuais": containers}


def _paginas(meta: dict[str, str]) -> list[dict]:
    """Sete páginas; layouts dentro de x 20–1260 e y 20–700."""
    eq = _c("dim_equipes", "nome_padronizado")
    ano = _c("dim_temporadas", "ano")
    modelo = (
        f"Modelo: {meta['modelo_selecionado']}. Corte de treino: {meta['corte_treino']}. "
        f"Versão: {meta['versao']}."
    )
    return [
        _pagina(
            "Visão Geral",
            [
                _titulo("Visão Geral"),
                _visual("card", (20, 90, 200, 110), {"Values": [_m("Partidas")]}, "Partidas"),
                _visual("card", (240, 90, 200, 110), {"Values": [_m("Gols")]}, "Gols"),
                _visual(
                    "card", (460, 90, 200, 110), {"Values": [_m("Gols por jogo")]}, "Gols por jogo"
                ),
                _visual("slicer", (680, 90, 280, 110), {"Values": [ano]}, "Temporada"),
                _visual("slicer", (980, 90, 280, 110), {"Values": [eq]}, "Equipe"),
                _visual(
                    "lineChart",
                    (20, 220, 600, 300),
                    {"Category": [ano], "Y": [_m("Gols")]},
                    "Gols por temporada",
                ),
                _visual(
                    "clusteredBarChart",
                    (640, 220, 620, 480),
                    {"Category": [eq], "Y": [_m("Pontos totais")]},
                    "Pontos por equipe",
                ),
                _caixa_texto(
                    (20, 540, 600, 160),
                    [
                        "Fonte: OpenFootball (CC0), temporadas 2018–2025.",
                        "Os filtros de equipe e temporada se aplicam aos indicadores.",
                    ],
                ),
            ],
        ),
        _pagina(
            "Tendências",
            [
                _titulo("Tendências"),
                _visual("slicer", (20, 90, 300, 100), {"Values": [ano]}, "Temporada"),
                _visual("slicer", (340, 90, 300, 100), {"Values": [eq]}, "Equipe"),
                _caixa_texto(
                    (660, 90, 600, 100),
                    ["Média recente: média de pontos nas últimas 5 partidas de cada equipe."],
                ),
                _visual(
                    "lineChart",
                    (20, 210, 1240, 240),
                    {"Category": [_c("analitico", "data_referencia")], "Y": [_m("Média recente")]},
                    "Média recente por data",
                ),
                _visual(
                    "clusteredBarChart",
                    (20, 470, 1240, 230),
                    {"Category": [eq], "Y": [_m("Média recente")]},
                    "Média recente por equipe",
                ),
            ],
        ),
        _pagina(
            "Estatística",
            [
                _titulo("Estatística"),
                _visual("slicer", (20, 90, 300, 100), {"Values": [ano]}, "Temporada"),
                _visual("slicer", (340, 90, 300, 100), {"Values": [eq]}, "Equipe"),
                _visual(
                    "clusteredColumnChart",
                    (20, 210, 600, 490),
                    {"Category": [_c(FATO, "pontos")], "Y": [_m("Observações de equipe")]},
                    "Distribuição de pontos (0, 1 e 3)",
                ),
                _visual(
                    "tableEx",
                    (640, 90, 620, 610),
                    {
                        "Values": [
                            eq,
                            _m("Partidas"),
                            _m("Gols"),
                            _m("Pontos totais"),
                            _m("Gols por jogo"),
                        ]
                    },
                    "Tabela estatística",
                ),
            ],
        ),
        _pagina(
            "Laboratório de Modelos",
            [
                _titulo("Laboratório de Modelos"),
                _visual(
                    "card",
                    (20, 90, 300, 120),
                    {"Values": [_m("MAE global selecionado")]},
                    "MAE global holdout (selecionado)",
                ),
                _visual(
                    "card",
                    (340, 90, 300, 120),
                    {"Values": [_m("MAE global baseline")]},
                    "MAE global holdout (M00 baseline)",
                ),
                _visual(
                    "card",
                    (660, 90, 300, 120),
                    {"Values": [_m("Modelo selecionado")]},
                    "Modelo selecionado",
                ),
                _visual(
                    "card",
                    (980, 90, 280, 120),
                    {"Values": [_m("Corte de treino")]},
                    "Corte de treino",
                ),
                _visual(
                    "tableEx",
                    (20, 230, 760, 470),
                    {
                        "Values": [
                            _c("metricas", c)
                            for c in ("fase", "modelo", "temporada", "mae", "rmse")
                        ]
                    },
                    "Métricas dos modelos",
                ),
                _visual(
                    "clusteredBarChart",
                    (800, 230, 460, 470),
                    {"Category": [_c("importancias", "atributo")], "Y": [_m("Importância")]},
                    "Importância por permutação (ΔMAE)",
                ),
            ],
        ),
        _pagina(
            "Previsões",
            [
                _titulo("Previsões"),
                _visual("slicer", (20, 90, 320, 100), {"Values": [eq]}, "Equipe"),
                _caixa_texto(
                    (360, 90, 900, 100),
                    [
                        "Previsões retrospectivas 2025; horizonte 5 partidas, não certezas.",
                        modelo + " Intervalo: 90% empírico.",
                    ],
                ),
                _visual(
                    "lineChart",
                    (20, 210, 760, 490),
                    {
                        "Category": [_c("previsoes", "data_referencia")],
                        "Y": [_m("Média prevista"), _m("Média observada")],
                    },
                    "Média prevista e observada",
                ),
                _visual(
                    "tableEx",
                    (800, 210, 460, 490),
                    {
                        "Values": [
                            _c("previsoes", c)
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
        ),
        _pagina(
            "Assistente",
            [
                _titulo("Assistente"),
                _caixa_texto(
                    (20, 90, 1240, 300),
                    [
                        "Assistente de perguntas e respostas sobre dados e previsões (fase T009).",
                        "Para usar, inicie a API FastAPI local e abra o endereço no navegador.",
                        "A página não depende de serviço externo e não envia dados para a nuvem.",
                        "Sem a API ativa, o endereço não responde.",
                    ],
                    "16px",
                ),
                _caixa_texto((20, 420, 800, 80), [URL_ASSISTENTE], "24px", COR_DESTAQUE),
            ],
        ),
        _pagina(
            "Metodologia",
            [
                _titulo("Metodologia"),
                _caixa_texto(
                    (20, 90, 1240, 610),
                    [
                        "Fonte: OpenFootball, licença CC0 verificada (docs/sources_audit.md).",
                        "Período analisado: temporadas 2018–2025 do Campeonato Brasileiro Série A.",
                        "Dados de 2026 estão fora do escopo.",
                        modelo,
                        "Alvo: média de pontos nas próximas 5 partidas.",
                        "Validação temporal com janela expansiva; holdout exclusivo de 2025.",
                        "Baseline: M00 média recente de 5 partidas. Métricas: MAE e RMSE.",
                        "Limitações: dados observacionais, uma competição "
                        "e amostra pequena por equipe.",
                        "Previsões não são certezas.",
                        "Correlação e importância preditiva não indicam causalidade.",
                        "Tema observacional: os resultados descrevem o passado.",
                        "Não garantem desempenho futuro.",
                        f"Notas do modelo: {meta['notas']}",
                    ],
                ),
            ],
        ),
    ]


# --- Escrita e validação final ----------------------------------------------------------------


def _validar_referencias(tabelas: list[dict], paginas: list[dict]) -> None:
    colunas = {t["name"]: {c["name"] for c in t["columns"]} for t in tabelas}
    campos = {t["name"]: colunas[t["name"]] | {m["name"] for m in t["measures"]} for t in tabelas}
    for de, ce, para, cp in RELACIONAMENTOS:
        if ce not in colunas.get(de, set()) or cp not in colunas.get(para, set()):
            raise ErroProjeto(f"relacionamento sem coluna: {de}[{ce}] -> {para}[{cp}]")
    for tabela in tabelas:
        for medida in tabela["measures"]:
            for tab, col in re.findall(r"(\w+)\[(\w+)\]", medida["expression"]):
                if col not in colunas.get(tab, set()):
                    raise ErroProjeto(
                        f"medida {medida['name']} referencia coluna inexistente: {tab}[{col}]"
                    )
    for pagina in paginas:
        for visual in pagina["visuais"]:
            pos = visual["position"]
            if (
                pos["x"] < 20
                or pos["y"] < 20
                or pos["x"] + pos["width"] > 1260
                or pos["y"] + pos["height"] > 700
            ):
                raise ErroProjeto(
                    f"visual fora da área útil na página {pagina['pagina']['displayName']}"
                )
            estado = visual["visual"].get("query", {}).get("queryState", {})
            for papel in estado.values():
                for proj in papel["projections"]:
                    origem = next(iter(proj["field"].values()))
                    entidade, propriedade = (
                        origem["Expression"]["SourceRef"]["Entity"],
                        origem["Property"],
                    )
                    if propriedade not in campos.get(entidade, set()):
                        raise ErroProjeto(f"campo de visual inexistente: {entidade}[{propriedade}]")


def _escrever_modelo(raiz: Path, modelo: dict) -> None:
    semantico = raiz / f"{NOME}.SemanticModel"
    _gravar_json(semantico / "definition.pbism", {"version": "4.0"})
    _gravar_json(semantico / "model.bim", modelo)


def _escrever_relatorio(raiz: Path, paginas: list[dict]) -> None:
    relatorio = raiz / f"{NOME}.Report"
    pbir = _ler_json(relatorio / "definition.pbir")
    pbir["datasetReference"] = {"byPath": {"path": f"../{NOME}.SemanticModel"}}
    _gravar_json(relatorio / "definition.pbir", pbir)
    paginas_dir = relatorio / "definition" / "pages"
    shutil.rmtree(paginas_dir, ignore_errors=True)
    for pagina in paginas:
        _gravar_json(paginas_dir / pagina["id"] / "page.json", pagina["pagina"])
        for visual in pagina["visuais"]:
            destino = paginas_dir / pagina["id"] / "visuals" / visual["name"] / "visual.json"
            _gravar_json(destino, visual)
    ids = [p["id"] for p in paginas]
    _gravar_json(
        paginas_dir / "pages.json",
        {"$schema": SCHEMA_PAGINAS, "pageOrder": ids, "activePageName": ids[0]},
    )
