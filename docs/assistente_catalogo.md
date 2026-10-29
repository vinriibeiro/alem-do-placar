# Catálogo de consultas do assistente

Todas as consultas leem o dataset analítico (`data/processed/dataset_analitico.parquet`, duas linhas por partida) e as saídas de modelagem. Implementação: `src/api/catalogo.py` (histórico) e `src/api/assistant.py` (modelo e tendências). O modelo de linguagem só escolhe uma destas consultas; ele não gera SQL.

Cada consulta devolve: `texto_base`, `dados`, `fonte`, `periodo`, `limitacoes`.

| Consulta | Parâmetros | Exemplo de pergunta |
|---|---|---|
| `classificacao` | `ano`, `top` | Qual foi a classificação de 2024? |
| `resumo_equipe` | `equipe`, `ano` | Resumo do Flamengo em 2025 |
| `comparar_equipes` | `equipe_a`, `equipe_b`, `ano` | Compare Palmeiras e Flamengo em 2025 |
| `confronto_direto` | `equipe_a`, `equipe_b`, `ano` | Histórico entre Flamengo e Palmeiras |
| `mando` | `equipe`, `ano` | Como o Corinthians vai como mandante e visitante? |
| `gols` | `ano` | Quais foram as maiores goleadas? |
| `sequencias` | `tipo` (invicta, vitorias, derrotas, sem_vencer), `equipe`, `ano` | Maior sequência invicta de 2025 |
| `ranking` | `metrica` (pontos, aproveitamento, ataque, defesa, saldo, consistencia, vitorias), `ano`, `top` | Qual a melhor defesa de 2024? |
| `consulta_modelo` | `intencao` (previsao, erro, importancia, explicacao, consistencia, evolucao), `equipe`, `ano`, `queda` | Qual é a previsão do Flamengo? |

## Regras de cálculo

- Pontos 3/1/0. Classificação ordenada por pontos, vitórias, saldo e gols pró. Os critérios oficiais de desempate não são aplicados, e a resposta avisa isso.
- Equipe aceita nome completo ou parcial único. Nome ambíguo gera pedido de esclarecimento, nunca palpite.
- Ano fora de 2018–2025 gera erro explícito; nenhum outro ano é usado no lugar.
- "Mais consistente" significa menor desvio-padrão dos pontos por jogo, não melhor desempenho.
- xG, jogos futuros e dados externos não existem no projeto e recebem a resposta padrão do PRD 9.5.
