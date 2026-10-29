"""Gerador do projeto Power BI local (PBIP/PBIR) do Além do Placar (T008).

Copia o scaffold oficial do template, substitui as páginas e gera o modelo semântico (TMSL em
model.bim) com partições M que leem somente arquivos locais. Não executa CLI, não acessa rede e
não altera as pastas de entrada.
"""

import csv
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from evaluation.powerbi_layout import construir_paginas, construir_tema

NOME = "AlemDoPlacar"
URL_ASSISTENTE = "https://ALTERAR"
TEMA_ARQUIVO = "AlemDoPlacarTheme.json"
MODELO_BASELINE = "M00_media_recente_5"
FATO = "fato_desempenho_equipes"
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

# (nome, expressão DAX, formatString)
_VIT_CASA = f'CALCULATE(COUNTROWS({FATO}),{FATO}[mando_campo]="mandante",{FATO}[pontos]=3)'
_JOGOS_CASA = f'CALCULATE(COUNTROWS({FATO}),{FATO}[mando_campo]="mandante")'
_MAE = "CALCULATE(MAX(metricas[mae]),metricas[fase]="
_RMSE = "CALCULATE(MAX(metricas[rmse]),metricas[fase]="
MEDIDAS_DAX = [
    ("Partidas", f"DISTINCTCOUNT({FATO}[partida_id])", "#,0"),
    ("Temporadas", "DISTINCTCOUNT(dim_temporadas[ano])", "0"),
    ("Observações de equipe", f"COUNTROWS({FATO})", "#,0"),
    ("Gols", f"SUM({FATO}[gols_pro])", "#,0"),
    ("Gols sofridos", f"SUM({FATO}[gols_contra])", "#,0"),
    ("Saldo de gols", f"SUM({FATO}[saldo_gols])", "+#,0;-#,0;0"),
    ("Pontos totais", f"SUM({FATO}[pontos])", "#,0"),
    ("Vitórias", f"CALCULATE(COUNTROWS({FATO}),{FATO}[pontos]=3)", "#,0"),
    ("Empates", f"CALCULATE(COUNTROWS({FATO}),{FATO}[pontos]=1)", "#,0"),
    ("Derrotas", f"CALCULATE(COUNTROWS({FATO}),{FATO}[pontos]=0)", "#,0"),
    ("Gols por jogo", "DIVIDE([Gols],[Partidas])", "0.00"),
    ("Gols sofridos por jogo", "DIVIDE([Gols sofridos],[Observações de equipe])", "0.00"),
    ("Pontos por jogo", "DIVIDE([Pontos totais],[Observações de equipe])", "0.00"),
    ("Aproveitamento", "DIVIDE([Pontos totais],3*[Observações de equipe])", "0.0%"),
    ("Vitórias do mandante", f"DIVIDE({_VIT_CASA},{_JOGOS_CASA})", "0.0%"),
    ("Volatilidade de pontos", f"STDEV.P({FATO}[pontos])", "0.00"),
    (
        "Posição",
        "IF(ISINSCOPE(dim_equipes[nome_padronizado]),"
        "RANKX(ALL(dim_equipes[nome_padronizado]),[Pontos totais],,DESC,Dense))",
        "0",
    ),
    ("Média prevista", "AVERAGE(previsoes[previsao])", "0.00"),
    ("Média observada", "AVERAGE(previsoes[alvo])", "0.00"),
    ("Limite inferior", "AVERAGE(previsoes[limite_inferior])", "0.00"),
    ("Limite superior", "AVERAGE(previsoes[limite_superior])", "0.00"),
    (
        "Erro absoluto médio",
        "AVERAGEX(previsoes,ABS(previsoes[previsao]-previsoes[alvo]))",
        "0.000",
    ),
    ("Média 3 jogos", "AVERAGE(analitico[media_pontos_3])", "0.00"),
    ("Média recente", "AVERAGE(analitico[media_pontos_5])", "0.00"),
    ("Média 10 jogos", "AVERAGE(analitico[media_pontos_10])", "0.00"),
    ("Importância", "AVERAGE(importancias[delta_mae_media])", "0.0000"),
    (
        "MAE global selecionado",
        "VAR ModeloAtual = [Modelo selecionado] RETURN "
        'CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",'
        'metricas[modelo]=ModeloAtual,metricas[temporada]="todas")',
        "0.000",
    ),
    (
        "MAE global baseline",
        'CALCULATE(MAX(metricas[mae]),metricas[fase]="holdout",'
        f'metricas[modelo]="{MODELO_BASELINE}",metricas[temporada]="todas")',
        "0.000",
    ),
    ("MAE validação", _MAE + '"validacao",metricas[temporada]="todas")', "0.000"),
    ("MAE holdout", _MAE + '"holdout",metricas[temporada]="todas")', "0.000"),
    ("RMSE validação", _RMSE + '"validacao",metricas[temporada]="todas")', "0.000"),
    ("RMSE holdout", _RMSE + '"holdout",metricas[temporada]="todas")', "0.000"),
]


class ErroProjeto(ValueError):
    """Entrada ausente ou inválida, ou saída já ocupada."""


def _url_dados(url_base: str | None, subpasta: str, arquivo: str) -> str | None:
    return f"{url_base.rstrip('/')}/{subpasta}/{arquivo}" if url_base else None


def gerar_projeto(
    pasta_saida: Path,
    pasta_processados: Path,
    pasta_modelagem: Path,
    pasta_cientifica: Path,
    template_dir: Path,
    *,
    fonte_dados: str = "local",
    url_base_dados: str | None = None,
    url_assistente: str = URL_ASSISTENTE,
    tokens: Path | None = None,
) -> Path:
    """Gera o projeto PBIP em ``pasta_saida`` e devolve o caminho do ``.pbip``.

    As pastas de entrada são somente lidas. ``pasta_saida`` deve estar ausente ou vazia.
    ``fonte_dados="web"`` troca ``File.Contents`` por ``Web.Contents`` em ``url_base_dados``
    (ex.: ``https://raw.githubusercontent.com/usuario/repo/main/data``), o que permite atualizar
    o relatório publicado sem gateway. O padrão ``"local"`` não acessa rede.
    """
    if fonte_dados not in {"local", "web"}:
        raise ErroProjeto("fonte_dados deve ser 'local' ou 'web'")
    if fonte_dados == "web" and not (url_base_dados or "").startswith("https://"):
        raise ErroProjeto("fonte_dados='web' exige url_base_dados começando com https://")
    web = fonte_dados == "web"
    tokens_design = _ler_tokens(tokens)
    saida_resolvida = pasta_saida.resolve()
    for entrada in (pasta_processados, pasta_modelagem, pasta_cientifica, template_dir):
        origem_resolvida = entrada.resolve()
        if saida_resolvida == origem_resolvida or origem_resolvida in saida_resolvida.parents:
            raise ErroProjeto("saída não pode estar dentro de uma pasta de entrada")
    _validar_template(template_dir)
    _validar_saida(pasta_saida)
    meta = _ler_metadados(pasta_modelagem / "metadados.json")

    def _proc(nome: str, medidas: list | None = None, arquivo: str | None = None) -> dict:
        arq = arquivo or f"{nome}.parquet"
        url = _url_dados(url_base_dados, "processed", arq) if web else None
        return _tabela_parquet(nome, pasta_processados / arq, medidas, url)

    tabelas = [_proc(nome) for nome in ("dim_equipes", "dim_temporadas", "fato_partidas")]
    tabelas.append(_proc(FATO, _medidas(meta)))
    url_prev = _url_dados(url_base_dados, "predictions/modelagem", "previsoes.parquet")
    tabelas += [
        _proc("analitico", arquivo="dataset_analitico.parquet"),
        _tabela_parquet(
            "previsoes", pasta_modelagem / "previsoes.parquet", None, url_prev if web else None
        ),
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
    paginas = construir_paginas(meta, tokens_design, url_assistente)
    _validar_referencias(tabelas, paginas)
    shutil.copytree(template_dir, pasta_saida, dirs_exist_ok=True)
    _escrever_modelo(pasta_saida, modelo)
    _escrever_relatorio(pasta_saida, paginas, construir_tema(tokens_design))
    return pasta_saida / f"{NOME}.pbip"


def _ler_tokens(caminho: Path | None) -> dict[str, str]:
    """Tokens de design de ``tema_tokens.json``; sem arquivo, usa o padrão do layout."""
    if caminho is None:
        return {}
    dados = _ler_json(caminho)
    cores = dados.get("cores") if isinstance(dados, dict) else None
    if not isinstance(cores, dict):
        raise ErroProjeto(f"tokens inválidos: {caminho}")
    return {str(k): str(v) for k, v in cores.items()}


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
        **(
            {"cobertura": str(dados["cobertura_holdout"])}
            if isinstance(dados.get("cobertura_holdout"), int | float)
            else {}
        ),
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


def _tabela_parquet(
    nome: str, caminho: Path, medidas: list | None = None, url: str | None = None
) -> dict:
    """Partição Parquet local (``File.Contents``) ou, se ``url`` for dada, ``Web.Contents``."""
    if url:
        origem = f"Parquet.Document(Web.Contents({_texto_literal(url)}))"
    else:
        origem = f"Parquet.Document(File.Contents({_texto_literal(caminho.resolve())}))"
    expressao = ["let", f"    Origem = {origem}", "in", "    Origem"]
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
    medidas = [{"name": n, "expression": _texto_literal(v)} for n, v in constantes]
    if meta.get("cobertura"):
        medidas.append(
            {
                "name": "Cobertura do intervalo",
                "expression": repr(float(meta["cobertura"])),
                "formatString": "0.0%",
            }
        )
    for nome, dax, formato in MEDIDAS_DAX:
        medida = {"name": nome, "expression": dax}
        if formato:
            medida["formatString"] = formato
        medidas.append(medida)
    return medidas


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
                pos["x"] < 0
                or pos["y"] < 0
                or pos["x"] + pos["width"] > 1280
                or pos["y"] + pos["height"] > 720
            ):
                raise ErroProjeto(
                    f"visual fora do canvas na página {pagina['pagina']['displayName']}"
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


def _escrever_relatorio(raiz: Path, paginas: list[dict], tema: dict) -> None:
    relatorio = raiz / f"{NOME}.Report"
    pbir = _ler_json(relatorio / "definition.pbir")
    pbir["datasetReference"] = {"byPath": {"path": f"../{NOME}.SemanticModel"}}
    _gravar_json(relatorio / "definition.pbir", pbir)
    _registrar_tema(relatorio, tema)
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


def _registrar_tema(relatorio: Path, tema: dict) -> None:
    """Grava o tema do projeto em RegisteredResources e o registra em report.json."""
    _gravar_json(relatorio / "StaticResources" / "RegisteredResources" / TEMA_ARQUIVO, tema)
    caminho = relatorio / "definition" / "report.json"
    dados = _ler_json(caminho)
    colecao = dados.setdefault("themeCollection", {})
    versao = colecao.get("baseTheme", {}).get(
        "reportVersionAtImport", {"visual": "2.11.0", "report": "3.4.0", "page": "2.3.1"}
    )
    colecao["customTheme"] = {
        "name": TEMA_ARQUIVO,
        "reportVersionAtImport": versao,
        "type": "RegisteredResources",
    }
    pacotes = [
        p
        for p in dados.setdefault("resourcePackages", [])
        if p.get("name") != "RegisteredResources"
    ]
    pacotes.append(
        {
            "name": "RegisteredResources",
            "type": "RegisteredResources",
            "items": [{"name": TEMA_ARQUIVO, "path": TEMA_ARQUIVO, "type": "CustomTheme"}],
        }
    )
    dados["resourcePackages"] = pacotes
    _gravar_json(caminho, dados)
