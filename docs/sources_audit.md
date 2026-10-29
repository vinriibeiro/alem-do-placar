# Auditoria de fontes e perfil aprovado (T003)

- **Data:** 2026-10-29
- **Tarefa:** T003 — Adaptador OpenFootball local e auditoria verificável
- **Verificador de licença:** Codex (verificação documental)
- **Escopo:** arquivos `Football.TXT` 2018–2025 baixados pelo controlador no commit `f51b2dcf5e0fab9f0abd5206ab8c24a413e67277`. Nenhuma coleta automática nesta etapa e nenhum dado de 2026.

## 1. Decisão

Fonte selecionada: **OpenFootball, `openfootball_2018_2025`**, perfil em `config/approved_source.toml` (catálogo `versao = "0.1.0"`).

- Licença: CC0-1.0, conforme `LICENSE.md` e `README` oficiais no commit citado.
- `url_termos`: https://github.com/openfootball/south-america/blob/f51b2dcf5e0fab9f0abd5206ab8c24a413e67277/LICENSE.md
- `data_verificacao`: 2026-10-29.
- Justificativa: disponibilidade dos arquivos, licença explícita e validação local do adaptador.

O catálogo anterior, `config/data_sources.toml`, não foi alterado. Nele, as fontes permanecem candidatas.

## 2. Candidatas

| Fonte | Situação nesta revisão |
|---|---|
| OpenFootball | **Selecionada** (perfil `approved_source.toml`). |
| Football-Data (https://www.football-data.co.uk/data.php) | **Não selecionada.** A página de contato (https://football-data.co.uk/contact.php), citada nesta auditoria, restringe o uso a fins pessoais/acadêmicos e a automação leve. Por cautela e pela alternativa CC0 disponível, esta fonte não foi selecionada; esta decisão não é um parecer jurídico. Evidência consultada pelo controlador em 29/10/2026: "The free data offered by Football-Data is intended for private individuals only for personal betting and/or academic interest and research". |
| StatsBomb Open Data | Permanece candidata, sem decisão nesta tarefa. |

## 3. Cobertura e período

- Amostra real auditada: 8 arquivos, 2018 a 2025, 380 partidas por temporada, 3040 no total. Conversão real executada pelo controlador: 3.040 IDs únicos, 20 clubes e 38 jogos por clube por temporada, sem falhas críticas de integridade. Datas e placares aceitos pelo pipeline; arquivos Parquet gerados.
- **2015–2017:** ausente nesta revisão. O período candidato do PRD 2.2 (2015–2025) foi ajustado para 2018–2025 para esta fonte. O PRD 2.2 condiciona o uso à disponibilidade, à cobertura e à licença. O PRD não foi alterado.
- **2026:** excluído. Pelo PRD 2.2, a temporada é reservada para avaliação temporal final, mediante data de corte definida previamente.

## 4. Mapeamento dos 18 campos do PRD

- Campos mínimos com coluna canônica: `partida_id`, `data_partida`, `temporada`, `competicao`, `equipe_mandante`, `equipe_visitante`, `gols_mandante`, `gols_visitante`, `rodada`.
- `resultado`: `derivado` (H/D/A calculado dos gols pelo pipeline).
- Campos complementares indisponíveis no `Football.TXT`: `nao_utilizado` (`finalizacoes`, `finalizacoes_no_alvo`, `posse_de_bola`, `cartoes`, `escanteios`, `xg`, `dias_descanso`, `outras_estatisticas`).
- O perfil não contém a expressão "a verificar".

## 5. Formato e regras do adaptador (`src/ingestion/openfootball.py`)

- Cabeçalho `= Competição AAAA`: o ano precisa coincidir com a temporada.
- Rodada `▪ Matchday N`.
- Data `Dia Mes DD [AAAA]`: sem ano, o ano é o da temporada. Exceção: temporada 2020 em janeiro/fevereiro usa 2021. Ano explícito prevalece. Não há inferência de virada de ano pela diminuição do mês; remarcações fora de ordem mantêm o ano da temporada.
- Partida `[HH:MM] Mandante v Visitante G-G [(i-i)]`: horário e intervalo são aceitos e descartados.
- Comentários (`#`) e linhas vazias são descartados. Qualquer outra linha falha com o número da linha.
- `partida_id` = SHA256 completo de temporada, data ISO e equipes normalizadas. Não usa número de linha.
- Mandante igual ao visitante e partida duplicada falham.

## 6. Aliases de equipes (revisáveis)

A forma canônica de cada par é uma decisão de revisão. Ela segue a forma listada nesta auditoria. Inventário de 54 nomes reais conferido contra os oito arquivos pelo controlador, sem inferência aproximada. A tabela completa abaixo registra as correspondências efetivas.

| Alias (forma encontrada) | Forma canônica |
|---|---|
| AC Goianiense | Atlético Goianiense |
| América MG | América Mineiro |
| CA Paranaense | Athletico Paranaense |
| CA Mineiro | Atlético Mineiro |
| Bahia BA | EC Bahia |
| Botafogo RJ | Botafogo FR |
| Ceará CE | Ceará SC |
| Corinthians SP | SC Corinthians Paulista |
| Coritiba PR | Coritiba FBC |
| Cruzeiro | Cruzeiro EC |
| Cuiabá MT | Cuiabá EC |
| Flamengo RJ | CR Flamengo |
| Fluminense RJ | Fluminense FC |
| Fortaleza CE | Fortaleza EC |
| Goiás GO | Goiás EC |
| Grêmio Porto Alegre | Grêmio FBPA |
| Internacional | SC Internacional |
| Juventude RS | EC Juventude |
| Palmeiras | SE Palmeiras |
| Red Bull Bragantino | RB Bragantino |
| Sport Recife PE | SC Recife |
| Vasco da Gama RJ | CR Vasco da Gama |
| Vitória BA | EC Vitória |

Nomes fora da tabela são preservados com espaços normalizados. Não há alias aproximado. Os nomes não mapeados devem ser listados na conferência com os arquivos reais.

## 7. Riscos registrados

- Nomes não cobertos pela tabela de aliases.
- Remarcações mudam a data e, portanto, o `partida_id`.
- Campos complementares indisponíveis.
- Datas e placares validados localmente não equivalem a conferência independente contra a CBF.
- Verificação de licença documental, sem revisão humana registrada.

## 8. Testes e instalação

- Testes: `tests/unit/test_openfootball.py`, com texto sintético, `tmp_path` e sem rede.
- Comandos previstos (não executados nesta etapa): `python -m pip install -e ".[test,lint]"` e `python -B -m pytest tests/unit/test_openfootball.py`.
- Dependências novas: nenhuma. O módulo usa a biblioteca padrão e `processing.padronizacao.normalizar_texto`. O `pyproject.toml` não foi alterado.
- Estado: a execução dos testes e a conferência dos arquivos reais ficam com o controlador. Nenhum resultado de teste é afirmado aqui.

## 9. Evidência de execução real

Commit fixo: f51b2dcf5e0fab9f0abd5206ab8c24a413e67277

| Temporada | Partidas | Clubes | Data inicial | Data final | SHA256 do arquivo |
|---|---:|---:|---|---|---|
| 2018 | 380 | 20 | 2018-04-14 | 2018-12-02 | 29d3aff9298bb3ffc93dc90f728825d0db412a518064417265ebd40d63d2a122 |
| 2019 | 380 | 20 | 2019-04-27 | 2019-12-08 | 6eb300a0160adf2e34e2caa372fb29ec0340c6e69d69f349e895fbc297536ad7 |
| 2020 | 380 | 20 | 2020-08-08 | 2021-02-25 | 5ff13ca1b4b2209453948cd0a0ab46bfadb081fe84fc920bfa21dc88676316aa |
| 2021 | 380 | 20 | 2021-05-29 | 2021-12-09 | 0f5c18cadd5828126113bbbaf09eb56c6001fed728a2242f65493e169c25cdfa |
| 2022 | 380 | 20 | 2022-04-09 | 2022-11-13 | 83e1445ee9962700c1534bd762a7586f37de21a4e7ca88b31d86a5b1937fda3f |
| 2023 | 380 | 20 | 2023-04-15 | 2023-12-06 | c05ee51787ae8c577da81352c5a0db3e895e6baf02fdd8514ffc670d878da3f3 |
| 2024 | 380 | 20 | 2024-04-13 | 2024-12-08 | 9c39f868c78e85e53758482a2138d986b412606af541cc65cba88af211c1860d |
| 2025 | 380 | 20 | 2025-03-29 | 2025-12-07 | d7114ce4e6194239f11ff3bef2e9ad1d86a7b35ac4d61359e73670cfc7032806 |

### Inventário completo conferido

| Nome encontrado | Forma canônica do adaptador |
|---|---|
| AC Goianiense | Atlético Goianiense |
| América MG | América Mineiro |
| América Mineiro | América Mineiro |
| Athletico Paranaense | Athletico Paranaense |
| Atlético Goianiense | Atlético Goianiense |
| Atlético Mineiro | Atlético Mineiro |
| Avaí SC | Avaí SC |
| Bahia BA | EC Bahia |
| Botafogo FR | Botafogo FR |
| Botafogo RJ | Botafogo FR |
| CA Mineiro | Atlético Mineiro |
| CA Paranaense | Athletico Paranaense |
| CR Flamengo | CR Flamengo |
| CR Vasco da Gama | CR Vasco da Gama |
| CSA AL | CSA AL |
| Ceará CE | Ceará SC |
| Ceará SC | Ceará SC |
| Chapecoense | Chapecoense |
| Corinthians SP | SC Corinthians Paulista |
| Coritiba FBC | Coritiba FBC |
| Coritiba PR | Coritiba FBC |
| Criciúma EC | Criciúma EC |
| Cruzeiro EC | Cruzeiro EC |
| Cruzeiro | Cruzeiro EC |
| Cuiabá EC | Cuiabá EC |
| Cuiabá MT | Cuiabá EC |
| EC Bahia | EC Bahia |
| EC Juventude | EC Juventude |
| EC Vitória | EC Vitória |
| Flamengo RJ | CR Flamengo |
| Fluminense FC | Fluminense FC |
| Fluminense RJ | Fluminense FC |
| Fortaleza CE | Fortaleza EC |
| Fortaleza EC | Fortaleza EC |
| Goiás EC | Goiás EC |
| Goiás GO | Goiás EC |
| Grêmio FBPA | Grêmio FBPA |
| Grêmio Porto Alegre | Grêmio FBPA |
| Internacional | SC Internacional |
| Juventude RS | EC Juventude |
| Mirassol FC | Mirassol FC |
| Palmeiras | SE Palmeiras |
| Paraná Clube | Paraná Clube |
| RB Bragantino | RB Bragantino |
| Red Bull Bragantino | RB Bragantino |
| SC Corinthians Paulista | SC Corinthians Paulista |
| SC Internacional | SC Internacional |
| SC Recife | SC Recife |
| SE Palmeiras | SE Palmeiras |
| Santos FC | Santos FC |
| Sport Recife PE | SC Recife |
| São Paulo FC | São Paulo FC |
| Vasco da Gama RJ | CR Vasco da Gama |
| Vitória BA | EC Vitória |
