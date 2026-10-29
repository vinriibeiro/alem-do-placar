"""Testes do redesign do relatório Power BI (F3): layout, tema, navegação e fonte web."""

import json
from itertools import combinations
from pathlib import Path

import pytest
from test_powerbi import _gerar, _modelo, entradas  # noqa: F401

from evaluation.powerbi import ErroProjeto, gerar_projeto

RAIZ = Path(__file__).resolve().parents[2]
TOKENS = RAIZ / "dashboard" / "assets" / "tema_tokens.json"
TEMA = "AlemDoPlacar.Report/StaticResources/RegisteredResources/AlemDoPlacarTheme.json"


def _visuais(saida: Path) -> dict[str, list[dict]]:
    relatorio = saida / "AlemDoPlacar.Report" / "definition" / "pages"
    ordem = json.loads((relatorio / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    paginas = {}
    for ident in ordem:
        pagina = json.loads((relatorio / ident / "page.json").read_text(encoding="utf-8"))
        paginas[pagina["displayName"]] = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((relatorio / ident / "visuals").glob("*/visual.json"))
        ]
    return paginas


def _gerar_com(pastas, destino: Path, **kwargs) -> Path:
    gerar_projeto(
        destino,
        pastas["processados"],
        pastas["modelagem"],
        pastas["cientifica"],
        pastas["template"],
        **kwargs,
    )
    return destino


@pytest.fixture
def saida(entradas, tmp_path):  # noqa: F811
    destino = tmp_path / "saida"
    _gerar(entradas, destino)
    return destino


def test_sete_paginas_na_ordem_do_prd(saida):
    assert list(_visuais(saida)) == [
        "Visão Geral",
        "Tendências",
        "Estatística",
        "Laboratório de Modelos",
        "Previsões",
        "Assistente",
        "Metodologia",
    ]


def test_toda_pagina_tem_cabecalho_navegacao_e_rodape(saida):
    for nome, visuais in _visuais(saida).items():
        tipos = [v["visual"]["visualType"] for v in visuais]
        assert tipos.count("pageNavigator") == 1, nome
        topo = [v for v in visuais if v["position"]["y"] == 0]
        assert sum(v["position"]["width"] for v in topo) == 1280, nome
        assert nome in json.dumps([v["visual"] for v in topo], ensure_ascii=False)
        for v in topo:
            contexto = v["visual"]["visualContainerObjects"]
            assert (
                contexto["visualHeader"][0]["properties"]["show"]["expr"]["Literal"]["Value"]
                == "false"
            )
        assert any(v["position"]["y"] >= 698 for v in visuais), nome


def test_visuais_dentro_do_canvas_e_sem_sobreposicao(saida):
    for nome, visuais in _visuais(saida).items():
        for v in visuais:
            p = v["position"]
            assert p["x"] >= 0 and p["y"] >= 0 and p["x"] + p["width"] <= 1280, nome
            assert p["y"] + p["height"] <= 720, nome
        for a, b in combinations(visuais, 2):
            pa, pb = a["position"], b["position"]
            separados = (
                pa["x"] + pa["width"] <= pb["x"]
                or pb["x"] + pb["width"] <= pa["x"]
                or pa["y"] + pa["height"] <= pb["y"]
                or pb["y"] + pb["height"] <= pa["y"]
            )
            assert separados, f"{nome}: sobreposição {pa} x {pb}"


def test_paginas_de_dados_nao_dependem_de_caixas_de_texto(saida):
    paginas = _visuais(saida)
    for nome in ("Visão Geral", "Tendências", "Estatística", "Laboratório de Modelos", "Previsões"):
        tipos = [v["visual"]["visualType"] for v in paginas[nome]]
        dados = [t for t in tipos if t not in {"textbox", "pageNavigator"}]
        assert len(dados) >= 4, nome


def test_tema_gravado_e_registrado_no_relatorio(saida):
    tema = json.loads((saida / TEMA).read_text(encoding="utf-8"))
    assert tema["name"] == "AlemDoPlacar" and len(tema["dataColors"]) >= 6
    fundo = tema["visualStyles"]["page"]["*"]["background"][0]["color"]["solid"]["color"]
    assert fundo == "#f6f8fa"
    rj = json.loads(
        (saida / "AlemDoPlacar.Report/definition/report.json").read_text(encoding="utf-8")
    )
    assert rj["themeCollection"]["customTheme"]["name"] == "AlemDoPlacarTheme.json"
    pacotes = {p["name"]: p for p in rj["resourcePackages"]}
    assert pacotes["RegisteredResources"]["items"][0]["type"] == "CustomTheme"


def test_tokens_do_site_alimentam_o_tema(entradas, tmp_path):  # noqa: F811
    destino = _gerar_com(entradas, tmp_path / "com_tokens", tokens=TOKENS)
    tema = json.loads((destino / TEMA).read_text(encoding="utf-8"))
    cores = json.loads(TOKENS.read_text(encoding="utf-8"))["cores"]
    assert tema["dataColors"][0] == cores["serie-1"]
    assert tema["tableAccent"] == cores["cor-destaque"]


def test_tokens_invalidos_geram_erro_claro(entradas, tmp_path):  # noqa: F811
    ruim = tmp_path / "t.json"
    ruim.write_text('{"x": 1}', encoding="utf-8")
    with pytest.raises(ErroProjeto, match="tokens inválidos"):
        _gerar_com(entradas, tmp_path / "s", tokens=ruim)


def test_botao_do_assistente_abre_a_url_informada(entradas, tmp_path):  # noqa: F811
    destino = _gerar_com(
        entradas, tmp_path / "url", url_assistente="https://alem.example/assistente"
    )
    texto = json.dumps(_visuais(destino)["Assistente"], ensure_ascii=False)
    assert '"url": "https://alem.example/assistente"' in texto
    assert "127.0.0.1" not in texto


def test_url_padrao_do_assistente_e_um_marcador_visivel(saida):
    assert "https://ALTERAR" in json.dumps(_visuais(saida)["Assistente"], ensure_ascii=False)


def test_fonte_web_usa_web_contents_e_nao_caminhos_locais(entradas, tmp_path):  # noqa: F811
    destino = _gerar_com(
        entradas,
        tmp_path / "web",
        fonte_dados="web",
        url_base_dados="https://raw.githubusercontent.com/u/r/main/data/",
    )
    tabelas = {
        t["name"]: "\n".join(t["partitions"][0]["source"]["expression"])
        for t in _modelo(destino)["model"]["tables"]
    }
    esperado = "https://raw.githubusercontent.com/u/r/main/data/processed/dim_equipes.parquet"
    assert f'Web.Contents("{esperado}")' in tabelas["dim_equipes"]
    assert "predictions/modelagem/previsoes.parquet" in tabelas["previsoes"]
    assert "processed/dataset_analitico.parquet" in tabelas["analitico"]
    for nome in ("dim_equipes", "fato_desempenho_equipes", "analitico", "previsoes"):
        assert "File.Contents" not in tabelas[nome] and "C:\\" not in tabelas[nome]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fonte_dados": "web"},
        {"fonte_dados": "web", "url_base_dados": "http://inseguro.example/data"},
        {"fonte_dados": "ftp", "url_base_dados": "https://x/y"},
    ],
)
def test_fonte_web_exige_https_e_valor_valido(entradas, tmp_path, kwargs):  # noqa: F811
    with pytest.raises(ErroProjeto):
        _gerar_com(entradas, tmp_path / "s", **kwargs)
    assert not (tmp_path / "s").exists()


def _fato(saida: Path) -> dict:
    tabelas = _modelo(saida)["model"]["tables"]
    return next(t for t in tabelas if t["name"] == "fato_desempenho_equipes")


def test_medidas_novas_tem_formato_e_nomes_unicos(saida):
    medidas = _fato(saida)["measures"]
    nomes = [m["name"] for m in medidas]
    assert len(nomes) == len(set(nomes))
    formatos = {m["name"]: m.get("formatString") for m in medidas}
    assert formatos["Aproveitamento"] == "0.0%"
    assert formatos["Vitórias do mandante"] == "0.0%"
    novas = {
        "Posição",
        "Volatilidade de pontos",
        "Saldo de gols",
        "Temporadas",
        "Erro absoluto médio",
    }
    assert novas <= set(nomes)
    expr = {m["name"]: m["expression"] for m in medidas}
    assert "RANKX" in expr["Posição"] and "STDEV.P" in expr["Volatilidade de pontos"]


def test_cobertura_do_intervalo_vira_medida_quando_informada(entradas, tmp_path):  # noqa: F811
    caminho = entradas["modelagem"] / "metadados.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["cobertura_holdout"] = 0.9121
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    destino = tmp_path / "cob"
    _gerar(entradas, destino)
    cob = next(m for m in _fato(destino)["measures"] if m["name"] == "Cobertura do intervalo")
    assert cob["expression"] == "0.9121" and cob["formatString"] == "0.0%"


def test_visuais_referenciam_somente_campos_existentes(saida):
    campos = {
        t["name"]: {c["name"] for c in t["columns"]} | {m["name"] for m in t["measures"]}
        for t in _modelo(saida)["model"]["tables"]
    }
    for nome, visuais in _visuais(saida).items():
        for v in visuais:
            for papel in v["visual"].get("query", {}).get("queryState", {}).values():
                for proj in papel["projections"]:
                    origem = next(iter(proj["field"].values()))
                    entidade = origem["Expression"]["SourceRef"]["Entity"]
                    assert origem["Property"] in campos[entidade], (nome, entidade)


def _escudos_csv(caminho: Path, url: str = "https://upload.wikimedia.org/x/flamengo.png") -> Path:
    linhas = ["equipe,artigo,escudo_url", f"Flamengo,Clube,{url}", "Sem Escudo,Nada,"]
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def test_escudos_entram_na_dimensao_como_imagem(entradas, tmp_path):  # noqa: F811
    destino = _gerar_com(entradas, tmp_path / "esc", escudos=_escudos_csv(tmp_path / "e.csv"))
    dim = next(t for t in _modelo(destino)["model"]["tables"] if t["name"] == "dim_equipes")
    coluna = next(c for c in dim["columns"] if c["name"] == "escudo")
    assert coluna["dataCategory"] == "ImageUrl"
    m = "\n".join(dim["partitions"][0]["source"]["expression"])
    assert "Table.NestedJoin" in m and "JoinKind.LeftOuter" in m and "flamengo.png" in m
    assert "Sem Escudo" not in m
    paginas = _visuais(destino)
    for nome in ("Visão Geral", "Estatística"):
        texto = json.dumps(paginas[nome], ensure_ascii=False)
        assert '"Property": "escudo"' in texto, nome


def test_sem_escudos_nenhuma_tabela_referencia_a_coluna(saida):
    assert '"escudo"' not in json.dumps(_visuais(saida), ensure_ascii=False)


@pytest.mark.parametrize("url", ["http://inseguro/x.png", 'https://x/"quebra.png'])
def test_escudo_com_url_insegura_e_rejeitado(entradas, tmp_path, url):  # noqa: F811
    with pytest.raises(ErroProjeto, match="URL de escudo"):
        _gerar_com(entradas, tmp_path / "s", escudos=_escudos_csv(tmp_path / "e.csv", url))


def test_csv_de_escudos_versionado_cobre_todas_as_equipes():
    import csv

    import pandas as pd

    linhas = list(csv.DictReader((RAIZ / "config" / "escudos.csv").open(encoding="utf-8")))
    equipes = set(
        pd.read_parquet(RAIZ / "data" / "processed" / "dim_equipes.parquet")["nome_padronizado"]
    )
    assert {r["equipe"] for r in linhas} == equipes
    assert all(r["escudo_url"].startswith("https://") for r in linhas)


def _visuais_do_tipo(saida: Path, tipo: str) -> list[dict]:
    return [v for vs in _visuais(saida).values() for v in vs if v["visual"]["visualType"] == tipo]


def test_cartoes_tem_altura_para_o_valor_e_sem_rotulo_repetido(saida):
    for v in _visuais_do_tipo(saida, "card"):
        assert v["position"]["height"] >= 96
        rotulo = v["visual"]["objects"]["categoryLabels"][0]["properties"]["show"]
        assert rotulo["expr"]["Literal"]["Value"] == "false"


def test_segmentacoes_tem_altura_para_o_menu(saida):
    for v in _visuais_do_tipo(saida, "slicer"):
        assert v["position"]["height"] >= 72


def test_barras_de_ranking_ordenadas_do_maior_para_o_menor(saida):
    barras = _visuais_do_tipo(saida, "clusteredBarChart")
    assert barras
    for v in barras:
        ordem = v["visual"]["query"]["sortDefinition"]["sort"][0]
        assert ordem["direction"] == "Descending"


def test_colunas_tem_rotulos_amigaveis(saida):
    texto = json.dumps(_visuais(saida), ensure_ascii=False)
    assert '"displayName": "Equipe"' in texto and '"displayName": "Temporada"' in texto
