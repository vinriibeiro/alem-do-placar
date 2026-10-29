# Roadmap

Melhorias priorizadas depois da primeira publicação. A ordem considera o ganho para o visitante, o risco e o custo.

## Antes de divulgar (bloqueios)

1. **Teste manual da Claude API real.** Definir `LLM_API_KEY`, fazer 20 perguntas e comparar com o modo determinístico. Só então confiar no modo com IA.
2. **Validar o Power BI no Desktop** com `docs/qa/T008/checklist_desktop.md` e corrigir o que falhar.
3. **Revisão técnica e QA funcional** das tarefas T001 a T010, com relatórios em `docs/qa/`.

## Próximas melhorias

| Prioridade | Melhoria | Por quê |
|---|---|---|
| Alta | Conjunto formal de avaliação do assistente: 100 perguntas com resposta esperada, rodado a cada mudança | Hoje a qualidade é verificada por 20 perguntas. Um conjunto maior mede regressões e permite comparar `claude-opus-5-5` com modelos menores |
| Alta | Temporada 2026 como avaliação final do modelo | O PRD reservou 2026 para teste temporal. É a prova mais honesta do modelo |
| Alta | Mapa de calor e ordenação nos visuais do Power BI | Foram deixados de fora para não arriscar propriedades sem verificação no Desktop |
| Média | Atualização automática dos dados | Hoje o pipeline é executado à mão. Um job agendado mantém o site em dia durante a temporada |
| Média | Intervalos de previsão calibrados | O intervalo atual é empírico e sem garantia por causa da sobreposição dos alvos |
| Média | Conversa com contexto no assistente | Cada pergunta é independente. Perguntas de acompanhamento, como "e em 2023?", exigem memória da conversa |
| Média | Mais métricas por jogo | Finalizações, posse e cartões, se uma fonte licenciada for aprovada |
| Baixa | xG | Permitiria testar a hipótese H06. Depende de fonte com licença compatível |
| Baixa | Outras competições | O desenho já separa competição e temporada. Exige nova auditoria de fonte |
| Baixa | Domínio próprio e analytics de uso sem dados pessoais | Para acompanhar quais perguntas as pessoas fazem |

## Riscos acompanhados

| Risco | Mitigação atual |
|---|---|
| Custo da API | Teto diário, limite por IP e fallback determinístico |
| Respostas inventadas | O modelo só redige números devolvidos por consultas fechadas; sem consulta, o texto dele é descartado |
| Dados desatualizados | A página mostra o período dos dados; atualização automática está no roadmap |
| Power BI público | Dados abertos e agregados; remoção pelo código de inserção |
