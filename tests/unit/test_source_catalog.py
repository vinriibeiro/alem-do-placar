"""Testes do catálogo de fontes (T002).

Usam apenas a biblioteca padrão e o Pytest, leem o TOML versionado e arquivos
temporários. Não acessam rede, não baixam dados e não criam processos filhos.
"""

import re
from pathlib import Path

import pytest

from ingestion.source_catalog import (
    CAMPOS_COMPLEMENTARES_PRD,
    CAMPOS_MINIMOS_PRD,
    CAMPOS_OBRIGATORIOS_FONTE,
    CAMPOS_PRD,
    CatalogoInvalido,
    carregar_catalogo,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOGO_REAL = ROOT / "config" / "data_sources.toml"
IDS_PRD = {"football_data", "statsbomb_open_data", "openfootball"}

MAPEAMENTO_TESTE = "\n".join(f'{campo} = "a verificar"' for campo in CAMPOS_PRD)

EVIDENCIAS_TEXTO = {
    "url_termos": 'url_termos = "https://exemplo.invalid/termos"',
    "data_verificacao": 'data_verificacao = "2026-10-29"',
    "verificador": 'verificador = "Revisor humano"',
}
JUSTIFICATIVA_TEXTO = 'justificativa = "Fonte única com licença revisada."'


def _fonte_toml(*, status: str = "pendente_verificacao", decisao: str = "pendente", extras=""):
    return f"""[catalogo]
versao = "0.0.0-teste"

[[fontes]]
id = "fonte_teste"
nome = "Fonte de teste"
url = "https://exemplo.invalid/dados"
licenca = "a verificar"
status_licenca = "{status}"
cobertura_brasileirao = "a verificar"
temporadas = "a verificar"
campos_essenciais = ["data", "mandante"]
campos_complementares = []
riscos = ["Risco de teste."]
decisao = "{decisao}"
{extras}
[fontes.mapeamento]
{MAPEAMENTO_TESTE}
"""


def _escrever(diretorio: Path, texto: str) -> Path:
    caminho = diretorio / "catalogo.toml"
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def _remover_linha(texto: str, campo: str) -> str:
    novo, total = re.subn(rf"(?m)^{campo} = .*\n", "", texto, count=1)
    assert total == 1, campo
    return novo


def test_catalogo_real_contem_as_tres_fontes_do_prd():
    catalogo = carregar_catalogo(CATALOGO_REAL)
    assert {fonte.id for fonte in catalogo.fontes} == IDS_PRD
    assert catalogo.versao == "0.1.0"


def test_catalogo_real_permanece_pendente_sem_selecao():
    catalogo = carregar_catalogo(CATALOGO_REAL)
    assert catalogo.fonte_selecionada() is None
    for fonte in catalogo.fontes:
        assert fonte.status_licenca.value == "pendente_verificacao", fonte.id
        assert fonte.decisao.value == "pendente", fonte.id
        assert fonte.cobertura_brasileirao == "a verificar", fonte.id
        assert fonte.temporadas == "a verificar", fonte.id


@pytest.mark.parametrize(
    "campo", [campo for campo in CAMPOS_OBRIGATORIOS_FONTE if campo != "mapeamento"]
)
def test_campos_obrigatorios_ausentes_geram_erro(tmp_path, campo):
    texto = _remover_linha(_fonte_toml(), campo)
    with pytest.raises(CatalogoInvalido, match=campo):
        carregar_catalogo(_escrever(tmp_path, texto))


def test_mapeamento_sem_campo_do_prd_gera_erro(tmp_path):
    texto = _remover_linha(_fonte_toml(), "partida_id")
    with pytest.raises(CatalogoInvalido, match="partida_id"):
        carregar_catalogo(_escrever(tmp_path, texto))


@pytest.mark.parametrize(
    ("kwargs", "campo"),
    [({"status": "aprovada"}, "status_licenca"), ({"decisao": "talvez"}, "decisao")],
)
def test_valores_fora_dos_enums_geram_erro(tmp_path, kwargs, campo):
    with pytest.raises(CatalogoInvalido, match=campo):
        carregar_catalogo(_escrever(tmp_path, _fonte_toml(**kwargs)))


@pytest.mark.parametrize("ausente", list(EVIDENCIAS_TEXTO))
def test_licenca_verificada_sem_evidencia_e_rejeitada(tmp_path, ausente):
    extras = "\n".join(valor for nome, valor in EVIDENCIAS_TEXTO.items() if nome != ausente)
    texto = _fonte_toml(status="verificada", extras=extras)
    with pytest.raises(CatalogoInvalido, match=ausente):
        carregar_catalogo(_escrever(tmp_path, texto))


def test_selecao_sem_licenca_verificada_e_rejeitada(tmp_path):
    texto = _fonte_toml(decisao="selecionada")
    with pytest.raises(CatalogoInvalido, match="licença verificada"):
        carregar_catalogo(_escrever(tmp_path, texto))


def test_selecao_sem_justificativa_e_rejeitada(tmp_path):
    extras = "\n".join(EVIDENCIAS_TEXTO.values())
    texto = _fonte_toml(status="verificada", decisao="selecionada", extras=extras)
    with pytest.raises(CatalogoInvalido, match="justificativa"):
        carregar_catalogo(_escrever(tmp_path, texto))


def test_selecao_com_licenca_verificada_e_justificativa_e_aceita(tmp_path):
    extras = "\n".join([*EVIDENCIAS_TEXTO.values(), JUSTIFICATIVA_TEXTO])
    texto = _fonte_toml(status="verificada", decisao="selecionada", extras=extras)
    catalogo = carregar_catalogo(_escrever(tmp_path, texto))
    assert catalogo.fonte_selecionada().id == "fonte_teste"


def test_mapeamento_cobre_campos_minimos_e_complementares_do_prd():
    catalogo = carregar_catalogo(CATALOGO_REAL)
    for fonte in catalogo.fontes:
        chaves = set(fonte.mapeamento)
        assert set(CAMPOS_MINIMOS_PRD) <= chaves, fonte.id
        assert set(CAMPOS_COMPLEMENTARES_PRD) <= chaves, fonte.id


def test_toml_invalido_gera_erro(tmp_path):
    with pytest.raises(CatalogoInvalido, match="TOML inválido"):
        carregar_catalogo(_escrever(tmp_path, "[[fontes\nid = "))


def test_catalogo_real_sem_valores_com_cara_de_segredo():
    texto = CATALOGO_REAL.read_text(encoding="utf-8")
    chaves_sensiveis = re.findall(
        r"(?im)^\s*[\w-]*(?:token|password|secret|api_key|senha)[\w-]*\s*=", texto
    )
    credenciais_em_url = re.findall(r"://[^/\s:@]+:[^/\s@]+@", texto)
    cadeias_opacas = re.findall(r"[A-Za-z0-9]{32,}", texto)
    assert chaves_sensiveis == []
    assert credenciais_em_url == []
    assert cadeias_opacas == []
