"""Orquestração do pipeline de coleta e tratamento (T003; PRD 4.2).

Sequência: fonte selecionada -> leitura local -> cópia bruta -> padronização -> validação
-> tabelas -> persistência. Falhas explícitas interrompem antes de gravar os dados processados.
Nenhuma chamada de rede ocorre.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

from ingestion.coleta import copiar_bruto, ler_partidas, selecionar_fonte
from ingestion.source_catalog import CatalogoFontes
from processing.padronizacao import ALIASES_EQUIPES, padronizar_partidas
from processing.persistencia import escrever_tabela
from processing.tabelas import gerar_tabelas
from validation.integridade import (
    RelatorioIntegridade,
    levantar_se_critico,
    validar_desempenho,
    validar_partidas,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConfiguracaoPipeline:
    """Parâmetros de execução: formatos de data e pastas de saída."""

    formatos_data: tuple[str, ...]
    pasta_raw: Path
    pasta_processed: Path


@dataclass(frozen=True, slots=True)
class ResultadoPipeline:
    """Resumo da execução: fonte, cópia bruta, tabelas gravadas e relatório."""

    fonte_id: str
    arquivo_bruto: Path
    tabelas: dict[str, Path]
    relatorio: RelatorioIntegridade


def carregar_configuracao(caminho_settings: Path) -> ConfiguracaoPipeline:
    """Lê ``config/settings.yaml``; caminhos relativos são resolvidos a partir da raiz."""
    with caminho_settings.open(encoding="utf-8") as arquivo:
        dados = yaml.safe_load(arquivo)
    raiz = caminho_settings.parents[1]
    caminhos = dados["paths"]
    return ConfiguracaoPipeline(
        formatos_data=tuple(dados["pipeline"]["formatos_data"]),
        pasta_raw=raiz / caminhos["raw"],
        pasta_processed=raiz / caminhos["processed"],
    )


def executar_pipeline(
    origem: Path,
    catalogo: CatalogoFontes,
    configuracao: ConfiguracaoPipeline,
) -> ResultadoPipeline:
    """Executa o pipeline sobre um arquivo local de partidas. Não acessa a rede."""
    fonte = selecionar_fonte(catalogo)
    logger.info("fonte selecionada: %s", fonte.id)
    linhas = ler_partidas(origem, fonte)
    logger.info("linhas lidas: %d", len(linhas))
    arquivo_bruto = copiar_bruto(origem, fonte, configuracao.pasta_raw)
    logger.info("cópia bruta gravada: %s", arquivo_bruto)

    partidas = padronizar_partidas(linhas, configuracao.formatos_data, ALIASES_EQUIPES)
    relatorio = RelatorioIntegridade(tuple(validar_partidas(partidas)))
    levantar_se_critico(relatorio)

    tabelas = gerar_tabelas(partidas)
    desempenho = validar_desempenho(tabelas["fato_desempenho_equipes"])
    relatorio = RelatorioIntegridade(relatorio.achados + tuple(desempenho))
    levantar_se_critico(relatorio)
    for aviso in relatorio.avisos:
        logger.warning("aviso de integridade: %s", aviso.mensagem)

    arquivos = {
        nome: escrever_tabela(nome, linhas_tabela, configuracao.pasta_processed)
        for nome, linhas_tabela in tabelas.items()
    }
    logger.info("tabelas gravadas: %s", ", ".join(sorted(arquivos)))
    return ResultadoPipeline(fonte.id, arquivo_bruto, arquivos, relatorio)
