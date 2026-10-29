import socket
from pathlib import Path

import pytest

from ingestion.coleta import ColetaErro
from ingestion.source_catalog import CatalogoFontes, carregar_catalogo, construir_catalogo
from processing.consultas import executar_consulta
from processing.pipeline import ConfiguracaoPipeline, carregar_configuracao, executar_pipeline
from validation.integridade import IntegridadeErro

RAIZ = Path(__file__).resolve().parents[2]
FORMATOS = ("%Y-%m-%d", "%d/%m/%Y")
TABELAS = ("dim_equipes", "dim_temporadas", "fato_partidas", "fato_desempenho_equipes")

MAPEAMENTO = {
    "partida_id": "id",
    "data_partida": "data",
    "temporada": "temporada",
    "competicao": "competicao",
    "equipe_mandante": "mandante",
    "equipe_visitante": "visitante",
    "gols_mandante": "gols_m",
    "gols_visitante": "gols_v",
    "resultado": "resultado_fonte",
    "rodada": "rodada",
    "finalizacoes": "nao_usado",
    "finalizacoes_no_alvo": "nao_usado",
    "posse_de_bola": "nao_usado",
    "cartoes": "nao_usado",
    "escanteios": "nao_usado",
    "xg": "nao_usado",
    "dias_descanso": "nao_usado",
    "outras_estatisticas": "nao_usado",
}

CSV_VALIDO = (
    "id,data,temporada,competicao,mandante,visitante,gols_m,gols_v,rodada\n"
    "1,2024-05-04,2024,Brasileirão,Flamengo,Atlético-MG,2,1,1\n"
    "2,04/05/2024,2024,Brasileirão,Atlético MG,Flamengo,0,0,1\n"
    "3,11/05/2024,2024,Brasileirão,Grêmio,Palmeiras,1,3,2\n"
)


@pytest.fixture(autouse=True)
def _bloquear_rede(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("rede não permitida em teste")

    monkeypatch.setattr(socket, "socket", proibido)
    monkeypatch.setattr(socket, "create_connection", proibido)
    monkeypatch.setattr(socket, "getaddrinfo", proibido)


def _catalogo(selecionada: bool = True, mapeamento: dict | None = None) -> CatalogoFontes:
    fonte = {
        "id": "fonte_teste",
        "nome": "Fonte sintética",
        "url": "https://exemplo.invalid/fonte",
        "licenca": "licença de teste",
        "status_licenca": "verificada" if selecionada else "pendente_verificacao",
        "cobertura_brasileirao": "sintética",
        "temporadas": "sintética",
        "campos_essenciais": ["id"],
        "campos_complementares": [],
        "riscos": ["dados sintéticos para teste"],
        "decisao": "selecionada" if selecionada else "pendente",
        "mapeamento": dict(mapeamento or MAPEAMENTO),
    }
    if selecionada:
        fonte.update(
            url_termos="https://exemplo.invalid/termos",
            data_verificacao="2026-10-29",
            verificador="teste automatizado",
            justificativa="teste automatizado",
        )
    return construir_catalogo({"catalogo": {"versao": "0.0.0-teste"}, "fontes": [fonte]})


def _config(base: Path) -> ConfiguracaoPipeline:
    return ConfiguracaoPipeline(
        formatos_data=FORMATOS,
        pasta_raw=base / "raw",
        pasta_processed=base / "processed",
    )


def _origem(tmp_path: Path, conteudo: str = CSV_VALIDO) -> Path:
    origem = tmp_path / "partidas.csv"
    origem.write_text(conteudo, encoding="utf-8")
    return origem


def test_catalogo_real_sem_fonte_selecionada_falha_sem_gravar(tmp_path):
    catalogo = carregar_catalogo(RAIZ / "config" / "data_sources.toml")
    with pytest.raises(ColetaErro, match="nenhuma fonte selecionada"):
        executar_pipeline(_origem(tmp_path), catalogo, _config(tmp_path))
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "processed").exists()


@pytest.mark.parametrize("campo", tuple(MAPEAMENTO))
def test_mapeamento_a_verificar_falha_sem_gravar(tmp_path, campo):
    catalogo = _catalogo(mapeamento={**MAPEAMENTO, campo: "a verificar"})
    with pytest.raises(ColetaErro, match="a verificar"):
        executar_pipeline(_origem(tmp_path), catalogo, _config(tmp_path))
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "processed").exists()


def test_competicao_ausente_interrompe_sem_tabela_com_valor_inventado(tmp_path):
    conteudo = CSV_VALIDO.replace(",Brasileirão,", ",,")
    with pytest.raises(IntegridadeErro, match="'competicao' ausente"):
        executar_pipeline(_origem(tmp_path, conteudo), _catalogo(), _config(tmp_path))
    assert not (tmp_path / "processed").exists()


def test_equipe_sem_alias_nao_pode_jogar_contra_variacao_do_proprio_nome(tmp_path):
    conteudo = CSV_VALIDO.replace("Flamengo,Atlético-MG", "Corinthians,CORINTHIANS")
    with pytest.raises(IntegridadeErro, match="mandante igual ao visitante"):
        executar_pipeline(_origem(tmp_path, conteudo), _catalogo(), _config(tmp_path))
    assert not (tmp_path / "processed").exists()


def test_pipeline_grava_copia_bruta_e_tabelas_do_prd(tmp_path):
    resultado = executar_pipeline(_origem(tmp_path), _catalogo(), _config(tmp_path))
    assert resultado.fonte_id == "fonte_teste"
    assert resultado.arquivo_bruto.parent == tmp_path / "raw"
    assert set(resultado.tabelas) == set(TABELAS)
    assert all(caminho.exists() for caminho in resultado.tabelas.values())
    assert resultado.relatorio.criticos == ()


def test_pipeline_e_reproduzivel_entre_execucoes(tmp_path):
    origem = _origem(tmp_path)
    primeira = executar_pipeline(origem, _catalogo(), _config(tmp_path / "a"))
    segunda = executar_pipeline(origem, _catalogo(), _config(tmp_path / "b"))
    for nome in TABELAS:
        assert primeira.tabelas[nome].read_bytes() == segunda.tabelas[nome].read_bytes()


def test_dados_invalidos_interrompem_antes_das_tabelas(tmp_path):
    duplicado = CSV_VALIDO + "1,2024-05-04,2024,Brasileirão,Flamengo,Palmeiras,1,0,1\n"
    with pytest.raises(IntegridadeErro):
        executar_pipeline(_origem(tmp_path, duplicado), _catalogo(), _config(tmp_path))
    assert not (tmp_path / "processed").exists()


def test_pipeline_registra_logs(tmp_path, caplog):
    with caplog.at_level("INFO", logger="processing.pipeline"):
        executar_pipeline(_origem(tmp_path), _catalogo(), _config(tmp_path))
    assert "fonte selecionada: fonte_teste" in caplog.text
    assert "tabelas gravadas" in caplog.text


def test_csv_sem_coluna_rodada_prossegue_com_aviso(tmp_path):
    conteudo = "\n".join(linha.rsplit(",", 1)[0] for linha in CSV_VALIDO.splitlines()) + "\n"
    resultado = executar_pipeline(_origem(tmp_path, conteudo), _catalogo(), _config(tmp_path))
    assert len(resultado.tabelas) == 4
    assert resultado.relatorio.criticos == ()
    assert sum("'rodada' ausente" in a.mensagem for a in resultado.relatorio.avisos) == 3


def test_consulta_pontos_por_equipe_com_parametro(tmp_path):
    config = _config(tmp_path)
    executar_pipeline(_origem(tmp_path), _catalogo(), config)
    linhas = executar_consulta(config.pasta_processed, "pontos_por_equipe", [2024])
    assert [(linha["equipe"], linha["pontos"]) for linha in linhas] == [
        ("Flamengo", 4),
        ("Palmeiras", 3),
        ("Atlético Mineiro", 1),
        ("Grêmio", 0),
    ]


def test_consulta_fora_do_catalogo_e_recusada(tmp_path):
    with pytest.raises(KeyError, match="não autorizada"):
        executar_consulta(tmp_path, "DROP TABLE dim_equipes")


def test_consultas_nao_criam_arquivo_duckdb(tmp_path):
    config = _config(tmp_path)
    executar_pipeline(_origem(tmp_path), _catalogo(), config)
    executar_consulta(config.pasta_processed, "partidas_por_temporada")
    assert list(tmp_path.rglob("*.duckdb")) == []


def test_configuracao_le_settings_do_projeto():
    configuracao = carregar_configuracao(RAIZ / "config" / "settings.yaml")
    assert configuracao.formatos_data == ("%Y-%m-%d", "%d/%m/%Y")
    assert configuracao.pasta_raw == RAIZ / "data" / "raw"
    assert configuracao.pasta_processed == RAIZ / "data" / "processed"
