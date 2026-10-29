# Roteiro de validação no Power BI Desktop (T008, F3)

Quem executa: Vinícius. Tempo estimado: 20 minutos. Registre o resultado e salve capturas em `docs/qa/T008/capturas/`.

## 1. Abrir

1. Abra `dashboard/powerbi/AlemDoPlacar/AlemDoPlacar.pbip` no Power BI Desktop.
2. Aguarde a carga. Se pedir permissão para ler os arquivos locais, aceite.

| Verificação | Resultado |
|---|---|
| Abre sem mensagem de relatório corrompido | [ ] |
| Carrega 8 tabelas sem erro | [ ] |
| Visão de modelo mostra 7 relacionamentos | [ ] |
| Sem aviso de caminho ambíguo (se houver, desative os relacionamentos de `analitico` e `previsoes`) | [ ] |

Se o Desktop recusar o relatório, anote a mensagem exata e o nome da página. Os pontos mais prováveis são pageNavigator, pivotTable, scatterChart e o formato do tema.

## 2. Aparência

| Verificação | Resultado |
|---|---|
| Fundo da página cinza claro e visuais em cartões brancos com borda | [ ] |
| Cabeçalho azul-marinho com título e subtítulo em todas as páginas | [ ] |
| Navegador de páginas visível abaixo do cabeçalho em todas as páginas | [ ] |
| Cores dos gráficos seguem a paleta azul-marinho, verde, amarelo | [ ] |
| Nenhum texto cortado nos cartões e títulos | [ ] |
| Rodapé legível | [ ] |

## 3. Navegação e filtros

| Verificação | Resultado |
|---|---|
| Clicar no navegador troca de página com Ctrl+clique no Desktop | [ ] |
| Segmentação de temporada filtra os visuais da página | [ ] |
| Segmentação de equipe filtra os visuais da página | [ ] |
| Botão "Clique aqui para perguntar" na página Assistente abre a URL (por enquanto https://ALTERAR) | [ ] |

## 4. Números contra o Python

Rode no terminal e compare com os cartões sem filtros:

```powershell
.\.venv\Scripts\python.exe -c "import pandas as pd; f=pd.read_parquet('data/processed/fato_partidas.parquet'); d=pd.read_parquet('data/processed/fato_desempenho_equipes.parquet'); print(len(f), d.gols_pro.sum()/len(f), (f.resultado=='H').mean())"
```

| Indicador no Power BI | Esperado | Resultado |
|---|---|---|
| Partidas | 3.040 | [ ] |
| Temporadas | 8 | [ ] |
| Gols por jogo | 2,38 | [ ] |
| Vitórias do mandante | 47,6% | [ ] |
| MAE do modelo (holdout) | 0,478 | [ ] |
| MAE do baseline (holdout) | 0,567 | [ ] |
| Visão Geral, temporada 2025: líder da classificação | Flamengo, 79 pontos | [ ] |
| Visão Geral, temporada 2024: líder da classificação | Botafogo, 79 pontos | [ ] |

## 5. Visuais novos (conferir um a um)

| Visual | Resultado |
|---|---|
| Tendências: matriz equipe x temporada mostra aproveitamento em % | [ ] |
| Estatística: dispersão saldo de gols x pontos com um ponto por equipe | [ ] |
| Visão Geral: coluna Posição da tabela preenchida (1, 2, 3...) | [ ] |
| Previsões: linhas de previsto, observado e limites aparecem para uma equipe | [ ] |
| Laboratório: barras de MAE com validação e holdout por modelo | [ ] |

## 6. Desempenho

| Verificação | Resultado |
|---|---|
| Troca de filtro responde em menos de 2 segundos | [ ] |

## 7. Registro

Anexe capturas das 7 páginas. Registre em `docs/qa/T008/resultado_desktop.md` a data, a versão do Power BI Desktop, os itens com falha e as mensagens de erro.
