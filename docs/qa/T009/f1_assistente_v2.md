# T009 v2 (F1) — Assistente com catálogo ampliado e camada Claude

- **Data:** 2026-10-29
- **Branch:** feature/t009-assistente-v2
- **Responsável:** Claude Code
- **Arquivos novos:** src/api/catalogo.py, llm.py, servico.py, config.py, tests/unit/test_catalogo_llm.py, docs/api_contrato.md, docs/assistente_catalogo.md
- **Arquivos alterados:** src/api/assistant.py, app.py, server.py, pyproject.toml, .env.example
- **Testes:** suíte completa, ver resultado no commit. 39 testes novos, com cliente Anthropic simulado.
- **Limitação:** a chamada real à Claude API NÃO foi testada, pois não há LLM_API_KEY neste ambiente. O formato do pedido (beta de fallback, esquema estrito, effort baixo) foi verificado só contra a assinatura do SDK e o cliente simulado. Teste manual necessário com chave real.
- **Revisão Codex / QA Gemini:** não registrados.
- **Status:** AGUARDANDO REVISÃO
