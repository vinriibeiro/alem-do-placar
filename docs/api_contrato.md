# Contrato da API local (T009 v2)

> A interface pública agora é a **Central de Consulta**, estática: ela lê `dados/<nome>.json`
> (`partidas`, `modelo`, `destaques`, `escudos`, `conhecimento`, `contexto`, `sugestoes`, `config`),
> gerados por `src/api/central.py`. O servidor local serve os mesmos arquivos em `/dados/<nome>.json`.
> Os endpoints abaixo continuam disponíveis para uso local, mas o site não depende deles.

Base: mesma origem do site. Sem CORS aberto. Documentação OpenAPI desativada.

## Endpoints

| Método | Rota | Uso |
|---|---|---|
| GET | `/health` | `{"app": "alem-do-placar", "status": "ok"}` |
| GET | `/api/contexto` | Anos, equipes, métricas do modelo, `temas` e `llm_ativo` |
| GET | `/api/sugestoes` | `{"sugestoes": [8 perguntas de exemplo]}` (amostra aleatória dos temas) |
| POST | `/api/pergunta` | Responde uma pergunta |

### POST `/api/pergunta`

Corpo (campos extras são rejeitados): `pergunta` (3–500 caracteres), `ano` (inteiro, opcional), `equipe` (até 100 caracteres, opcional).

Resposta:

| Campo | Tipo | Observação |
|---|---|---|
| `status` | string | `ok`, `esclarecimento`, `fora_escopo`, `indisponivel`, `insuficiente`, `sem_dados` |
| `texto` | string | Resposta em português |
| `dados` | lista de objetos | Linhas da consulta; vazia quando não há tabela |
| `fonte` | string ou null | Origem dos números |
| `periodo` | string ou null | Período coberto |
| `limitacoes` | lista de strings | Sempre presente |
| `modo` | `"llm"` ou `"deterministico"` | Quem redigiu a resposta |
| `consultas_usadas` | lista de strings | Ferramentas do catálogo executadas (vazia no modo determinístico) |
| `modelo`, `versao_modelo` | string ou null | Modelo preditivo do projeto |

### Códigos HTTP

| Código | Quando |
|---|---|
| 200 | Resposta produzida, inclusive recusas de escopo |
| 400 | Host não permitido |
| 403 | Origem não permitida |
| 413 | Corpo acima de 4096 bytes |
| 422 | Entrada inválida |
| 429 | Mais de `RATE_LIMIT_PER_MIN` perguntas por IP em 60 s (`Retry-After: 60`) |
| 503 | Dados locais indisponíveis |

## Degradação

O teto diário (`LLM_DAILY_LIMIT`), erro de rede, limite de taxa do provedor ou recusa do modelo não geram erro: a resposta vem do modo determinístico, com o motivo como primeira entrada de `limitacoes`. Decisão tomada para a demonstração pública não quebrar quando a cota acaba.

## Variáveis de ambiente

| Variável | Padrão | Função |
|---|---|---|
| `LLM_API_KEY` | vazio | Chave da Claude API. Sem ela, só o modo determinístico |
| `LLM_MODEL` | `claude-opus-5-5` | Modelo do assistente |
| `LLM_DAILY_LIMIT` | 500 | Chamadas ao LLM por dia (processo) |
| `RATE_LIMIT_PER_MIN` | 20 | Perguntas por IP por minuto |
| `ALLOWED_HOSTS` | locais | Hosts extras, separados por vírgula |
| `ALLOWED_ORIGINS` | vazio | Origens extras para POST |
| `TRUST_PROXY` | falso | Usa `X-Forwarded-For` para o IP |
| `POWERBI_EMBED_URL` | vazio | URL do relatório público (usada na F2) |

## Segurança

- A IA nunca escreve SQL nem código. Escolhe ferramentas fechadas com esquema estrito, e os parâmetros são revalidados no servidor.
- Se o modelo não usar nenhuma ferramenta, o texto dele é descartado e a resposta padrão de "não calculável" é devolvida.
- A chave nunca é enviada ao navegador nem registrada. Os logs não contêm o texto das perguntas.
- O prompt do sistema não é exposto por nenhum endpoint.
