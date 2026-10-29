# Resultado do teste de fumaça e integridade

- URL: `http://127.0.0.1:8799/site`
- Verificações: 15; falhas: 0

| Categoria | Verificação | Esperado | Resultado | Observação |
|---|---|---|---|---|
| Infraestrutura | GET /index.html | 200 | OK | status 200 |
| Infraestrutura | GET /dashboard.html | 200 | OK | status 200 |
| Infraestrutura | GET /consulta.html | 200 | OK | status 200 |
| Infraestrutura | GET /metodologia.html | 200 | OK | status 200 |
| Infraestrutura | GET /dados/partidas.json | 200 | OK | status 200 |
| Infraestrutura | GET /dados/modelo.json | 200 | OK | status 200 |
| Infraestrutura | GET /dados/conhecimento.json | 200 | OK | status 200 |
| Infraestrutura | GET /dados/destaques.json | 200 | OK | status 200 |
| Infraestrutura | GET /dados/contexto.json | 200 | OK | status 200 |
| Infraestrutura | GET /dados/config.json | 200 | OK | status 200 |
| Segurança | CSP na página | meta Content-Security-Policy | OK |  |
| KPIs | Partidas | 3040 | OK | 3040 |
| KPIs | Temporadas | 8 | OK | 8 |
| KPIs | MAE do modelo | 0.478 | OK | 0.478 |
| KPIs | Cobertura | 91,2% | OK | 0.9121 |
