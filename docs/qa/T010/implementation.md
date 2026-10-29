# T010 (F5) — QA final, documentação e divulgação

- **Data:** 2026-10-29
- **Branch:** feature/t010-publicacao (contém F0 a F5, empilhadas; nada mesclado em develop ou main)
- **Responsável:** Claude Code

## Evidências

| Verificação | Resultado |
|---|---|
| Suíte completa, ruff check e ruff format | 337 testes aprovados, sem pendências |
| Teste de fumaça e integridade (`scripts/smoke_test.py`) contra instância local | 35 de 35 verificações, ver `test-results.md` |
| Indicadores da página inicial contra cálculo independente nas tabelas de fatos | Partidas 3.040, temporadas 8, MAE 0,478 e cobertura 91,2% conferem |
| 20 perguntas de 10 categorias contra cálculo independente | Classificação, resumo, comparação, confronto, mando, gols, sequência, ranking e modelo conferem |
| Recusas | Clima, injeção de comando e ano inexistente sem dados inventados |
| Revisão visual em Chrome headless | Defeitos encontrados e corrigidos: nota vazia do KPI de partidas e rolagem da página ao devolver o foco ao campo do chat |

## Documentação

README de portfólio com diagrama, resultados e limitações; `docs/roadmap.md`; textos públicos da metodologia revisados (sem referência a "controlador" e com a situação correta da fonte de dados); material de divulgação em `docs/divulgacao/`.

## Não verificado (mesmas limitações das fases anteriores)

Claude API real, Power BI Desktop, build da imagem Docker, Render e URL pública. O teste de fumaça deve ser repetido contra a URL pública com `--pausa 3.2`.

## Divergências encontradas

Nenhuma divergência numérica entre a aplicação e os cálculos independentes.

- **Revisão Codex / QA Gemini:** não registrados.
- **Status:** AGUARDANDO REVISÃO, VALIDAÇÕES MANUAIS E APROVAÇÃO
