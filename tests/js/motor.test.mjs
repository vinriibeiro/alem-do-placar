// Testes do motor da Central de Consulta com os dados reais do projeto.
// Uso: CENTRAL_DADOS=<pasta com os JSON> node --test tests/js/motor.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { criarMotor, FORA_DO_TEMA, SEM_INFORMACAO, normalizar } from "../../src/api/static/js/motor.js";

const pasta = process.env.CENTRAL_DADOS;
const ler = (n) => JSON.parse(readFileSync(join(pasta, `${n}.json`), "utf-8"));
const dados = Object.fromEntries(["partidas", "modelo", "destaques", "escudos", "conhecimento"].map((n) => [n, ler(n)]));
const motor = criarMotor(dados);
const r = (p, f) => motor.responder(p, f);
const conhecimento = (p, id) => {
  const res = r(p);
  const item = dados.conhecimento.find((c) => c.id === id);
  assert.equal(res.tipo, "conhecimento", `${p} -> ${res.tipo}: ${res.texto}`);
  assert.equal(res.titulo, item.titulo, `${p} -> ${res.titulo}`);
  return res;
};

// ---------- perguntas de exemplo do pedido ----------
test("melhor ataque de 2025 calculado das partidas", () => {
  const res = r("Qual equipe teve o melhor ataque em 2025?");
  assert.equal(res.tipo, "estatistica");
  assert.match(res.texto, /^Flamengo teve o melhor ataque de 2025: 78 gols marcados em 38 jogos/);
  assert.match(res.fonte, /OpenFootball/);
});

test("perguntas conceituais vão para a base de conhecimento certa", () => {
  conhecimento("Como funciona a classificação?", "classificacao");
  conhecimento("O que significa MAE?", "mae");
  conhecimento("Como o modelo calcula as previsões?", "como-preve");
  conhecimento("Qual algoritmo apresentou o menor erro?", "melhor-modelo");
  conhecimento("O que é saldo médio de gols?", "saldo-medio");
  conhecimento("Qual é a diferença entre treino e teste?", "treino-teste");
  conhecimento("Por que as previsões podem errar?", "por-que-erra");
  conhecimento("Quais dados foram utilizados?", "dados");
  conhecimento("Como foi feita a validação dos modelos?", "validacao");
  conhecimento("Quais são as limitações do projeto?", "limitacoes");
  conhecimento("Como interpretar o gráfico de tendências?", "tendencias");
});

test("respostas da base trazem números reais e origem", () => {
  const res = conhecimento("O que significa MAE?", "mae");
  assert.match(res.texto, new RegExp(String(dados.modelo.mae_teste).replace(".", ",")));
  assert.ok(res.fonte && res.relacionados.length > 0);
});

test("tolera erro de digitação e falta de acento", () => {
  conhecimento("o que significa mae", "mae");
  conhecimento("como funsiona a clasificacao", "classificacao");
});

// ---------- estatísticas ----------
test("classificação respeita a temporada e o desempate", () => {
  const res = r("Qual foi a classificação de 2024?");
  assert.equal(res.titulo, "Classificação 2024");
  assert.equal(res.tabela.linhas.length, 20);
  assert.deepEqual(res.tabela.linhas[0].slice(0, 3), [1, "Botafogo FR", 79]);
  const t = motor.linhas(2024);
  for (let i = 1; i < t.length; i++) {
    const a = t[i - 1], b = t[i];
    assert.ok(a.P > b.P || (a.P === b.P && (a.V > b.V || (a.V === b.V && (a.SG > b.SG || (a.SG === b.SG && a.GP >= b.GP))))));
  }
  assert.equal(res.tabela.linhas[19][9], "Rebaixamento");
});

test("campeão e rebaixados", () => {
  const camp = r("Quem foi o campeão de 2025?");
  assert.match(camp.texto, /^Flamengo foi campeão de 2025 com 79 pontos .*3 à frente do vice SE Palmeiras \(76\)/);
  assert.equal(camp.kpis[0][1], "Flamengo");
  assert.match(r("Quem foi rebaixado em 2025?").texto, /^Rebaixados em 2025/);
});

test("filtros da interface são usados quando a pergunta não traz ano ou equipe", () => {
  assert.equal(r("Qual a melhor defesa?", { ano: 2024 }).titulo, "Melhor defesa de 2024");
  assert.match(r("Como foi o desempenho?", { ano: 2025, equipe: "Flamengo" }).titulo, /^Flamengo em 2025/);
});

test("comparação, confronto, mando, sequência e goleadas", () => {
  assert.match(r("Compare Palmeiras e Flamengo em 2025").texto, /Flamengo fez 79 pontos/);
  const conf = r("Histórico de confrontos entre Flamengo e Palmeiras");
  assert.match(conf.titulo, /^Confrontos/);
  assert.equal(conf.tabela.linhas.length, 16);
  assert.match(r("Como o Corinthians vai como mandante e visitante?").texto, /^SC Corinthians Paulista de 2018 a 2025 fez/);
  assert.match(r("Maior sequência invicta de 2025").texto, /12 jogos seguidos/);
  assert.match(r("Quais foram as maiores goleadas?").texto, /8 × 0/);
  assert.match(r("Quantos gols por jogo no histórico?").texto, /média de 2,38 gols por partida/);
});

test("artilheiro, craque e goleiro vêm dos prêmios reais", () => {
  const art = r("Quem foi o artilheiro de 2025?");
  assert.match(art.texto, /Kaio Jorge \(Cruzeiro EC\) foi o artilheiro de 2025, com 21 gols/);
  assert.equal(art.imagem, null);
  assert.match(art.credito, /Sem foto/);
  const empate = r("Quem foi o artilheiro de 2024?");
  assert.match(empate.texto, /dividiram a artilharia/);
  assert.match(r("Quem foi o craque do Brasileirão de 2021?").texto, /Hulk/);
  const foto = r("Quem foi o craque de 2025?");
  assert.ok(foto.imagem.startsWith("https://") && /CC BY/.test(foto.credito));
});

test("previsão de uma equipe com faixa e aviso", () => {
  const res = r("Qual é a previsão do Flamengo?");
  assert.equal(res.tipo, "estatistica");
  assert.match(res.texto, /faixa de .* a .*estimativa retrospectiva/);
});

// ---------- casos de borda pedidos ----------
test("temporada sem dados", () => {
  const res = r("Qual foi a classificação de 2026?");
  assert.equal(res.tipo, "sem_dados");
  assert.ok(res.texto.startsWith(SEM_INFORMACAO));
  assert.match(res.texto, /2018 a 2025/);
});

test("equipe ausente na temporada", () => {
  const res = r("Como foi a campanha da Chapecoense em 2025?");
  assert.equal(res.tipo, "sem_dados");
  assert.match(res.texto, /não disputou a Série A em 2025/);
});

test("jogador sem fotografia e prêmio não registrado", () => {
  assert.equal(r("Quem foi o melhor goleiro de 2025?").imagem, null);
  const semPremio = r("Quem foi o craque do Brasileirão de 2023?");
  assert.equal(semPremio.tipo, "sem_dados");
  assert.match(semPremio.texto, /não registra/);
});

test("métrica indisponível", () => {
  for (const p of ["Qual o xG do Flamengo em 2025?", "Quantas finalizações o Palmeiras teve?", "Quantos torcedores o Flamengo tem?"]) {
    const res = r(p);
    assert.equal(res.tipo, "sem_dados", p);
    assert.ok(res.texto.startsWith(SEM_INFORMACAO), p);
  }
});

test("consulta ambígua pede esclarecimento", () => {
  const res = r("Como foi o Atlético em 2021?");
  assert.equal(res.tipo, "esclarecimento");
  assert.match(res.texto, /Atlético Goianiense, Atlético Mineiro/);
  assert.match(r("Como foi o Atlético Mineiro em 2021?").texto, /^Atlético Mineiro terminou 2021 em 1º lugar/);
});

test("perguntas fora do assunto são recusadas", () => {
  for (const p of ["Me passa uma receita de bolo de cenoura", "Quem vai ganhar a eleição para presidente?", "Como programar em Python?", "Qual a capital da França?"]) {
    const res = r(p);
    assert.equal(res.tipo, "fora_tema", p);
    assert.equal(res.texto, FORA_DO_TEMA);
  }
});

test("pergunta no tema sem resposta comprovada não inventa", () => {
  const res = r("Qual time tem o melhor uniforme do campeonato?");
  assert.equal(res.tipo, "sem_dados");
  assert.equal(res.texto, SEM_INFORMACAO);
  assert.ok(Array.isArray(res.relacionados));
});

test("normalização e pergunta curta", () => {
  assert.equal(normalizar("  Classificação, São Paulo! "), "classificacao sao paulo");
  assert.equal(r("ab").tipo, "esclarecimento");
});

test("nenhuma resposta estatística sem fonte", () => {
  const perguntas = [
    "Qual a melhor defesa de 2023?", "Resumo do Grêmio", "Maior sequência de derrotas do Santos",
    "Quem teve mais vitórias em 2022?", "Gols por partida em 2020",
  ];
  for (const p of perguntas) {
    const res = r(p);
    assert.equal(res.tipo, "estatistica", `${p}: ${res.texto}`);
    assert.ok(res.fonte, p);
  }
});
