# T009 (F2) — Redesign do web app

- **Data:** 2026-10-29
- **Branch:** feature/t009-webapp-redesign
- **Responsável:** Claude Code
- **Entrega:** design system em `src/api/static/css/tokens.css` (espelhado em `dashboard/assets/tema_tokens.json` por `scripts/gerar_og.py`), páginas Início, Dashboard, Assistente (chat) e Metodologia (gerada de `docs/model_card.md` e `docs/methodology.md`), rotas `/api/config`, `/api/sugestoes`, `/figuras/*`, imagem Open Graph.
- **Testes:** suíte completa (ver commit). Novos: `tests/unit/test_webapp.py`. Garantem que o HTML só referencia arquivos existentes, que não há `innerHTML` nem script inline, validação da URL do embed e lista branca de figuras.
- **Evidências visuais:** `docs/qa/T009/capturas/` (Chrome headless, 1280 px e 500 px).
- **Limitação:** a largura mínima do Chrome headless é 500 px, então 360 px não foi capturado. O CSS usa colunas fluidas e rolagem horizontal só dentro das tabelas. Teste manual em celular real recomendado.
- **Dashboard:** sem `POWERBI_EMBED_URL` a página mostra o estado "em publicação". O iframe só foi testado pela lógica, não com um relatório real.
- **Revisão Codex / QA Gemini:** não registrados.
- **Status:** AGUARDANDO REVISÃO
