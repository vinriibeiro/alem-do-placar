"""Testes do catálogo, da camada LLM (cliente simulado), dos limites e da segurança (T009 v2)."""

import json
from itertools import permutations
from pathlib import Path
from types import SimpleNamespace

import anthropic
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.assistant import BaseConsultas
from api.catalogo import Catalogo, ConsultaErro
from api.llm import MODELO_PADRAO, definir_ferramentas

try:
    import httpx2 as httpx
except ImportError:  # pragma: no cover
    import httpx

EQUIPES = ["Alfa FC", "Beta FC", "Gama EC", "Delta SC"]


def _partidas() -> list[dict]:
    """Turno e returno entre 4 equipes em 2024 e 2025, com placares determinísticos."""
    out = []
    dia = 0
    for ano in (2024, 2025):
        for i, j in permutations(range(4), 2):
            gh, ga = (i + j + ano) % 4, (i * j) % 3
            data = pd.Timestamp(f"{ano}-03-01") + pd.Timedelta(days=dia % 200)
            dia += 1
            out.append(
                {
                    "ano": ano,
                    "h": EQUIPES[i],
                    "a": EQUIPES[j],
                    "gh": gh,
                    "ga": ga,
                    "data": data,
                    "id": f"{ano}{i}{j}",
                }
            )
    return out


def _pontos(g1: int, g2: int) -> int:
    return 3 if g1 > g2 else 1 if g1 == g2 else 0


def _historico() -> pd.DataFrame:
    linhas = []
    for m in _partidas():
        for eq, adv, gp, gc, mando in (
            (m["h"], m["a"], m["gh"], m["ga"], 1),
            (m["a"], m["h"], m["ga"], m["gh"], 0),
        ):
            linhas.append(
                {
                    "partida_id": m["id"],
                    "equipe": eq,
                    "adversario": adv,
                    "data_referencia": m["data"],
                    "temporada": m["ano"],
                    "mando": mando,
                    "pontos": _pontos(gp, gc),
                    "gols_pro": gp,
                    "gols_contra": gc,
                    "media_pontos_5": 1.0,
                    "desvio_pontos_5": 0.5,
                }
            )
    return pd.DataFrame(linhas)


def _raiz(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    for sub in ("processed", "predictions/modelagem", "predictions/cientifica"):
        (d / sub).mkdir(parents=True)
    _historico().to_parquet(d / "processed" / "dataset_analitico.parquet", index=False)
    pd.DataFrame(
        {
            "equipe": ["Alfa FC"],
            "data_referencia": pd.to_datetime(["2025-09-08"]),
            "previsao": [2.4],
            "limite_inferior": [1.2],
            "limite_superior": [3.0],
            "observado": [2.6],
        }
    ).to_parquet(d / "predictions/modelagem/previsoes.parquet", index=False)
    meta = {
        "modelo_selecionado": "M01_ridge",
        "versao": "T006-1.0",
        "ano_holdout": 2025,
        "corte_treino": "2025-03-29",
    }
    (d / "predictions/modelagem/metadados.json").write_text(json.dumps(meta), encoding="utf-8")
    pd.DataFrame(
        {"atributo": ["media_pontos_5"], "delta_mae_media": [0.05], "delta_mae_desvio": [0.01]}
    ).to_csv(d / "predictions/cientifica/importancias.csv", index=False)
    return tmp_path


@pytest.fixture
def raiz(tmp_path):
    return _raiz(tmp_path)


@pytest.fixture
def cat():
    return Catalogo(_historico())


# ---------------- catálogo ----------------
def test_classificacao_confere_com_contagem_independente(cat):
    esperado = {e: 0 for e in EQUIPES}
    for m in _partidas():
        if m["ano"] == 2025:
            esperado[m["h"]] += _pontos(m["gh"], m["ga"])
            esperado[m["a"]] += _pontos(m["ga"], m["gh"])
    r = cat.classificacao(2025)
    assert {d["equipe"]: d["pontos"] for d in r["dados"]} == esperado
    assert [d["posicao"] for d in r["dados"]] == [1, 2, 3, 4]
    assert r["dados"][0]["pontos"] == max(esperado.values())
    assert "2025" in r["periodo"] and r["fonte"]
    assert r["dados"][0]["jogos"] == 6


def test_classificacao_top_e_ano_padrao(cat):
    assert len(cat.classificacao(None, 2)["dados"]) == 2
    assert "2025" in cat.classificacao()["texto_base"]


def test_parametros_invalidos_geram_erro_seguro(cat):
    with pytest.raises(ConsultaErro):
        cat.classificacao(1999)
    with pytest.raises(ConsultaErro):
        cat.resumo_equipe("Time Que Nao Existe")
    with pytest.raises(ConsultaErro):
        cat.comparar_equipes("Alfa FC", "Alfa FC")
    with pytest.raises(ConsultaErro):
        cat.sequencias("tipo_invalido")
    with pytest.raises(ConsultaErro):
        cat.ranking("inexistente")


def test_resolucao_de_equipe_por_nome_parcial_e_ambiguidade(cat):
    assert cat.equipe("alfa") == "Alfa FC"
    assert cat.equipe("DELTA SC") == "Delta SC"
    with pytest.raises(ConsultaErro):
        cat.equipe("FC")  # Alfa FC e Beta FC


def test_resumo_historico_e_por_temporada(cat):
    hist = cat.resumo_equipe("Alfa FC")
    assert len(hist["dados"]) == 2
    assert "12 jogos" in hist["texto_base"]
    ano = cat.resumo_equipe("Alfa FC", 2024)
    assert len(ano["dados"]) == 1
    assert ano["dados"][0]["jogos"] == 6
    assert ano["dados"][0]["equipe"] == "Alfa FC"
    assert "2024" in ano["texto_base"]


def test_confronto_direto_tem_ida_e_volta(cat):
    r = cat.confronto_direto("Alfa FC", "Beta FC")
    assert len(r["dados"]) == 4  # 2 por temporada
    assert {d["mandante"] for d in r["dados"]} == {"Alfa FC", "Beta FC"}
    soma = sum(1 for m in _partidas() if {m["h"], m["a"]} == {"Alfa FC", "Beta FC"})
    assert soma == 4


def test_mando_gols_e_ranking(cat):
    m = cat.mando()
    assert {d["mando"] for d in m["dados"]} == {"mandante", "visitante"}
    g = cat.gols(2025)
    total = [x["gh"] + x["ga"] for x in _partidas() if x["ano"] == 2025]
    assert g["dados"][0]["gols_por_jogo"] == round(sum(total) / len(total), 2)
    rk = cat.ranking("ataque", 2025, 2)
    assert len(rk["dados"]) == 2 and rk["dados"][0]["valor"] >= rk["dados"][1]["valor"]
    assert (
        cat.ranking("defesa", 2025)["dados"][0]["valor"]
        <= cat.ranking("defesa", 2025)["dados"][-1]["valor"]
    )


def test_sequencias(cat):
    r = cat.sequencias("invicta", "Alfa FC", 2025)
    assert len(r["dados"]) == 1 and r["dados"][0]["maior_sequencia"] >= 0
    todas = cat.sequencias("derrotas")
    assert todas["dados"][0]["maior_sequencia"] >= todas["dados"][-1]["maior_sequencia"]


def test_catalogo_nao_depende_de_ordem_do_dataframe():
    h = _historico().sample(frac=1, random_state=1).reset_index(drop=True)
    a = Catalogo(h).classificacao(2025)["dados"]
    b = Catalogo(_historico()).classificacao(2025)["dados"]
    assert a == b


# ---------------- roteamento determinístico ----------------
@pytest.mark.parametrize(
    "pergunta,trecho",
    [
        ("Qual foi a classificação de 2025?", "Classificação calculada de 2025"),
        ("Compare Alfa FC e Beta FC em 2025", "Em 2025"),
        ("Histórico de confrontos entre Alfa FC e Beta FC", "Confrontos entre"),
        ("Como o Alfa FC vai como mandante e visitante?", "mandante"),
        ("Quais foram as maiores goleadas?", "goleadas"),
        ("Maior sequência de derrotas do Gama EC", "derrotas"),
        ("Qual a melhor defesa de 2025?", "gols sofridos"),
        ("Resumo do Delta SC em 2025", "Delta SC em 2025"),
    ],
)
def test_roteamento_deterministico_do_catalogo(raiz, pergunta, trecho):
    r = BaseConsultas(raiz).responder(pergunta)
    assert r["status"] == "ok", r["texto"]
    assert trecho.lower() in r["texto"].lower()
    assert r["fonte"] and r["periodo"]


def test_fora_de_escopo_continua_recusando(raiz):
    r = BaseConsultas(raiz).responder("Qual o clima em Curitiba?")
    assert r["status"] == "fora_escopo" and "Não é possível calcular" in r["texto"]


def test_ano_inexistente_nao_e_substituido(raiz):
    r = BaseConsultas(raiz).responder("Qual a classificação de 2031?")
    assert r["status"] != "ok" and "2031" in r["texto"]


# ---------------- LLM (cliente simulado) ----------------
def _tool(nome, entrada, id_="tu_1"):
    return SimpleNamespace(type="tool_use", id=id_, name=nome, input=entrada)


def _texto(t):
    return SimpleNamespace(type="text", text=t)


class ClienteFalso:
    def __init__(self, *respostas, erro=None):
        self.respostas = list(respostas)
        self.chamadas = []
        self.erro = erro
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.chamadas.append(kw)
        if self.erro:
            raise self.erro
        blocos, parada = self.respostas.pop(0)
        return SimpleNamespace(content=blocos, stop_reason=parada)


def _app(raiz, cliente=None, **env):
    return TestClient(create_app(raiz, cliente_llm=cliente, env=env), base_url="http://127.0.0.1")


def test_fluxo_llm_com_ferramenta_e_resposta_fundamentada(raiz):
    cli = ClienteFalso(
        ([_tool("classificacao", {"ano": 2025, "top": 2})], "tool_use"),
        ([_texto("Em 2025 a equipe líder fez mais pontos.")], "end_turn"),
    )
    r = _app(raiz, cli).post("/api/pergunta", json={"pergunta": "Quem liderou 2025?"})
    j = r.json()
    assert r.status_code == 200 and j["modo"] == "llm" and j["status"] == "ok"
    assert j["consultas_usadas"] == ["classificacao"]
    assert len(j["dados"]) == 2 and j["fonte"] and "2025" in j["periodo"]
    assert any("IA" in x for x in j["limitacoes"])
    primeira = cli.chamadas[0]
    assert primeira["model"] == MODELO_PADRAO == "claude-opus-5-5"
    assert primeira["output_config"] == {"effort": "low"}
    assert primeira["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert all(
        t["strict"] and t["input_schema"]["additionalProperties"] is False
        for t in primeira["tools"]
    )
    segunda = cli.chamadas[1]["messages"]
    assert (
        segunda[-1]["content"][0]["type"] == "tool_result"
        and not segunda[-1]["content"][0]["is_error"]
    )


def test_ferramentas_cobrem_catalogo_e_modelo():
    nomes = {t["name"] for t in definir_ferramentas()}
    assert {
        "classificacao",
        "confronto_direto",
        "ranking",
        "sequencias",
        "consulta_modelo",
    } <= nomes
    for t in definir_ferramentas():
        assert set(t["input_schema"]["required"]) == set(t["input_schema"]["properties"])


def test_llm_sem_ferramenta_descarta_texto_e_nao_inventa(raiz):
    cli = ClienteFalso(([_texto("O Alfa FC vai ganhar a Libertadores com 99 pontos!")], "end_turn"))
    j = (
        _app(raiz, cli)
        .post("/api/pergunta", json={"pergunta": "Quem ganha a Libertadores?"})
        .json()
    )
    assert j["status"] == "fora_escopo" and "99" not in j["texto"]
    assert "Não é possível calcular" in j["texto"] and j["dados"] == []


def test_parametro_nao_autorizado_e_erro_de_ferramenta(raiz):
    cli = ClienteFalso(
        ([_tool("classificacao", {"ano": 2025, "sql": "DROP TABLE x"})], "tool_use"),
        ([_texto("Não consegui consultar.")], "end_turn"),
    )
    j = _app(raiz, cli).post("/api/pergunta", json={"pergunta": "Mostre a tabela"}).json()
    ret = cli.chamadas[1]["messages"][-1]["content"][0]
    assert ret["is_error"] is True
    assert j["status"] == "fora_escopo" and j["consultas_usadas"] == []


def test_ferramenta_desconhecida_e_bloqueada(raiz):
    cli = ClienteFalso(
        ([_tool("executar_sql", {"q": "select 1"})], "tool_use"), ([_texto("x")], "end_turn")
    )
    _app(raiz, cli).post("/api/pergunta", json={"pergunta": "rode um sql"})
    assert cli.chamadas[1]["messages"][-1]["content"][0]["is_error"] is True


def test_consulta_modelo_via_llm(raiz):
    cli = ClienteFalso(
        (
            [
                _tool(
                    "consulta_modelo",
                    {"intencao": "erro", "equipe": None, "ano": None, "queda": False},
                )
            ],
            "tool_use",
        ),
        ([_texto("O erro médio foi de cerca de 0,2 ponto.")], "end_turn"),
    )
    j = _app(raiz, cli).post("/api/pergunta", json={"pergunta": "Qual o erro do modelo?"}).json()
    assert j["consultas_usadas"] == ["consulta_modelo"] and j["modelo"] == "M01_ridge"


def test_filtros_da_interface_vao_na_mensagem(raiz):
    cli = ClienteFalso(([_texto("ok")], "end_turn"))
    _app(raiz, cli).post(
        "/api/pergunta", json={"pergunta": "Resumo", "ano": 2025, "equipe": "Alfa FC"}
    )
    msg = cli.chamadas[0]["messages"][0]["content"]
    assert "2025" in msg and "Alfa FC" in msg


@pytest.mark.parametrize(
    "erro",
    [
        anthropic.RateLimitError(
            "x", response=httpx.Response(429, request=httpx.Request("POST", "http://x")), body=None
        ),
        anthropic.APIConnectionError(request=httpx.Request("POST", "http://x")),
        anthropic.InternalServerError(
            "x", response=httpx.Response(500, request=httpx.Request("POST", "http://x")), body=None
        ),
    ],
)
def test_falha_do_llm_cai_no_modo_deterministico(raiz, erro):
    j = (
        _app(raiz, ClienteFalso(erro=erro))
        .post("/api/pergunta", json={"pergunta": "Qual foi a classificação de 2025?"})
        .json()
    )
    assert j["modo"] == "deterministico" and j["status"] == "ok"
    assert "determinístico" in j["limitacoes"][0]


def test_recusa_do_modelo_cai_no_fallback(raiz):
    cli = ClienteFalso(([], "refusal"))
    j = (
        _app(raiz, cli)
        .post("/api/pergunta", json={"pergunta": "Qual foi a classificação de 2025?"})
        .json()
    )
    assert j["modo"] == "deterministico"


def test_sem_chave_usa_modo_deterministico(raiz):
    c = _app(raiz)
    j = c.post("/api/pergunta", json={"pergunta": "Qual foi a classificação de 2025?"}).json()
    assert j["modo"] == "deterministico" and c.get("/api/contexto").json()["llm_ativo"] is False


# ---------------- limites e segurança ----------------
def test_limite_diario_do_llm_degrada_para_deterministico(raiz):
    cli = ClienteFalso(
        ([_texto("Resposta IA")], "end_turn"), ([_texto("Resposta IA 2")], "end_turn")
    )
    c = _app(raiz, cli, LLM_DAILY_LIMIT="1")
    p = {"pergunta": "Qual foi a classificação de 2025?"}
    c.post("/api/pergunta", json=p)
    j = c.post("/api/pergunta", json=p).json()
    assert j["modo"] == "deterministico" and "Limite diário" in j["limitacoes"][0]
    assert len(cli.chamadas) == 1


def test_limite_de_taxa_por_ip_retorna_429(raiz):
    c = _app(raiz, None, RATE_LIMIT_PER_MIN="2")
    p = {"pergunta": "Qual foi a classificação de 2025?"}
    assert c.post("/api/pergunta", json=p).status_code == 200
    assert c.post("/api/pergunta", json=p).status_code == 200
    r = c.post("/api/pergunta", json=p)
    assert r.status_code == 429 and r.headers["retry-after"] == "60"


def test_corpo_grande_e_rejeitado(raiz):
    r = _app(raiz).post(
        "/api/pergunta", content=b"x" * 5000, headers={"content-type": "application/json"}
    )
    assert r.status_code == 413


def test_hosts_e_origens_configuraveis_por_ambiente(raiz):
    app = create_app(raiz, env={"ALLOWED_HOSTS": "meu.app", "ALLOWED_ORIGINS": "https://outro.app"})
    c = TestClient(app, base_url="https://meu.app")
    p = {"pergunta": "Qual foi a classificação de 2025?"}
    assert c.post("/api/pergunta", json=p, headers={"Origin": "https://meu.app"}).status_code == 200
    assert (
        c.post("/api/pergunta", json=p, headers={"Origin": "https://outro.app"}).status_code == 200
    )
    assert (
        c.post("/api/pergunta", json=p, headers={"Origin": "https://evil.com"}).status_code == 403
    )
    assert TestClient(app, base_url="https://evil.com").get("/health").status_code == 400


def test_padrao_continua_somente_local(raiz):
    c = TestClient(create_app(raiz, env={}), base_url="http://meu.app")
    assert c.get("/health").status_code == 400


def test_contexto_nao_vaza_chave_nem_prompt(raiz):
    c = _app(raiz, None, LLM_API_KEY="sk-ant-segredo-123")
    corpo = c.get("/api/contexto").text + c.get("/api/sugestoes").text
    assert "sk-ant" not in corpo and "Regras obrigatórias" not in corpo
    assert c.get("/api/contexto").json()["llm_ativo"] is True


def test_sugestoes_e_temas(raiz):
    c = _app(raiz)
    s = c.get("/api/sugestoes").json()["sugestoes"]
    assert len(s) == 8 and all(isinstance(x, str) for x in s)
    assert len(c.get("/api/contexto").json()["temas"]) >= 8


def test_headers_de_seguranca(raiz):
    h = _app(raiz).get("/health").headers
    assert h["x-content-type-options"] == "nosniff" and "referrer-policy" in h
