"""Nomes amigáveis e definições (fonte única para dashboard, site e dicionário de dados).

As descrições dos atributos foram conferidas em ``src/features/temporais.py``: todas as janelas
são calculadas por equipe e temporada, em ordem cronológica, e incluem o jogo de referência
(o alvo começa no jogo seguinte, então não há uso de informação futura).
"""

ATRIBUTOS = {
    "media_pontos_3": (
        "Média de pontos nos últimos 3 jogos",
        "Média dos pontos (3, 1 ou 0) da equipe nos 3 jogos mais recentes da temporada, incluindo o jogo de referência.",
    ),
    "media_pontos_5": (
        "Média de pontos nos últimos 5 jogos",
        "Média dos pontos da equipe nos 5 jogos mais recentes da temporada. Também é o modelo de referência.",
    ),
    "media_pontos_10": (
        "Média de pontos nos últimos 10 jogos",
        "Média dos pontos da equipe nos 10 jogos mais recentes da temporada.",
    ),
    "media_saldo_gols_3": (
        "Saldo médio de gols nos últimos 3 jogos",
        "Média de (gols marcados − gols sofridos) nos 3 jogos mais recentes da temporada.",
    ),
    "media_saldo_gols_5": (
        "Saldo médio de gols nos últimos 5 jogos",
        "Média de (gols marcados − gols sofridos) nos 5 jogos mais recentes da temporada.",
    ),
    "media_saldo_gols_10": (
        "Saldo médio de gols nos últimos 10 jogos",
        "Média de (gols marcados − gols sofridos) nos 10 jogos mais recentes da temporada.",
    ),
    "desvio_pontos_5": (
        "Oscilação dos pontos nos últimos 5 jogos",
        "Desvio-padrão dos pontos nos 5 jogos mais recentes: quanto maior, mais irregular a equipe.",
    ),
    "media_pontos_mandante_historico": (
        "Média de pontos como mandante na temporada",
        "Média dos pontos da equipe nos jogos em casa da temporada, até o jogo de referência.",
    ),
    "media_pontos_visitante_historico": (
        "Média de pontos como visitante na temporada",
        "Média dos pontos da equipe nos jogos fora de casa da temporada, até o jogo de referência.",
    ),
    "jogos_acumulados": (
        "Jogos disputados na temporada",
        "Quantidade de jogos da equipe na temporada até o jogo de referência.",
    ),
    "dias_descanso": (
        "Dias de descanso",
        "Dias entre o jogo de referência e o jogo anterior da equipe na mesma temporada.",
    ),
    "mando": (
        "Jogou em casa",
        "1 quando a equipe foi mandante no jogo de referência; 0 quando foi visitante.",
    ),
}

MODELOS = {
    "M00_media_recente_5": ("Média dos últimos 5 jogos (referência)", "Referência"),
    "B01_media_historica_treino": ("Média histórica do treino (referência)", "Referência"),
    "M01_ridge": ("Regressão Ridge", "Machine Learning"),
    "M02_random_forest": ("Random Forest", "Machine Learning"),
    "M03_hist_gradient_boosting": ("Gradient Boosting", "Machine Learning"),
}

FASES = {"validacao": "Validação (2022–2024)", "holdout": "Teste com dados de 2025"}

METRICAS = {
    "mae": (
        "Erro médio absoluto (MAE)",
        "Em média, quantos pontos por jogo a previsão erra, para mais ou para menos.",
    ),
    "rmse": (
        "Raiz do erro quadrático médio (RMSE)",
        "Parecido com o MAE, mas pesa mais os erros grandes.",
    ),
    "vies": (
        "Viés",
        "Média de (previsto − real): positivo indica previsões otimistas; negativo, pessimistas.",
    ),
}

ALVO = (
    "Média de pontos nos próximos 5 jogos",
    "Soma dos pontos da equipe nos 5 jogos seguintes da mesma temporada, dividida por 5.",
)


def nome_modelo(codigo: str) -> str:
    return MODELOS.get(codigo, (codigo, ""))[0]


def nome_atributo(codigo: str) -> str:
    return ATRIBUTOS.get(codigo, (codigo, ""))[0]
