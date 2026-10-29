# Publicação do Além do Placar

Este guia leva o projeto do computador ao ar em um link público. Cada passo marcado com **você** exige uma decisão ou uma conta sua. Nada aqui é feito automaticamente.

## O que vai ao ar

Um único serviço Docker com o site (início, dashboard, assistente, metodologia) e a API. O dashboard do Power BI aparece dentro do site por um iframe público. Os dados são lidos de arquivos Parquet incluídos na imagem.

## Pré-requisitos

| Item | Responsável | Observação |
|---|---|---|
| Repositório público no GitHub | você | Vazio, sem README, por exemplo `alem-do-placar` |
| Conta no Render, ligada ao GitHub | você | render.com |
| Chave da Claude API | você | console.anthropic.com. Defina um limite mensal de gasto lá. Sem chave, o assistente funciona em modo básico |
| Power BI Pro e Publicar na web habilitado | você | Veja a seção Power BI |

## 1. Enviar o código ao GitHub

Na pasta do projeto, com a branch que você aprovou:

```powershell
git remote set-url origin https://github.com/SEU_USUARIO/alem-do-placar.git
git push -u origin develop
git push origin main   # somente depois de aprovar o merge em main
```

Confirme antes que `git status` está limpo e que nenhum `.env` aparece no repositório.

## 2. Criar o serviço no Render

1. Render, New, Blueprint, escolha o repositório. O Render lê o `render.yaml`.
2. Preencha as variáveis marcadas como manuais:

| Variável | Valor |
|---|---|
| `LLM_API_KEY` | Sua chave da Claude API |
| `ALLOWED_HOSTS` | O domínio do serviço (ex.: `alem-do-placar.onrender.com`) e o domínio próprio, se houver |
| `POWERBI_EMBED_URL` | Deixe vazio por enquanto; preencha depois do passo Power BI |
| `REPO_URL` | URL do repositório no GitHub |

3. O plano Starter evita que o serviço hiberne. O plano gratuito hiberna e demora cerca de 50 segundos para acordar.
4. `autoDeploy` está desligado. Cada nova versão é publicada por você, com Manual Deploy.

O Render define `RENDER_EXTERNAL_HOSTNAME` sozinho, e o site já aceita esse host.

## 3. Power BI

1. Gere o projeto em modo web, com a URL do seu repositório e do seu site:

```powershell
.\.venv\Scripts\python.exe scripts\gerar_powerbi.py --fonte web `
  --url-base https://raw.githubusercontent.com/SEU_USUARIO/alem-do-placar/main/data `
  --url-assistente https://alem-do-placar.onrender.com/assistente
```

2. Abra `dashboard/powerbi/AlemDoPlacar/AlemDoPlacar.pbip` no Power BI Desktop e siga `docs/qa/T008/checklist_desktop.md`.
3. Publique no seu workspace.
4. No Serviço do Power BI: Arquivo, Inserir relatório, **Publicar na web (público)**. Copie o endereço do iframe.
5. No Render, preencha `POWERBI_EMBED_URL` com esse endereço e reinicie o serviço.

Se Publicar na web estiver desabilitado, o administrador do locatário precisa liberar em Portal de administração, Configurações de locatário. Em locatário corporativo isso costuma ser bloqueado; use uma conta pessoal.

Aviso de privacidade: Publicar na web torna o relatório público para qualquer pessoa com o link. Os dados são CC0 e agregados, sem informação pessoal.

## 4. Verificar

Depois do deploy, na URL pública:

| Verificação | Esperado |
|---|---|
| `/health` | `{"app":"alem-do-placar","status":"ok"}` |
| `/` | Página inicial com os KPIs preenchidos |
| `/dashboard` | O relatório do Power BI carrega dentro do site |
| `/assistente` | Pergunta "Qual foi a classificação de 2025?" responde com Flamengo líder e 79 pontos |
| `/metodologia` | Documentos e três figuras |
| Cabeçalhos | Resposta de `/` inclui `content-security-policy` e `strict-transport-security` |

## 5. Custos e limites

| Item | Valor de referência |
|---|---|
| Render Starter | Cerca de US$ 7 por mês |
| Claude API | Poucos centavos de dólar por pergunta com esforço baixo; teto diário de chamadas em `LLM_DAILY_LIMIT` (300 no `render.yaml`) |
| Limite por visitante | `RATE_LIMIT_PER_MIN` perguntas por minuto por IP (20) |

Ao atingir o teto diário, o assistente continua no modo básico, sem erro para o visitante.

## 6. Alternativa gratuita: Hugging Face Spaces

1. Crie um Space do tipo Docker.
2. Envie o repositório (o `Dockerfile` já serve) e defina a porta `8000` em `app_port` no README do Space.
3. Configure os mesmos segredos em Settings, Variables and secrets. Defina `ALLOWED_HOSTS` com o domínio `*.hf.space` do Space.
4. O Space hiberna depois de inatividade e o primeiro acesso demora.

## Teste local da imagem

```powershell
docker build -t alem-do-placar .
docker run --rm -p 8000:8000 -e ALLOWED_HOSTS=localhost alem-do-placar
```

Depois abra http://127.0.0.1:8000. Variáveis opcionais estão em `.env.example` e em `docs/api_contrato.md`.

## Reverter

No Render, Events, Rollback para a versão anterior. Para tirar o site do ar, suspenda o serviço. O Power BI público é removido em Configurações do espaço de trabalho, Gerenciar códigos de inserção.
