"""Registro local de experimentos com MLflow (T006; PRD 7.2 e RNF07).

Usa somente o backend SQLite local. Não usa servidor nem nuvem e não altera
a URI global do MLflow. Registra parâmetros e métricas numéricas; nenhuma credencial é gravada.
"""

import math
from pathlib import Path
from typing import Any

NOME_EXPERIMENTO = "alem-do-placar-t006"
MENSAGEM_INDISPONIVEL = "backend local do MLflow indisponível; confira as dependências declaradas"


def tracking_uri_local(pasta: Path | str) -> str:
    """URI SQLite absoluta, independente da configuração global do MLflow."""
    return "sqlite:///" + (Path(pasta).resolve() / "mlflow.db").as_posix()


def registrar_experimento(resultado: dict[str, Any], pasta: Path | str) -> str:
    """Registra o resultado de ``executar_backtest`` em ``pasta`` e devolve o id da execução."""
    parametros, metricas = _parametros_e_metricas(resultado)
    try:
        from mlflow.tracking import MlflowClient
    except ImportError as erro:
        raise RuntimeError(MENSAGEM_INDISPONIVEL) from erro

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    try:
        uri = tracking_uri_local(pasta)
        cliente = MlflowClient(tracking_uri=uri, registry_uri=uri)
        experimento = cliente.get_experiment_by_name(NOME_EXPERIMENTO)
        if experimento is not None:
            id_experimento = experimento.experiment_id
        else:
            id_experimento = cliente.create_experiment(
                NOME_EXPERIMENTO, artifact_location=(pasta.resolve() / "artifacts").as_uri()
            )
        run_id = cliente.create_run(id_experimento).info.run_id
        try:
            for chave, valor in parametros.items():
                cliente.log_param(run_id, chave, valor)
            for chave, valor in metricas.items():
                cliente.log_metric(run_id, chave, valor)
        finally:
            cliente.set_terminated(run_id)
    except Exception as erro:
        raise RuntimeError(f"falha ao registrar experimento em {pasta}: {erro}") from erro
    return run_id


def _parametros_e_metricas(resultado: dict[str, Any]) -> tuple[dict, dict]:
    metadados = resultado["metadados"]
    parametros = {
        "seed": str(metadados["seed"]),
        "modelo": str(resultado["modelo_selecionado"]),
        "versao": str(resultado["versao"]),
        "atributos": ",".join(resultado["atributos"]),
        "anos_validacao": ",".join(str(ano) for ano in metadados["anos_validacao"]),
        "ano_holdout": str(metadados["ano_holdout"]),
        "corte_treino": str(metadados["corte_treino"]),
        "horizonte": str(metadados["horizonte"]),
    }
    metricas = {}
    for linha in resultado["metricas"].itertuples(index=False):
        if str(linha.temporada) != "todas":
            continue
        for medida in ("mae", "rmse", "vies"):
            metricas[f"{linha.fase}_{medida}_{linha.modelo}"] = _finito(getattr(linha, medida))
    metricas["quantil_erro_absoluto"] = _finito(metadados["quantil_erro_absoluto"])
    metricas["cobertura_holdout"] = _finito(metadados["cobertura_holdout"])
    return parametros, metricas


def _finito(valor: Any) -> float:
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValueError(f"métrica não finita: {valor}")
    return numero
