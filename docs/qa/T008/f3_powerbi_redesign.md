# T008 (F3) — Redesign do Power BI

- **Data:** 2026-10-29
- **Branch:** feature/t008-powerbi-redesign
- **Responsável:** Claude Code
- **Entrega:** `src/evaluation/powerbi_layout.py` (tema, cabeçalho, navegação, 7 páginas), gerador com fonte web e URL do assistente, 37 medidas com formato, `scripts/gerar_powerbi.py`, projeto regenerado, tokens compartilhados com o site.
- **Testes:** suíte completa (ver commit). Novos: `tests/unit/test_powerbi_layout.py` (canvas, sobreposição, navegação, tema, modo web, URL, medidas).
- **Limitação principal:** o resultado NÃO foi aberto no Power BI Desktop (indisponível neste ambiente). Roteiro em `docs/qa/T008/checklist_desktop.md`. Primeiros suspeitos se algo falhar: pageNavigator, pivotTable, scatterChart, hiperlink de caixa de texto e formato do tema.
- **Visuais não feitos:** formatação condicional (mapa de calor) da matriz e ordenação dos gráficos de barras, para não arriscar propriedades não verificadas. O usuário pode aplicá-las no Desktop.
- **Revisão Codex / QA Gemini:** não registrados.
- **Status:** AGUARDANDO VALIDAÇÃO NO DESKTOP, REVISÃO E QA
