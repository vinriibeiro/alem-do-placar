# T010 (F4) — Preparação de deploy: evidências locais

- **Data:** 2026-10-29
- **Branch:** feature/t010-deploy
- **Responsável:** Claude Code

## O que foi entregue

Dockerfile em dois estágios com usuário sem privilégios, `.dockerignore` em lista de permissão, `requirements-web.txt` (só dependências de execução), ponto de entrada `api.main`, `render.yaml` com deploy manual, CSP e HSTS, redirecionamento para HTTPS, suporte a HEAD, CI com build da imagem, LICENSE MIT e `docs/deploy.md`.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| Suíte completa, ruff check e ruff format | 337 testes aprovados, sem pendências |
| Ambiente virtual limpo só com `requirements-web.txt` mais `pip install --no-deps .` | Aplicação sobe sem scikit-learn, mlflow, duckdb ou matplotlib |
| Pasta de aplicação montada só com os arquivos da lista de permissão (cerca de 1 MB) | `/health`, `/api/contexto`, `/api/pergunta`, as 4 páginas, figuras e estáticos responderam 200 |
| Host público em HTTP com `FORCE_HTTPS` | 308 para HTTPS |
| Host público com `X-Forwarded-Proto: https` | 200 com `Strict-Transport-Security` |
| Host não permitido | 400 |
| CSP em navegador real (Chrome headless) | Chat, fontes e iframe do Power BI funcionam |

## O que NÃO foi verificado

- **Imagem Docker:** o Docker não está instalado nesta máquina, então `docker build` e `docker run` não foram executados. O job de CI constrói e testa a imagem no primeiro push. A simulação acima reproduz o conteúdo e as dependências da imagem, mas não o Dockerfile em si.
- **Render:** nenhum serviço foi criado.
- **Claude API real:** sem chave neste ambiente, a rota com LLM foi testada apenas com cliente simulado.
- **Push e remoto:** o remoto `origin` ainda aponta para o repositório de template. Nenhum push foi feito.

## Pendências do responsável

Criar o repositório e a conta no Render, definir os segredos, autorizar o push e o deploy, publicar o Power BI. Passos em `docs/deploy.md`.

- **Revisão Codex / QA Gemini:** não registrados.
- **Status:** AGUARDANDO AUTORIZAÇÃO DE PUBLICAÇÃO
