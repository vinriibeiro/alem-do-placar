"""Testes da Central de Consulta: dados públicos gerados e motor JavaScript (via Node)."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from api.central import montar

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def dados():
    return montar(RAIZ)


def test_arquivos_e_tamanho_razoavel(dados):
    assert set(dados) >= {
        "partidas",
        "modelo",
        "destaques",
        "escudos",
        "conhecimento",
        "contexto",
        "sugestoes",
        "config",
    }
    total = sum(len(json.dumps(v, ensure_ascii=False)) for v in dados.values())
    assert total < 400_000  # carregamento rápido no navegador


def test_partidas_completas_e_consistentes(dados):
    p = dados["partidas"]
    assert len(p["partidas"]) == 3040
    por_ano = {}
    por_rodada = {}
    for ano, _data, m, v, gm, gv, rodada in p["partidas"]:
        assert m != v and gm >= 0 and gv >= 0
        assert rodada is not None and 1 <= rodada <= 38
        por_ano[ano] = por_ano.get(ano, 0) + 1
        por_rodada[(ano, rodada)] = por_rodada.get((ano, rodada), 0) + 1
    assert set(por_ano.values()) == {380}
    assert set(por_rodada.values()) == {10}  # 10 jogos por rodada em todas as temporadas
    assert dados["contexto"]["partidas"] == 3040 and dados["contexto"]["temporadas"] == 8


def test_base_de_conhecimento_preenchida_com_fatos_reais(dados):
    itens = dados["conhecimento"]
    ids = [i["id"] for i in itens]
    assert len(ids) == len(set(ids)) and len(ids) >= 25
    for item in itens:
        assert item["perguntas"] and item["resposta"] and item["fonte"]
        assert not re.search(r"\{\w+\}", item["resposta"]), item["id"]
        for rel in item.get("relacionados", []):
            assert rel in ids, (item["id"], rel)
    mae = next(i for i in itens if i["id"] == "mae")["resposta"]
    assert f"{dados['modelo']['mae_teste']:.3f}".replace(".", ",") in mae
    assert "3.040" in next(i for i in itens if i["id"] == "dados")["resposta"]


def test_modelo_com_nomes_amigaveis_e_selecionado(dados):
    m = dados["modelo"]
    nomes = {c["nome"] for c in m["comparacao"]}
    assert "Regressão Ridge" in nomes and all("_" not in n for n in nomes)
    assert [c["codigo"] for c in m["comparacao"] if c["selecionado"]] == ["M01_ridge"]
    assert m["importancias"][0]["nome"] == "Saldo médio de gols nos últimos 5 jogos"
    assert len(m["previsoes"]) == 660


def test_fato_ausente_na_base_gera_erro(tmp_path):
    for sub in ("config",):
        shutil.copytree(RAIZ / sub, tmp_path / sub)
    shutil.copytree(RAIZ / "data", tmp_path / "data")
    caminho = tmp_path / "config" / "central_conhecimento.yaml"
    caminho.write_text(
        caminho.read_text(encoding="utf-8").replace(
            "o MAE foi {mae_teste}", "o MAE foi {inexistente}", 1
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="fatos ausentes"):
        montar(tmp_path)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js não instalado")
def test_motor_javascript_com_node(dados, tmp_path):
    for nome, valor in dados.items():
        (tmp_path / f"{nome}.json").write_text(
            json.dumps(valor, ensure_ascii=False), encoding="utf-8"
        )
    proc = subprocess.run(
        ["node", "--test", *map(str, sorted((RAIZ / "tests" / "js").glob("*.test.mjs")))],
        env={**__import__("os").environ, "CENTRAL_DADOS": str(tmp_path)},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    sys.stdout.write(proc.stdout[-2000:])
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]
