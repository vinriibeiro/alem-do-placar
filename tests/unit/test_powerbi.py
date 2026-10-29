import json
import re
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from evaluation.powerbi import ErroProjeto, gerar_projeto
from processing.persistencia import ESQUEMAS

ANALITICO = pa.schema(
    [
        ("equipe", pa.string()),
        ("temporada", pa.int64()),
        ("data_referencia", pa.date32()),
        ("media_pontos_5", pa.float64()),
    ]
)
PREVISOES = pa.schema(
    [
        ("equipe", pa.string()),
        ("temporada", pa.int64()),
        ("data_referencia", pa.date32()),
        ("previsao", pa.float64()),
        ("alvo", pa.float64()),
        ("limite_inferior", pa.float64()),
        ("limite_superior", pa.float64()),
    ]
)
METRICAS = [
    {
        "fase": "holdout",
        "modelo": "M01_ridge",
        "temporada": "todas",
        "mae": 0.478089,
        "rmse": 0.590887,
        "vies": -0.01683,
        "n": 660,
    },
    {
        "fase": "holdout",
        "modelo": "M00_media_recente_5",
        "temporada": "todas",
        "mae": 0.567091,
        "rmse": 0.722596,
        "vies": -0.00152,
        "n": 660,
    },
    {
        "fase": "holdout",
        "modelo": "M01_ridge",
        "temporada": 2025,
        "mae": 0.478089,
        "rmse": 0.590887,
        "vies": -0.01683,
        "n": 660,
    },
]
METADADOS = {
    "modelo_selecionado": "M01_ridge",
    "corte_treino": "2025-03-29",
    "versao": "T006-1.0",
    "notas": "Holdout 2025 não usado na seleção.",
}
IMPORTANCIAS = (
    "atributo,delta_mae_media,delta_mae_desvio\nmedia_pontos_5,0.25,0.01\nmando,-0.002,0.003\n"
)


def _json(caminho: Path, dados: object) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def _vazia(esquema: pa.Schema) -> pa.Table:
    return pa.Table.from_pylist([], schema=esquema)


def _template(raiz: Path) -> Path:
    relatorio = raiz / "AlemDoPlacar.Report"
    (raiz / "AlemDoPlacar.pbip").write_text('{"version":"1.0"}', encoding="utf-8")
    _json(
        relatorio / "definition.pbir",
        {"version": "4.0", "datasetReference": {"byPath": {"path": "../Outro"}}},
    )
    _json(relatorio / "definition/version.json", {"version": "2.0.0"})
    _json(relatorio / "definition/report.json", {"version": "4.0"})
    _json(relatorio / "definition/pages/old/page.json", {"name": "old"})
    tema = relatorio / "StaticResources/SharedResources/BaseThemes"
    tema.mkdir(parents=True)
    (tema / "Fluent2-CY26SU10.json").write_text('{"name":"tema"}', encoding="utf-8")
    return raiz


@pytest.fixture
def entradas(tmp_path: Path) -> dict[str, Path]:
    pastas = {n: tmp_path / n for n in ("processados", "modelagem", "cientifica", "template")}
    for pasta in pastas.values():
        pasta.mkdir()
    for nome in ("dim_equipes", "dim_temporadas", "fato_partidas", "fato_desempenho_equipes"):
        pq.write_table(_vazia(ESQUEMAS[nome]), pastas["processados"] / f"{nome}.parquet")
    pq.write_table(_vazia(ANALITICO), pastas["processados"] / "dataset_analitico.parquet")
    pq.write_table(_vazia(PREVISOES), pastas["modelagem"] / "previsoes.parquet")
    _json(pastas["modelagem"] / "metricas.json", METRICAS)
    _json(pastas["modelagem"] / "metadados.json", METADADOS)
    (pastas["cientifica"] / "importancias.csv").write_text(IMPORTANCIAS, encoding="utf-8")
    _template(pastas["template"])
    return pastas


def _gerar(entradas: dict[str, Path], saida: Path) -> Path:
    return gerar_projeto(
        saida,
        entradas["processados"],
        entradas["modelagem"],
        entradas["cientifica"],
        entradas["template"],
    )


def _modelo(saida: Path) -> dict:
    return json.loads((saida / "AlemDoPlacar.SemanticModel/model.bim").read_text(encoding="utf-8"))


def _snapshot(pastas: dict[str, Path]) -> dict[str, bytes]:
    return {
        f"{n}/{p.relative_to(raiz).as_posix()}": p.read_bytes()
        for n, raiz in pastas.items()
        for p in raiz.rglob("*")
        if p.is_file()
    }


def test_gera_pbip_sete_paginas_e_preserva_tema(entradas, tmp_path):
    saida = tmp_path / "saida"
    assert _gerar(entradas, saida) == saida / "AlemDoPlacar.pbip"
    report = saida / "AlemDoPlacar.Report"
    paginas = json.loads((report / "definition/pages/pages.json").read_text(encoding="utf-8"))
    assert len(paginas["pageOrder"]) == 7
    assert all(re.fullmatch(r"[0-9a-f]{20}", p) for p in paginas["pageOrder"])
    assert paginas["activePageName"] == paginas["pageOrder"][0]
    assert not (report / "definition/pages/old").exists()
    tema = report / "StaticResources/SharedResources/BaseThemes/Fluent2-CY26SU10.json"
    assert tema.read_text(encoding="utf-8") == '{"name":"tema"}'
    pbir = json.loads((report / "definition.pbir").read_text(encoding="utf-8"))
    assert pbir["datasetReference"] == {"byPath": {"path": "../AlemDoPlacar.SemanticModel"}}


def test_ids_estaveis_entre_execucoes(entradas, tmp_path):
    _gerar(entradas, tmp_path / "a")
    _gerar(entradas, tmp_path / "b")
    arquivo = "AlemDoPlacar.Report/definition/pages/pages.json"
    assert (tmp_path / "a" / arquivo).read_text() == (tmp_path / "b" / arquivo).read_text()


def test_modelo_tmsl_relacionamentos_e_particoes_locais(entradas, tmp_path):
    saida = tmp_path / "saida"
    _gerar(entradas, saida)
    modelo = _modelo(saida)["model"]
    assert modelo["culture"] == "pt-BR"
    assert len(modelo["relationships"]) == 7
    tabelas = {t["name"]: t for t in modelo["tables"]}
    assert {"dim_equipes", "analitico", "previsoes", "metricas", "importancias"} <= set(tabelas)
    tipos = {c["name"]: c["dataType"] for c in tabelas["fato_partidas"]["columns"]}
    assert tipos["partida_id"] == "string" and tipos["temporada_id"] == "int64"
    for tabela in modelo["tables"]:
        expressao = "\n".join(tabela["partitions"][0]["source"]["expression"])
        assert "Web.Contents" not in expressao and "Sql." not in expressao
    assert 'temporada = "2025"' in "\n".join(
        tabelas["metricas"]["partitions"][0]["source"]["expression"]
    )
    assert "delta_mae_media = 0.25" in "\n".join(
        tabelas["importancias"]["partitions"][0]["source"]["expression"]
    )


def test_medidas_referenciam_colunas_existentes(entradas, tmp_path):
    saida = tmp_path / "saida"
    _gerar(entradas, saida)
    tabelas = {t["name"]: t for t in _modelo(saida)["model"]["tables"]}
    medidas = {m["name"]: m["expression"] for m in tabelas["fato_desempenho_equipes"]["measures"]}
    esperadas = {
        "Partidas",
        "Gols",
        "Pontos totais",
        "Gols por jogo",
        "Média prevista",
        "Média observada",
        "MAE global selecionado",
        "MAE global baseline",
        "Média recente",
        "Importância",
        "Modelo selecionado",
    }
    assert esperadas <= set(medidas)
    assert '"M00_media_recente_5"' in medidas["MAE global baseline"]
    for tabela in tabelas.values():
        colunas = {c["name"] for c in tabela["columns"]}
        for tab, col in re.findall(r"(\w+)\[(\w+)\]", "".join(medidas.values())):
            if tab == tabela["name"]:
                assert col in colunas


def test_nao_altera_entradas(entradas, tmp_path):
    antes = _snapshot(entradas)
    _gerar(entradas, tmp_path / "saida")
    assert _snapshot(entradas) == antes


def test_saida_com_arquivos_falha_sem_sobrescrever(entradas, tmp_path):
    saida = tmp_path / "saida"
    saida.mkdir()
    (saida / "trabalho.txt").write_text("manual", encoding="utf-8")
    with pytest.raises(ErroProjeto, match="não será sobrescrita"):
        _gerar(entradas, saida)
    assert (saida / "trabalho.txt").read_text(encoding="utf-8") == "manual"
    assert not (saida / "AlemDoPlacar.pbip").exists()


def test_saida_vazia_e_permitida(entradas, tmp_path):
    saida = tmp_path / "vazia"
    saida.mkdir()
    assert _gerar(entradas, saida).is_file()


def test_campo_ausente_em_metadados_gera_erro_claro(entradas, tmp_path):
    caminho = entradas["modelagem"] / "metadados.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    del dados["corte_treino"]
    _json(caminho, dados)
    with pytest.raises(ErroProjeto, match="campo ausente em metadados.json: corte_treino"):
        _gerar(entradas, tmp_path / "saida")


def test_tipo_complexo_no_parquet_e_rejeitado(entradas, tmp_path):
    esquema = pa.schema([("equipe", pa.string()), ("lista", pa.list_(pa.int64()))])
    pq.write_table(_vazia(esquema), entradas["modelagem"] / "previsoes.parquet")
    with pytest.raises(ErroProjeto, match="tipo não suportado"):
        _gerar(entradas, tmp_path / "saida")


@pytest.mark.parametrize("pasta", ["processados", "modelagem", "cientifica", "template"])
def test_saida_interna_a_entrada_e_rejeitada_sem_modificar_arquivos(entradas, pasta):
    antes = _snapshot(entradas)
    with pytest.raises(ErroProjeto, match="dentro de uma pasta de entrada"):
        _gerar(entradas, entradas[pasta] / "gerado")
    assert _snapshot(entradas) == antes


def test_metadados_t006_sem_notas_opcionais_sao_aceitos(entradas, tmp_path):
    dados = {k: v for k, v in METADADOS.items() if k != "notas"}
    _json(entradas["modelagem"] / "metadados.json", dados)
    _gerar(entradas, tmp_path / "saida")


def test_nomes_de_medidas_nao_colidem_com_colunas_ignorando_caixa(entradas, tmp_path):
    saida = tmp_path / "saida"
    _gerar(entradas, saida)
    for tabela in _modelo(saida)["model"]["tables"]:
        colunas = {c["name"].casefold() for c in tabela["columns"]}
        medidas = {m["name"].casefold() for m in tabela["measures"]}
        assert not colunas.intersection(medidas)
