// Testes das análises ampliadas da Central. Valores esperados conferidos de forma independente
// em Python a partir das tabelas de fatos.
// Uso: CENTRAL_DADOS=<pasta com os JSON> node --test tests/js/analises.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { criarMotor, SEM_INFORMACAO } from "../../src/api/static/js/motor.js";

const pasta = process.env.CENTRAL_DADOS;
const ler = (n) => JSON.parse(readFileSync(join(pasta, `${n}.json`), "utf-8"));
const dados = Object.fromEntries(["partidas", "modelo", "destaques", "escudos", "conhecimento"].map((n) => [n, ler(n)]));
const motor = criarMotor(dados);
const r = (p, f) => motor.responder(p, f);

test("melhor e pior jogo de uma equipe", () => {
  const melhor = r("Qual melhor jogo do Palmeiras em 2025?");
  assert.equal(melhor.tipo, "estatistica");
  assert.match(melhor.texto, /venceu o RB Bragantino por 5 × 1, em casa, em 15\/10\/2025 \(rodada 28\)/);
  assert.equal(melhor.tabela.linhas[0][1], "15/10/2025");
  assert.ok(melhor.nota && melhor.kpis.length === 4 && melhor.relacionados.length >= 3);
  const pior = r("Qual foi o pior jogo do Palmeiras em 2025?");
  assert.match(pior.texto, /perdeu para o Flamengo por 0 × 2/);
  assert.match(r("Maior vitória do Flamengo no histórico").titulo, /Melhor jogo do Flamengo/);
  assert.match(r("Qual foi o último jogo do Santos?").titulo, /Último jogo do Santos FC/);
});

test("melhor ano de uma equipe aceita o intervalo completo", () => {
  const res = r("Qual foi o melhor ano do Vasco de 2018 até 2025?");
  assert.equal(res.tipo, "estatistica");
  assert.match(res.texto, /foi 2024: 10º lugar, com 50 pontos/);
  assert.equal(res.tabela.linhas.length, 6); // 2021 e 2022 fora da Série A
  assert.match(r("Em que ano o Palmeiras foi pior?").titulo, /Pior temporada/);
});

test("intervalo parcial de anos é recusado com explicação", () => {
  const res = r("Melhor ano do Vasco de 2019 até 2022");
  assert.equal(res.tipo, "esclarecimento");
  assert.match(res.texto, /histórico completo/);
});

test("classificação e jogos por rodada", () => {
  const cl = r("Quem liderava o campeonato após a rodada 20 de 2025?");
  assert.match(cl.titulo, /após a rodada 20/);
  assert.deepEqual(cl.tabela.linhas[0].slice(0, 3), [1, "Flamengo", 46]);
  assert.equal(cl.tabela.linhas[1][1], "SE Palmeiras");
  assert.equal(cl.tabela.escudoColuna, 1);
  const jogos = r("Jogos da rodada 5 de 2025");
  assert.equal(jogos.tabela.linhas.length, 10);
  assert.equal(r("Classificação após a rodada 99").tipo, "sem_dados");
});

test("últimos jogos e forma recente", () => {
  const res = r("Últimos 5 jogos do Flamengo em 2025");
  assert.equal(res.tabela.linhas.length, 5);
  assert.match(res.texto, /somou \d+ de 15 pontos/);
  assert.equal(res.kpis[0][0], "Pontos");
  assert.equal(r("Últimos jogos do Corinthians").tabela.linhas.length, 5);
});

test("campeões, títulos e vices", () => {
  const todos = r("Quem foram os campeões de cada temporada?");
  assert.equal(todos.tabela.linhas.length, 8);
  assert.deepEqual(todos.tabela.linhas.map((l) => l[0]), [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]);
  const flamengo = r("Quantos títulos o Flamengo tem?");
  assert.equal(flamengo.kpis[0][0], "Títulos");
  assert.ok(flamengo.kpis[0][1] >= 2);
  assert.ok(r("Quem mais foi campeão?").titulo.startsWith("Campeões"));
});

test("entradas e saídas da Série A e evolução entre temporadas", () => {
  const subiram = r("Quais times subiram em 2025?");
  assert.match(subiram.texto, /não disputaram a Série A de 2024/);
  assert.equal(subiram.tabela.linhas.length, 4);
  assert.equal(r("Quais clubes foram promovidos em 2018?").tipo, "sem_dados");
  const evol = r("Qual equipe mais evoluiu em 2025?");
  assert.match(evol.titulo, /Maior evolução de 2024 para 2025/);
  assert.ok(evol.tabela.linhas.length >= 5);
  assert.match(r("Quem mais caiu em 2025?").titulo, /Maior queda/);
  assert.match(r("O Palmeiras evoluiu de 2024 para 2025?").titulo, /SE Palmeiras: 2024 → 2025/);
});

test("placares, jogo com mais gols e estatísticas do campeonato", () => {
  const comum = r("Qual o placar mais comum?");
  assert.match(comum.texto, /1 × 0.*427 de 3\.040 jogos/);
  assert.equal(comum.tabela.linhas[1][0], "1 × 1");
  assert.match(r("Qual foi o jogo com mais gols?").texto, /Goiás EC 4 × 6 EC Bahia.*07\/10\/2023/);
  const stat = r("Estatísticas do campeonato de 2025");
  assert.equal(stat.kpis.length, 6);
  assert.match(r("Qual foi o melhor jogo do campeonato?").nota, /Não existe um critério objetivo/);
});

test("mando de campo detalhado", () => {
  const res = r("Como o Corinthians vai como mandante e visitante?");
  assert.match(res.texto, /^SC Corinthians Paulista de 2018 a 2025 fez/);
  assert.equal(res.tabela.linhas.length, 2);
  assert.equal(res.tabela.colunas.length, 9);
});

test("novos rankings: jogos sem sofrer gols e aproveitamento", () => {
  assert.equal(r("Quem teve mais jogos sem sofrer gols em 2025?").tipo, "estatistica");
  assert.match(r("Qual o melhor aproveitamento de 2024?").texto, /Botafogo FR/);
});

test("listas de artilheiros e craques", () => {
  const art = r("Quais foram os artilheiros de cada temporada?");
  assert.ok(art.tabela.linhas.length >= 8);
  assert.equal(art.tabela.colunas.length, 4);
  assert.match(art.texto, /Temporadas sem registro na fonte/);
  assert.ok(r("Quem foram os craques do Brasileirão?").tabela.linhas.length >= 6);
});

test("acertos e erros do modelo por equipe", () => {
  const erro = r("Qual equipe o modelo mais errou?");
  assert.equal(erro.tipo, "estatistica");
  assert.equal(erro.tabela.linhas.length, 10);
  const acerto = r("Qual equipe o modelo menos errou?");
  const mae = (x) => Number(x.tabela.linhas[0][2].replace(",", "."));
  assert.ok(mae(erro) >= mae(acerto));
  assert.equal(r("Qual a previsão do modelo para todas as equipes?").tabela.linhas.length, 20);
});

test("resumo de equipe traz indicadores, jogos marcantes e perguntas relacionadas", () => {
  const res = r("Como foi o Flamengo em 2025?");
  assert.equal(res.kpis.length, 8);
  assert.equal(res.kpis[0][1], "1º");
  assert.equal(res.tabela.linhas.length, 6);
  assert.match(res.texto, /Melhor jogo:/);
  assert.ok(res.relacionados.some((p) => p.startsWith("Melhor jogo do Flamengo")));
  assert.equal(r("Resumo do Grêmio").kpis[0][0], "Temporadas");
});

test("perguntas relacionadas são respondidas", () => {
  const res = r("Como foi o Palmeiras em 2024?");
  for (const p of res.relacionados) {
    const outra = r(p);
    assert.notEqual(outra.tipo, "fora_tema", p);
    assert.notEqual(outra.texto, SEM_INFORMACAO, p);
  }
});

test("só o ano mostra a classificação; equipe solta mostra o resumo", () => {
  assert.match(r("Brasileirão 2023").titulo, /Classificação 2023/);
  assert.match(r("Palmeiras").titulo, /SE Palmeiras/);
});

test("painel de curiosidades usa os dados", () => {
  const cards = motor.painel();
  assert.ok(cards.length >= 6);
  assert.match(cards[0].valor, /Flamengo/);
  assert.equal(cards[1].valor, "8 × 0");
  for (const c of cards) {
    assert.ok(c.rotulo && c.valor && c.detalhe && c.pergunta, c.rotulo);
    assert.notEqual(r(c.pergunta).tipo, "fora_tema", c.pergunta);
  }
});

test("bateria ampla: nenhuma pergunta do tema foge ou cai em silêncio", () => {
  const perguntas = [
    "Qual time fez mais gols em 2022?", "Quem tem a pior defesa de 2023?", "Quantas vitórias o Fluminense teve em 2024?",
    "Botafogo em 2024", "Como foi a campanha do Santos em 2019?", "Atlético Mineiro contra Cruzeiro",
    "Compare Grêmio e Internacional em 2023", "Maior sequência de vitórias do Palmeiras", "Qual a maior goleada de 2021?",
    "Como funciona o Brasileirão?", "O que é uma rodada?", "Quantos gols saem por jogo em 2020?",
    "Qual foi a classificação de 2019?", "Quem caiu em 2023?", "Quem foi vice-campeão de 2022?",
    "Pior jogo do Corinthians em 2021", "Quantos jogos o Bahia fez em 2025?", "Quem foi o artilheiro de 2019?",
  ];
  for (const p of perguntas) {
    const res = r(p);
    assert.notEqual(res.tipo, "fora_tema", p);
    assert.ok(res.texto.length > 20, p);
    if (res.tipo === "sem_dados") {
      assert.ok(res.texto.startsWith(SEM_INFORMACAO) || /não disputou|não existe|não há/.test(res.texto), `${p} -> ${res.texto}`);
    }
  }
});
