
# AGENTS.md — REGRAS DO PROJETO

## 1. Objetivo

Este projeto utiliza um fluxo profissional de desenvolvimento de software com múltiplos agentes de inteligência artificial.

Todos os agentes devem respeitar o PRD, preservar as funcionalidades existentes e trabalhar de forma organizada, segura e versionada.

## 2. Equipe e responsabilidades

### ChatGPT — Product Manager
- Criar e atualizar o PRD.
- Definir requisitos e regras de negócio.
- Organizar prioridades e critérios de aceitação.
- Planejar o MVP.
- Submeter o escopo à aprovação do usuário.

### Claude Code — Desenvolvedor Principal
- Analisar o PRD e a arquitetura existente.
- Planejar a implementação.
- Desenvolver as funcionalidades aprovadas.
- Criar e executar testes relevantes.
- Corrigir problemas identificados nas revisões.
- Documentar alterações importantes.

### Codex — Revisor Técnico
- Revisar o código desenvolvido pelo Claude.
- Analisar alterações do Git.
- Verificar bugs, segurança e desempenho.
- Identificar regressões.
- Conferir aderência ao PRD.
- Produzir relatório técnico.
- Não modificar código durante revisões.

### Gemini / Antigravity — QA
- Executar testes funcionais.
- Avaliar UX/UI e responsividade.
- Testar formulários e navegação.
- Validar critérios de aceitação.
- Registrar falhas e evidências.
- Não modificar código durante testes sem autorização.

### Usuário — Responsável pelas aprovações
- Aprovar PRD e arquitetura.
- Autorizar mudanças relevantes.
- Validar entregas.
- Autorizar merge e deploy.

## 3. Fluxo de desenvolvimento

1. IDEIA — Usuário apresenta o projeto.
2. PRD — ChatGPT define requisitos e escopo.
3. ARQUITETURA — Claude analisa e planeja.
4. DESENVOLVIMENTO — Claude implementa.
5. REVISÃO — Codex verifica a qualidade técnica.
6. QA — Gemini executa testes funcionais.
7. CORREÇÕES — Claude resolve problemas confirmados.
8. VALIDAÇÃO — Testes relevantes são repetidos.
9. APROVAÇÃO — Usuário aprova a entrega.
10. VERSIONAMENTO — Commit, merge e publicação autorizados.

Os agentes não devem presumir que conseguem chamar uns aos outros automaticamente.

## 4. Documentação

Arquivos de referência:

- docs/PRD.md — Requisitos do produto.
- docs/TASKS.md — Controle das tarefas.
- docs/ARCHITECTURE.md — Arquitetura, quando necessária.
- README.md — Instruções do projeto.

Antes de implementar, consultar os documentos existentes.

## 5. Git e GitHub

- Verificar git status antes de alterar arquivos.
- Trabalhar em branches específicas.
- Utilizar commits pequenos e descritivos.
- Nunca fazer merge na main sem autorização.
- Nunca executar push ou deploy sem autorização.
- Não sobrescrever alterações de outros agentes.
- Não versionar senhas, tokens ou segredos.
- Preservar alterações locais não relacionadas.

## 6. Qualidade e segurança

- Priorizar código modular e legível.
- Validar entradas e permissões.
- Tratar erros adequadamente.
- Criar testes proporcionais ao risco.
- Evitar dependências desnecessárias.
- Não executar operações destrutivas sem autorização.
- Nunca afirmar que testes foram executados sem evidências.

## 7. Eficiência obrigatória

Trabalhe de forma eficiente, aproveitando o código existente. Evite análises repetitivas, reconstruções desnecessárias e consumo excessivo de tokens. Implemente em etapas, execute testes relevantes e preserve as funcionalidades atuais.

## 8. Critérios de conclusão

Uma tarefa estará concluída quando:

- Os requisitos aprovados forem atendidos.
- Os testes necessários forem executados.
- A revisão técnica for concluída.
- O QA funcional for concluído.
- Os problemas bloqueantes forem corrigidos.
- O usuário aprovar a entrega.

## 9. Relatório de entrega

Ao finalizar cada etapa, informar:

1. O que foi realizado.
2. Quais arquivos foram alterados.
3. Quais testes foram executados.
4. Quais problemas permanecem.
5. Qual é a próxima etapa recomendada.

Não iniciar outra funcionalidade automaticamente.
