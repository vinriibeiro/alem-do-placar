# Publicação do Além do Placar

O projeto vai ao ar em duas partes, ambas gratuitas além da licença Power BI que você já tem:

| Parte | Onde | Custo |
|---|---|---|
| Site: início, Central de Consulta e metodologia | GitHub Pages (arquivos estáticos) | Gratuito |
| Dashboard | Power BI Service, "Publicar na web", incorporado na página Dashboard do site | Incluído no Power BI Pro |

Não há servidor, banco de dados nem API paga. Cada passo marcado com **você** depende da sua conta e da sua autorização; nada é publicado automaticamente.

## 1. Repositório no GitHub (você)

1. Crie um repositório público vazio, por exemplo `alem-do-placar`.
2. Na pasta do projeto, depois de aprovar a branch que vai para `main`:

```powershell
git remote set-url origin https://github.com/SEU_USUARIO/alem-do-placar.git
git push -u origin main
```

Confirme antes que `git status` está limpo e que nenhum `.env` aparece no repositório.

## 2. Site no GitHub Pages (você)

1. No repositório: Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. Em Actions, abra **Publicar site (GitHub Pages)** e clique em **Run workflow**. O workflow roda os testes, gera o site com `scripts/build_site.py` e publica.
3. O endereço será `https://SEU_USUARIO.github.io/alem-do-placar/`. A Central fica em `.../consulta.html`.

O workflow só roda quando você o aciona.

## 3. Dashboard no Power BI (você)

1. Gere o projeto lendo os dados do GitHub, com os links reais:

```powershell
.\.venv\Scripts\python.exe scripts\gerar_powerbi.py --fonte web `
  --url-base https://raw.githubusercontent.com/SEU_USUARIO/alem-do-placar/main/data `
  --url-central https://SEU_USUARIO.github.io/alem-do-placar/consulta.html `
  --url-repositorio https://github.com/SEU_USUARIO/alem-do-placar
```

2. Abra `dashboard/powerbi/AlemDoPlacar/AlemDoPlacar.pbip` no Power BI Desktop, confira com `docs/qa/T008/checklist_desktop.md` e publique no seu workspace.
3. No Power BI Service: Arquivo → Inserir relatório → **Publicar na web (público)**. Copie o endereço do iframe.
4. No GitHub: Settings → Secrets and variables → Actions → Variables → crie `POWERBI_EMBED_URL` com esse endereço.
5. Rode o workflow do Pages de novo. A página Dashboard do site passa a mostrar o relatório.

Se "Publicar na web" estiver desabilitado, o administrador do locatário precisa liberar em Portal de administração → Configurações de locatário. Em locatário corporativo isso costuma ser bloqueado; use uma conta pessoal.

Aviso: "Publicar na web" deixa o relatório visível para qualquer pessoa com o link. Os dados são abertos (CC0) e agregados, sem informação pessoal.

## 4. Verificar

| Endereço | Esperado |
|---|---|
| `.../index.html` | Página inicial com os indicadores preenchidos |
| `.../consulta.html?q=Quem foi o campeão de 2025?` | Flamengo, 79 pontos, com a origem |
| `.../consulta.html?q=receita de bolo` | Recusa educada (fora do tema) |
| `.../dashboard.html` | O relatório do Power BI carrega dentro da página |
| `.../metodologia.html` | Documentos e três figuras |

No Power BI publicado: a Visão Geral abre em 2025, Tendências e Previsões abrem no Flamengo, e o botão da página Central de Consulta abre o site.

## Alternativa: Cloudflare Pages

O mesmo site funciona no Cloudflare Pages: comando de build `pip install -e . && python scripts/build_site.py`, pasta de saída `site`. Prefira o GitHub Pages se não precisar de domínio próprio com recursos extras.

## Servidor local (opcional)

Para desenvolver, `scripts/run_local.ps1` sobe o mesmo site com FastAPI em `http://127.0.0.1:8765`. O `Dockerfile` e o `render.yaml` continuam no repositório para quem quiser hospedar a versão com servidor, mas não são necessários: a Central funciona sem servidor e sem chave de API.

## Reverter

- Site: rode o workflow a partir de um commit anterior, ou desative o Pages em Settings → Pages.
- Dashboard: no Power BI Service, Configurações → Gerenciar códigos de inserção → excluir.
