"""Testes do relatório Power BI: layout, tema, navegação, filtros, destaques e fonte web."""

import csv
import json
from itertools import combinations
from pathlib import Path

import pandas as pd
import pytest
from test_powerbi import _gerar, _modelo, entradas  # noqa: F401

from evaluation.powerbi import ErroProjeto, gerar_projeto
from evaluation.powerbi_layout import SEM_FOTO

RAIZ = Path(__file__).resolve().parents[2]
TOKENS = RAIZ / "dashboard" / "assets" / "tema_tokens.json"
TEMA = "AlemDoPlacar.Report/StaticResources/RegisteredResources/AlemDoPlacarTheme.json"
PAGINAS = [
    "Visão Geral",
    "Tendências",
    "Estatísticas",
    "Modelos",
    "Previsões",
    "Central de Consulta",
    "Metodologia",
]


def _paginas(saida: Path) -> dict[str, dict]:
    relatorio = saida / "AlemDoPlacar.Report" / "definition" / "pages"
    ordem = json.loads((relatorio / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    paginas = {}
    for ident in ordem:
        pagina = json.loads((relatorio / ident / "page.json").read_text(encoding="utf-8"))
        pagina["visuais"] = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((relatorio / ident / "visuals").glob("*/visual.json"))
        ]
        paginas[pagina["displayName"]] = pagina
    return paginas


def _visuais(saida: Path) -> dict[str, list[dict]]:
    return {nome: p["visuais"] for nome, p in _paginas(saida).items()}


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


def _do_tipo(saida: Path, tipo: str, pagina: str | None = None) -> list[dict]:
    paginas = _visuais(saida)
    fontes = [paginas[pagina]] if pagina else paginas.values()
    return [v for vs in fontes for v in vs if v["visual"]["visualType"] == tipo]


def _texto(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    """Projeto gerado com os dados reais do repositório."""
    return gerar_projeto(
        tmp_path_factory.mktemp("real") / "projeto",
        RAIZ / "data" / "processed",
        RAIZ / "data" / "predictions" / "modelagem",
        RAIZ / "data" / "predictions" / "cientifica",
        RAIZ / "dashboard" / "powerbi" / "template",
        tokens=TOKENS,
        escudos=RAIZ / "config" / "escudos.csv",
        destaques=RAIZ / "config" / "destaques.csv",
    ).parent


@pytest.fixture
def saida(entradas, tmp_path):  # noqa: F811
    destino = tmp_path / "saida"
    _gerar(entradas, destino)
    return destino


# ---------------- estrutura ----------------
def test_sete_paginas_na_ordem_pedida(saida):
    assert list(_visuais(saida)) == PAGINAS


def test_cabecalho_em_faixa_unica_sem_borda_e_rodape_visivel(saida):
    for nome, visuais in _visuais(saida).items():
        tipos = [v["visual"]["visualType"] for v in visuais]
        assert tipos.count("pageNavigator") == 1, nome
        topo = [v for v in visuais if v["position"]["y"] == 0]
        assert len(topo) == 1 and topo[0]["position"]["width"] == 1280, nome
        contexto = topo[0]["visual"]["visualContainerObjects"]
        assert contexto["border"][0]["properties"]["show"]["expr"]["Literal"]["Value"] == "false"
        assert (
            contexto["visualHeader"][0]["properties"]["show"]["expr"]["Literal"]["Value"] == "false"
        )
        assert nome in _texto(topo[0]["visual"]) and "ALÉM DO PLACAR" in _texto(topo[0]["visual"])
        rodape = [v for v in visuais if v["position"]["y"] >= 690]
        assert len(rodape) == 1 and rodape[0]["position"]["height"] >= 24, nome
        assert "OpenFootball" in _texto(rodape[0]["visual"])


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


def test_paginas_de_dados_tem_visuais_de_dados(saida):
    paginas = _visuais(saida)
    for nome in ("Tendências", "Estatísticas", "Modelos", "Previsões"):
        dados = [
            v
            for v in paginas[nome]
            if v["visual"]["visualType"] not in {"textbox", "pageNavigator"}
        ]
        assert len(dados) >= 4, nome


def test_tema_gravado_e_registrado_com_a_paleta_nova(saida):
    tema = json.loads((saida / TEMA).read_text(encoding="utf-8"))
    assert tema["name"] == "AlemDoPlacar" and tema["dataColors"][:3] == [
        "#075e45",
        "#15966a",
        "#f3c84b",
    ]
    fundo = tema["visualStyles"]["page"]["*"]["background"][0]["color"]["solid"]["color"]
    assert fundo == "#f3f5f4"
    rj = json.loads(
        (saida / "AlemDoPlacar.Report/definition/report.json").read_text(encoding="utf-8")
    )
    assert rj["themeCollection"]["customTheme"]["name"] == "AlemDoPlacarTheme.json"


def test_tokens_do_site_alimentam_o_tema(entradas, tmp_path):  # noqa: F811
    destino = _gerar_com(entradas, tmp_path / "com_tokens", tokens=TOKENS)
    tema = json.loads((destino / TEMA).read_text(encoding="utf-8"))
    cores = json.loads(TOKENS.read_text(encoding="utf-8"))["cores"]
    assert (
        tema["dataColors"][0] == cores["serie-1"] and tema["tableAccent"] == cores["cor-destaque"]
    )


def test_tokens_invalidos_geram_erro_claro(entradas, tmp_path):  # noqa: F811
    ruim = tmp_path / "t.json"
    ruim.write_text('{"x": 1}', encoding="utf-8")
    with pytest.raises(ErroProjeto, match="tokens inválidos"):
        _gerar_com(entradas, tmp_path / "s", tokens=ruim)


# ---------------- filtros e consistência ----------------
def _filtro_padrao(slicer: dict):
    geral = slicer["visual"].get("objects", {}).get("general")
    if not geral:
        return None
    cond = geral[0]["properties"]["filter"]["filter"]["Where"][0]["Condition"]["In"]
    return cond["Values"][0][0]["Literal"]["Value"]


def test_temporada_padrao_e_selecao_unica_onde_ha_ranking(saida):
    for pagina in ("Visão Geral", "Estatísticas"):
        slicers = _do_tipo(saida, "slicer", pagina)
        temporada = [s for s in slicers if '"Property": "ano"' in _texto(s["visual"]["query"])]
        assert temporada and _filtro_padrao(temporada[0]) == "2025L", pagina
        assert '"singleSelect"' in _texto(temporada[0]["visual"]["objects"])


def test_flamengo_como_equipe_inicial_em_tendencias_e_previsoes(saida):
    for pagina in ("Tendências", "Previsões"):
        slicers = _do_tipo(saida, "slicer", pagina)
        equipe = [s for s in slicers if "nome_padronizado" in _texto(s["visual"]["query"])]
        assert equipe and _filtro_padrao(equipe[0]) == "'Flamengo'", pagina


def test_equipe_de_tendencias_nao_filtra_matriz_nem_ranking(saida):
    pagina = _paginas(saida)["Tendências"]
    interacoes = pagina["visualInteractions"]
    nomes = {v["visual"]["visualType"]: v["name"] for v in pagina["visuais"]}
    alvos = {i["target"] for i in interacoes if i["type"] == "NoFilter"}
    assert {nomes["pivotTable"], nomes["clusteredBarChart"]} <= alvos


def _medidas(saida: Path) -> dict[str, dict]:
    fato = next(
        t for t in _modelo(saida)["model"]["tables"] if t["name"] == "fato_desempenho_equipes"
    )
    return {m["name"]: m for m in fato["measures"]}


def test_classificacao_nunca_mistura_temporadas(saida):
    medidas = _medidas(saida)
    for nome in (
        "Pontos (temporada)",
        "Jogos (temporada)",
        "Saldo (temporada)",
        "Aproveitamento (temporada)",
        "Posição",
    ):
        assert "HASONEVALUE(dim_temporadas[ano])" in medidas[nome]["expression"], nome
    assert "Selecione uma única temporada" in medidas["Aviso temporada"]["expression"]


def test_posicao_usa_desempate_e_ignora_equipes_sem_jogos(saida):
    expr = _medidas(saida)["Posição"]["expression"]
    assert "RANKX(FILTER(ALL(dim_equipes[nome_padronizado]), [Observações de equipe] > 0)" in expr
    ordem = [expr.index(t) for t in ("[Pontos totais]", "[Vitórias]", "[Saldo de gols]", "[Gols]")]
    assert ordem == sorted(ordem) and "Skip" in expr


def test_zona_por_posicao(saida):
    expr = _medidas(saida)["Zona"]["expression"]
    for trecho in (
        'p <= 4, "Libertadores"',
        'p <= 6, "Pré-Libertadores"',
        'p <= 12, "Sul-Americana"',
        'p >= 17, "Rebaixamento"',
    ):
        assert trecho in expr


def test_resultados_como_categorias_e_percentual(saida):
    fato = next(
        t for t in _modelo(saida)["model"]["tables"] if t["name"] == "fato_desempenho_equipes"
    )
    m = "\n".join(fato["partitions"][0]["source"]["expression"])
    assert '"Vitória"' in m and '"Empate"' in m and '"Derrota"' in m
    assert any(
        c["name"] == "resultado_equipe" and c["dataType"] == "string" for c in fato["columns"]
    )
    grafico = next(
        v
        for v in _do_tipo(saida, "clusteredColumnChart", "Estatísticas")
        if "resultado_equipe" in _texto(v)
    )
    assert "% dos resultados" in _texto(grafico) and '"pontos"' not in _texto(
        grafico["visual"]["query"]
    )


def test_pontos_por_jogo_com_media_do_campeonato(saida):
    combo = _do_tipo(saida, "lineClusteredColumnComboChart", "Estatísticas")[0]
    estado = combo["visual"]["query"]["queryState"]
    assert "Pontos por jogo" in _texto(estado["Y"]) and "Média do campeonato" in _texto(
        estado["Y2"]
    )
    medidas = _medidas(saida)
    assert (
        medidas["Pontos por jogo"]["expression"]
        == "DIVIDE([Pontos totais],[Observações de equipe])"
    )
    assert "ALL(dim_equipes)" in medidas["Média do campeonato"]["expression"]


# ---------------- modelos e previsões ----------------
def test_modelos_com_nomes_amigaveis(real):
    saida = real
    tabelas = {t["name"]: t for t in _modelo(saida)["model"]["tables"]}
    comp = "\n".join(tabelas["comparacao_modelos"]["partitions"][0]["source"]["expression"])
    assert "Regressão Ridge" in comp and "Média dos últimos 5 jogos (referência)" in comp
    assert (
        'selecionado = "Sim"' in comp
        and "mae_teste = null" not in comp.split("M01_ridge")[1].split("]")[0]
    )
    imp = "\n".join(tabelas["importancias"]["partitions"][0]["source"]["expression"])
    assert 'variavel = "Média de pontos nos últimos 5 jogos"' in imp
    texto = _texto(_visuais(saida)["Modelos"])
    assert "comparacao_modelos" in texto and '"Property": "variavel"' in texto
    assert '"Property": "atributo"' not in texto


def test_ranking_de_erro_do_menor_para_o_maior(saida):
    barras = _do_tipo(saida, "clusteredBarChart", "Modelos")
    erro = [b for b in barras if "comparacao_modelos" in _texto(b)]
    assert len(erro) == 2
    for b in erro:
        assert b["visual"]["query"]["sortDefinition"]["sort"][0]["direction"] == "Ascending"


def test_rankings_de_equipes_do_maior_para_o_menor(saida):
    for pagina in ("Tendências",):
        for b in _do_tipo(saida, "clusteredBarChart", pagina):
            assert b["visual"]["query"]["sortDefinition"]["sort"][0]["direction"] == "Descending"


def test_limites_da_previsao_tracejados_e_cinza(saida):
    linha = _do_tipo(saida, "lineChart", "Previsões")[0]
    estilos = {
        s["selector"]["metadata"]: s["properties"] for s in linha["visual"]["objects"]["lineStyles"]
    }
    inferior = estilos["fato_desempenho_equipes.Limite inferior"]
    assert inferior["lineStyle"]["expr"]["Literal"]["Value"] == "'dashed'"
    assert (
        estilos["fato_desempenho_equipes.Média prevista"]["strokeWidth"]["expr"]["Literal"]["Value"]
        == "3D"
    )
    assert "Os resultados reais podem ser diferentes" in _texto(_visuais(saida)["Previsões"])


# ---------------- central e links ----------------
def test_central_sem_url_nao_inventa_link(saida):
    texto = _texto(_visuais(saida)["Central de Consulta"]) + _texto(_visuais(saida)["Metodologia"])
    assert '"url"' not in texto and "após a publicação" in texto


def test_central_e_repositorio_com_url_informada(entradas, tmp_path):  # noqa: F811
    destino = _gerar_com(
        entradas,
        tmp_path / "url",
        url_central="https://u.github.io/alem/consulta.html",
        url_repositorio="https://github.com/u/alem",
    )
    texto = _texto(_visuais(destino))
    assert '"url": "https://u.github.io/alem/consulta.html"' in texto
    assert '"url": "https://github.com/u/alem"' in texto


@pytest.mark.parametrize(
    "kwargs", [{"url_central": "http://x"}, {"url_repositorio": "javascript:alert(1)"}]
)
def test_urls_inseguras_rejeitadas(entradas, tmp_path, kwargs):  # noqa: F811
    with pytest.raises(ErroProjeto, match="https"):
        _gerar_com(entradas, tmp_path / "s", **kwargs)


# ---------------- fonte web ----------------
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
    for nome in ("dim_equipes", "fato_desempenho_equipes", "analitico", "previsoes"):
        assert "File.Contents" not in tabelas[nome] and "C:\\" not in tabelas[nome]
    assert "resultado_equipe" in tabelas["fato_desempenho_equipes"]


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


# ---------------- medidas e referências ----------------
def test_medidas_tem_formato_e_nomes_unicos(saida):
    fato = next(
        t for t in _modelo(saida)["model"]["tables"] if t["name"] == "fato_desempenho_equipes"
    )
    nomes = [m["name"] for m in fato["measures"]]
    assert len(nomes) == len(set(nomes))
    medidas = _medidas(saida)
    assert medidas["Aproveitamento (temporada)"]["formatString"] == "0.0%"
    assert medidas["% dos resultados"]["formatString"] == "0.0%"
    assert "formatString" not in medidas["Zona"]


def test_cobertura_do_intervalo_vira_medida_quando_informada(entradas, tmp_path):  # noqa: F811
    caminho = entradas["modelagem"] / "metadados.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["cobertura_holdout"] = 0.9121
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    destino = tmp_path / "cob"
    _gerar(entradas, destino)
    cob = _medidas(destino)["Cobertura do intervalo"]
    assert cob["expression"] == "0.9121" and cob["formatString"] == "0.0%"
    assert "91,2%" in _texto(_visuais(destino)["Previsões"])


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


def test_cartoes_sem_rotulo_repetido_e_segmentacoes_altas(saida):
    for v in _do_tipo(saida, "card"):
        assert v["position"]["height"] >= 72
        rotulo = v["visual"]["objects"]["categoryLabels"][0]["properties"]["show"]
        assert rotulo["expr"]["Literal"]["Value"] == "false"
    for v in _do_tipo(saida, "slicer"):
        assert v["position"]["height"] >= 72


def test_colunas_tem_rotulos_amigaveis(saida):
    texto = _texto(_visuais(saida))
    assert '"displayName": "Equipe"' in texto and '"displayName": "Temporada"' in texto
    assert '"displayName": "Pos."' in texto and '"displayName": "Aprov."' in texto


# ---------------- escudos e destaques ----------------
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
    assert "Table.NestedJoin" in m and "flamengo.png" in m and "Sem Escudo" not in m
    for nome in ("Visão Geral", "Estatísticas"):
        assert '"Property": "escudo"' in _texto(_visuais(destino)[nome]), nome


@pytest.mark.parametrize("url", ["http://inseguro/x.png", 'https://x/"quebra.png'])
def test_escudo_com_url_insegura_e_rejeitado(entradas, tmp_path, url):  # noqa: F811
    with pytest.raises(ErroProjeto, match="URL de escudo"):
        _gerar_com(entradas, tmp_path / "s", escudos=_escudos_csv(tmp_path / "e.csv", url))


def test_destaques_reais_com_projeto_completo(real):
    """Confere os destaques de 2025 e 2023 com os dados reais."""
    destino = real
    modelo = _modelo(destino)["model"]
    tabelas = {
        t["name"]: "\n".join(t["partitions"][0]["source"]["expression"]) for t in modelo["tables"]
    }
    assert 'ano = 2025, nome = "Kaio Jorge"' in tabelas["destaque_artilheiro"]
    assert "21 gols" in tabelas["destaque_artilheiro"]
    assert (
        'ano = 2025, nome = "Flamengo"' in tabelas["destaque_ataque"]
        and "78 gols" in tabelas["destaque_ataque"]
    )
    assert 'ano = 2023, nome = "Não informado na fonte"' in tabelas["destaque_craque"]
    assert "%23E3F1EB" in tabelas["destaque_goleiro"]  # silhueta para quem não tem foto livre
    rel = {(r["fromTable"], r["toTable"]) for r in modelo["relationships"]}
    assert ("destaque_artilheiro", "dim_temporadas") in rel and len(modelo["relationships"]) == 11
    visuais = _texto(_visuais(destino)["Visão Geral"])
    for tab in ("destaque_artilheiro", "destaque_craque", "destaque_goleiro", "destaque_ataque"):
        assert tab in visuais


def test_csvs_versionados_cobrem_equipes_e_tem_fontes():
    escudos = list(csv.DictReader((RAIZ / "config" / "escudos.csv").open(encoding="utf-8")))
    equipes = set(
        pd.read_parquet(RAIZ / "data" / "processed" / "dim_equipes.parquet")["nome_padronizado"]
    )
    assert {r["equipe"] for r in escudos} == equipes
    destaques = list(csv.DictReader((RAIZ / "config" / "destaques.csv").open(encoding="utf-8")))
    for r in destaques:
        assert r["fonte"].startswith("https://pt.wikipedia.org/wiki/")
        assert r["clube"] in equipes, r
        if r["foto_url"]:
            assert r["foto_url"].startswith("https://") and r["foto_licenca"], r
    assert SEM_FOTO.startswith("data:image/svg+xml")
