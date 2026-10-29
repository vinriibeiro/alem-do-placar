# Evolução "Projeto Brasileirão": verificação dos critérios de aceitação

- **Data:** 29/10/2026
- **Branch:** feature/t008-powerbi-ajustes (nada mesclado em develop ou main; nenhum push)
- **Cópia do projeto salvo pelo Power BI Desktop antes da mudança:** branch `snapshot/desktop-salvo-2026-10-29`

| Critério | Situação | Como foi verificado |
|---|---|---|
| Cabeçalho e rodapé corrigidos em todas as páginas | Feito no gerador | Teste: faixa única de 1280 px sem borda e sem menu, rodapé com 24 px e texto. **Falta conferir no Desktop** |
| Identidade visual consistente | Feito | Paleta verde, amarelo e grafite nos tokens compartilhados pelo site e pelo tema do Power BI |
| Nenhum título importante cortado | Parcial | Alturas maiores, título com quebra de linha e "Modelos" no lugar de "Laboratório de Modelos". **Falta conferir no Desktop** |
| Classificação respeita a temporada | Feito | Medidas vazias sem temporada única; desempenho conferido contra o Python (Botafogo 79 em 2024, Flamengo 79 em 2025) |
| Cartões com dados verdadeiros | Feito | Artilheiro, Craque e Melhor Goleiro da Wikipédia (prêmios oficiais) e melhor ataque calculado; 2023 sem prêmio na fonte aparece como "Não informado na fonte" |
| Fotos e escudos corretos | Feito | Folhas de contato conferidas visualmente; fotos do artigo do próprio jogador, só com licença livre; silhueta quando não há |
| Tendências continua funcionando | Feito | Mesmos gráficos; linha de 3 jogos removida para legibilidade; Flamengo inicial; equipe não filtra matriz nem ranking |
| Resultados em categorias legíveis | Feito | Coluna Derrota, Empate e Vitória em percentual; teste garante que os pontos 0/1/3 não são o eixo |
| Modelos com nomes compreensíveis | Feito | Fonte única `src/evaluation/nomes.py`, conferida no código dos atributos |
| Métricas corretas | Feito | Valores lidos de `metricas.json`; teste de fumaça 35/35 |
| Previsões não misturam equipes | Feito | Flamengo inicial, seleção única; faixa cinza tracejada |
| Central sem API paga | Feito | JavaScript e JSON estáticos; 19 testes do motor em Node |
| Perguntas fora do assunto recusadas | Feito | Testes com receita, política, programação e geografia |
| Sem informações inventadas | Feito | Testes de métrica indisponível (xG, posse, torcida), temporada 2026, equipe ausente, nome ambíguo e jogador sem foto |
| Metodologia para leigos | Feito | Página do Power BI redesenhada e base de conhecimento da Central |
| Repositório organizado e documentado | Feito | README, dicionário de dados, auditoria, guia de publicação |
| Testes executados | Feito | 367 testes (Python e Node), ruff sem pendências |
| Telas menores | Parcial | CSS fluido; Chrome headless só captura a partir de 500 px |
| Links quebrados | Feito | Teste garante que todo `static/` referenciado existe; sem URL real configurada, nenhum link é inventado |

## Pendências do responsável

1. Fechar o Power BI Desktop e abrir `dashboard/powerbi/AlemDoPlacar-nova-versao/AlemDoPlacar.pbip` para conferir. Se estiver bom, rodar `python scripts/gerar_powerbi.py` para atualizar a pasta principal.
2. Publicar conforme `docs/deploy.md`.

- **Revisão Codex / QA Gemini:** não registrados.
