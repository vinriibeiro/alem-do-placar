// Motor da Central de Consulta: identifica o assunto, calcula estatísticas a partir das
// partidas e busca na base de conhecimento. Funções puras, sem DOM e sem rede (testável em Node).

export const FORA_DO_TEMA =
  "Esta central foi desenvolvida para esclarecer dúvidas sobre o Campeonato Brasileiro, os indicadores, os dados e os modelos deste projeto. Escolha um desses assuntos para continuar.";
export const SEM_INFORMACAO =
  "Não encontrei informações suficientes nos dados disponíveis para responder com segurança.";

const FONTE_PARTIDAS = "Calculado a partir das partidas do OpenFootball (CC0)";

const PARADAS = new Set(
  ("a o os as um uma uns umas de do da dos das em no na nos nas por para pra pelo pela com sem e ou " +
    "que qual quais quem quando onde como foi foram era ser sao e eh me mim voce voces seu sua isso " +
    "esse essa este esta aquele aquela ao aos se ja mais muito pouco tem teve ter tinha sobre entre " +
    "la lhe nao sim ate ha o que la").split(" "),
);

const DOMINIO = [
  "futebol", "campeonat", "brasileir", "serie", "time", "equipe", "clube", "jogo", "jogos", "partida", "gol",
  "ponto", "tabela", "classific", "rebaix", "campea", "campeo", "lider", "artilh", "goleir", "craque", "jogador",
  "modelo", "previs", "preve", "dado", "metric", "mae", "rmse", "erro", "variav", "atribut", "valid", "trein",
  "teste", "metodolog", "dashboard", "grafic", "central", "projeto", "temporad", "rodad", "vitori", "empat",
  "derrot", "saldo", "aproveit", "mandant", "visitant", "mando", "ataque", "defesa", "sequenc", "invict",
  "confront", "tendenc", "media", "movel", "algoritm", "ridge", "forest", "boosting", "baseline", "referenc",
  "importanc", "vazament", "limitac", "fonte", "openfootball", "libertadores", "sul", "zona", "escud", "xg",
  "finaliz", "posse", "desempat", "desempenh", "campanha", "uniforme", "torc", "oscila", "consisten", "regular", "volatil", "faixa", "intervalo", "incertez",
  "cobertur", "vies", "aposta", "power", "bi", "indicador", "estatist", "goleada", "placar",
];
const FORA = [
  "receita", "bolo", "cozinh", "politic", "eleic", "president", "governo", "deputad", "senador", "bitcoin",
  "cripto", "acoes da bolsa", "bolsa de valores", "dolar", "clima", "tempo amanha", "chuva", "filme", "serie de tv", "novela",
  "musica", "javascript", "html", "css", "programar", "programacao", "linguagem de", "medic", "remedio",
  "doenca", "viagem", "horoscopo", "namor", "piada",
];
const CONCEITO = [
  "o que e", "o que sao", "o que significa", "o que significam", "como funciona", "como se calcula",
  "como e calculad", "como foi calculad", "como foi feita", "como foram", "por que", "porque", "explique",
  "explica", "diferenca", "como interpretar", "como ler", "para que serve", "quais sao os criterios",
  "de onde vem", "como o modelo", "o modelo usa", "existe vazamento", "como e feita", "quais dados",
  "quais variaveis", "quais modelos", "qual e a variavel", "o que estamos", "e confiavel", "sao confiaveis",
];
const GENERICOS_EQUIPE = new Set([
  "fc", "ec", "sc", "se", "cr", "rb", "al", "clube", "esporte", "futebol", "sport", "de", "da", "do", "club",
  "paulista", "associacao",
]);
const APELIDOS = {
  galo: "Atlético Mineiro", "atletico mineiro": "Atlético Mineiro", "atletico mg": "Atlético Mineiro",
  "atletico goianiense": "Atlético Goianiense", "atletico go": "Atlético Goianiense", dragao: "Atlético Goianiense",
  athletico: "Athletico Paranaense", "atletico pr": "Athletico Paranaense", "atletico paranaense": "Athletico Paranaense",
  furacao: "Athletico Paranaense", cap: "Athletico Paranaense", timao: "SC Corinthians Paulista",
  corinthians: "SC Corinthians Paulista", verdao: "SE Palmeiras", mengao: "Flamengo", fogao: "Botafogo FR",
  peixe: "Santos FC", inter: "SC Internacional", colorado: "SC Internacional", "sao paulo": "São Paulo FC",
  spfc: "São Paulo FC", sport: "SC Recife", "sport recife": "SC Recife", bragantino: "RB Bragantino",
  "red bull": "RB Bragantino", vasco: "CR Vasco da Gama", "vasco da gama": "CR Vasco da Gama", leao: "Fortaleza EC",
  vozao: "Ceará SC", "america mineiro": "América Mineiro", "america mg": "América Mineiro", chape: "Chapecoense",
  coxa: "Coritiba FBC", tigre: "Criciúma EC", raposa: "Cruzeiro EC", dourado: "Cuiabá EC", tricolor: null,
};

export function normalizar(texto) {
  return String(texto || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9%\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function palavras(texto) {
  return normalizar(texto)
    .split(" ")
    .filter((t) => t && !PARADAS.has(t));
}

function distancia(a, b) {
  if (Math.abs(a.length - b.length) > 1) return 2;
  const m = a.length;
  const n = b.length;
  const d = Array.from({ length: m + 1 }, (_, i) => [i, ...Array(n).fill(0)]);
  for (let j = 1; j <= n; j++) d[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
  }
  return d[m][n];
}

const fmt = (n, casas = 0) =>
  Number(n).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
const pct = (n) => `${fmt(n * 100, 1)}%`;
const dataBR = (iso) => iso.split("-").reverse().join("/");

export function criarMotor(dados) {
  const { equipes } = dados.partidas;
  const jogos = dados.partidas.partidas.map(([ano, data, m, v, gm, gv]) => ({
    ano, data, mandante: equipes[m], visitante: equipes[v], gm, gv,
  }));
  const anos = [...new Set(jogos.map((j) => j.ano))].sort((a, b) => a - b);
  const ultimoAno = anos[anos.length - 1];
  const modelo = dados.modelo;
  const conhecimento = dados.conhecimento || [];
  const destaques = dados.destaques || [];
  const escudos = dados.escudos || {};

  // ---------- índice de equipes ----------
  const porToken = new Map();
  for (const e of equipes) {
    for (const t of normalizar(e).split(" ")) {
      if (t.length < 3 || GENERICOS_EQUIPE.has(t)) continue;
      if (!porToken.has(t)) porToken.set(t, new Set());
      porToken.get(t).add(e);
    }
  }

  function detectarEquipes(texto) {
    let resto = ` ${normalizar(texto)} `;
    const achadas = [];
    const ambiguos = [];
    const multi = Object.keys(APELIDOS).filter((k) => k.includes(" ")).sort((a, b) => b.length - a.length);
    for (const k of multi) {
      if (resto.includes(` ${k} `) && APELIDOS[k]) {
        achadas.push(APELIDOS[k]);
        resto = resto.replace(` ${k} `, " ");
      }
    }
    for (const e of equipes) {
      const n = ` ${normalizar(e)} `;
      if (resto.includes(n)) {
        achadas.push(e);
        resto = resto.replace(n, " ");
      }
    }
    for (const t of resto.trim().split(" ")) {
      if (!t) continue;
      if (t in APELIDOS) {
        if (APELIDOS[t]) achadas.push(APELIDOS[t]);
        continue;
      }
      const alvo = porToken.get(t);
      if (!alvo) continue;
      if (alvo.size === 1) achadas.push([...alvo][0]);
      else ambiguos.push([...alvo].sort());
    }
    return { equipes: [...new Set(achadas)], ambiguos };
  }

  function detectarAnos(texto) {
    return [...new Set((normalizar(texto).match(/\b(19|20)\d{2}\b/g) || []).map(Number))];
  }

  // ---------- cálculos ----------
  function linhas(ano) {
    const tab = new Map();
    const reg = (eq, gp, gc) => {
      if (!tab.has(eq)) tab.set(eq, { equipe: eq, J: 0, V: 0, E: 0, D: 0, GP: 0, GC: 0, casaJ: 0, casaP: 0, foraJ: 0, foraP: 0 });
      const r = tab.get(eq);
      r.J += 1; r.GP += gp; r.GC += gc;
      if (gp > gc) r.V += 1; else if (gp === gc) r.E += 1; else r.D += 1;
      return r;
    };
    for (const j of jogos) {
      if (ano && j.ano !== ano) continue;
      const m = reg(j.mandante, j.gm, j.gv);
      const v = reg(j.visitante, j.gv, j.gm);
      m.casaJ += 1; m.casaP += j.gm > j.gv ? 3 : j.gm === j.gv ? 1 : 0;
      v.foraJ += 1; v.foraP += j.gv > j.gm ? 3 : j.gv === j.gm ? 1 : 0;
    }
    const out = [...tab.values()].map((r) => ({ ...r, P: 3 * r.V + r.E, SG: r.GP - r.GC }));
    out.sort((a, b) => b.P - a.P || b.V - a.V || b.SG - a.SG || b.GP - a.GP || a.equipe.localeCompare(b.equipe));
    out.forEach((r, i) => { r.pos = i + 1; r.aprov = r.P / (3 * r.J); });
    return out;
  }

  function sequencia(equipe, ano, regra) {
    let melhor = 0, atual = 0, ini = null, fim = null, iniAtual = null;
    for (const j of jogos) {
      if ((ano && j.ano !== ano) || (j.mandante !== equipe && j.visitante !== equipe)) continue;
      const [gp, gc] = j.mandante === equipe ? [j.gm, j.gv] : [j.gv, j.gm];
      const pts = gp > gc ? 3 : gp === gc ? 1 : 0;
      if (regra(pts)) {
        atual += 1;
        if (atual === 1) iniAtual = j.data;
        if (atual > melhor) { melhor = atual; ini = iniAtual; fim = j.data; }
      } else atual = 0;
    }
    return { equipe, melhor, ini, fim };
  }

  // ---------- respostas ----------
  const resposta = (tipo, titulo, texto, extra = {}) => ({ tipo, titulo, texto, ...extra });
  const tabelaLinhas = (colunas, linhasT) => ({ colunas, linhas: linhasT });

  function validarAno(ano) {
    if (ano && !anos.includes(ano)) {
      return resposta("sem_dados", `Temporada ${ano}`,
        `${SEM_INFORMACAO} A temporada ${ano} não está nos dados; as temporadas disponíveis vão de ${anos[0]} a ${ultimoAno}.`,
        { fonte: FONTE_PARTIDAS });
    }
    return null;
  }

  function equipeNoAno(equipe, ano) {
    return jogos.some((j) => j.ano === ano && (j.mandante === equipe || j.visitante === equipe));
  }

  function zona(pos) {
    if (pos <= 4) return "Libertadores";
    if (pos <= 6) return "Pré-Libertadores";
    if (pos <= 12) return "Sul-Americana";
    if (pos >= 17) return "Rebaixamento";
    return "";
  }

  function rClassificacao(ano, { topo = 20, rebaixados = false } = {}) {
    const t = linhas(ano);
    const lider = t[0];
    let selec = t;
    let texto = `${lider.equipe} terminou ${ano} em 1º lugar, com ${lider.P} pontos em ${lider.J} jogos (${pct(lider.aprov)} de aproveitamento).`;
    if (rebaixados) {
      selec = t.filter((r) => r.pos >= 17);
      texto = `Rebaixados em ${ano} (17º a 20º): ${selec.map((r) => r.equipe).join(", ")}.`;
    } else if (topo < 20) selec = t.slice(0, topo);
    return resposta("estatistica", `Classificação ${ano}`, texto, {
      tabela: tabelaLinhas(["Pos.", "Equipe", "P", "J", "V", "E", "D", "SG", "Aprov.", "Zona"],
        selec.map((r) => [r.pos, r.equipe, r.P, r.J, r.V, r.E, r.D, r.SG, pct(r.aprov), zona(r.pos)])),
      fonte: `${FONTE_PARTIDAS}. Desempate: pontos, vitórias, saldo e gols marcados.`,
      pagina: "dashboard.html",
    });
  }

  const METRICAS = {
    ataque: { rotulo: "melhor ataque", campo: (r) => r.GP, desc: true, txt: (r) => `${r.GP} gols marcados` },
    defesa: { rotulo: "melhor defesa", campo: (r) => r.GC, desc: false, txt: (r) => `${r.GC} gols sofridos` },
    pior_ataque: { rotulo: "pior ataque", campo: (r) => r.GP, desc: false, txt: (r) => `${r.GP} gols marcados` },
    pior_defesa: { rotulo: "pior defesa", campo: (r) => r.GC, desc: true, txt: (r) => `${r.GC} gols sofridos` },
    saldo: { rotulo: "maior saldo de gols", campo: (r) => r.SG, desc: true, txt: (r) => `saldo ${r.SG > 0 ? "+" : ""}${r.SG}` },
    vitorias: { rotulo: "mais vitórias", campo: (r) => r.V, desc: true, txt: (r) => `${r.V} vitórias` },
    empates: { rotulo: "mais empates", campo: (r) => r.E, desc: true, txt: (r) => `${r.E} empates` },
    derrotas: { rotulo: "mais derrotas", campo: (r) => r.D, desc: true, txt: (r) => `${r.D} derrotas` },
    mandante: { rotulo: "melhor mandante", campo: (r) => r.casaP / r.casaJ, desc: true, txt: (r) => `${fmt(r.casaP / r.casaJ, 2)} pontos por jogo em casa` },
    visitante: { rotulo: "melhor visitante", campo: (r) => r.foraP / r.foraJ, desc: true, txt: (r) => `${fmt(r.foraP / r.foraJ, 2)} pontos por jogo fora` },
  };

  function rRanking(chave, ano) {
    const m = METRICAS[chave];
    const t = linhas(ano).slice().sort((a, b) => (m.desc ? m.campo(b) - m.campo(a) : m.campo(a) - m.campo(b)));
    const topo = t[0];
    const empatados = t.filter((r) => m.campo(r) === m.campo(topo)).map((r) => r.equipe);
    return resposta("estatistica", `${m.rotulo[0].toUpperCase()}${m.rotulo.slice(1)} de ${ano}`,
      `${empatados.join(" e ")} ${empatados.length > 1 ? "tiveram" : "teve"} o ${m.rotulo} de ${ano}: ${m.txt(topo)} em ${topo.J} jogos.`,
      {
        tabela: tabelaLinhas(["#", "Equipe", "Valor", "Jogos"], t.slice(0, 5).map((r, i) => [i + 1, r.equipe, m.txt(r), r.J])),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[topo.equipe] || null,
      });
  }

  function rResumo(equipe, ano) {
    if (ano) {
      if (!equipeNoAno(equipe, ano)) {
        return resposta("sem_dados", equipe, `${equipe} não disputou a Série A em ${ano} nos dados disponíveis.`, { fonte: FONTE_PARTIDAS });
      }
      const r = linhas(ano).find((x) => x.equipe === equipe);
      return resposta("estatistica", `${equipe} em ${ano}`,
        `${equipe} terminou ${ano} em ${r.pos}º lugar, com ${r.P} pontos, ${r.V} vitórias, ${r.E} empates e ${r.D} derrotas, saldo de gols ${r.SG > 0 ? "+" : ""}${r.SG} e ${pct(r.aprov)} de aproveitamento.`,
        { tabela: tabelaLinhas(["Pos.", "P", "J", "V", "E", "D", "GP", "GC", "SG", "Aprov."], [[r.pos, r.P, r.J, r.V, r.E, r.D, r.GP, r.GC, r.SG, pct(r.aprov)]]),
          fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null });
    }
    const porAno = anos.filter((a) => equipeNoAno(equipe, a)).map((a) => ({ ano: a, ...linhas(a).find((x) => x.equipe === equipe) }));
    const tot = porAno.reduce((s, r) => ({ J: s.J + r.J, P: s.P + r.P, V: s.V + r.V }), { J: 0, P: 0, V: 0 });
    const melhor = porAno.slice().sort((a, b) => a.pos - b.pos)[0];
    return resposta("estatistica", `${equipe} de ${anos[0]} a ${ultimoAno}`,
      `${equipe} disputou ${porAno.length} das ${anos.length} temporadas: ${tot.J} jogos, ${tot.V} vitórias e ${tot.P} pontos (${pct(tot.P / (3 * tot.J))} de aproveitamento). Melhor campanha: ${melhor.pos}º lugar em ${melhor.ano}.`,
      { tabela: tabelaLinhas(["Temporada", "Pos.", "P", "V", "E", "D", "SG"], porAno.map((r) => [r.ano, r.pos, r.P, r.V, r.E, r.D, r.SG])),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null });
  }

  function rComparar(a, b, ano) {
    const t = linhas(ano);
    const ra = t.find((x) => x.equipe === a);
    const rb = t.find((x) => x.equipe === b);
    const ref = ano ? `em ${ano}` : `de ${anos[0]} a ${ultimoAno}`;
    if (!ra || !rb) {
      const falta = !ra ? a : b;
      return resposta("sem_dados", "Comparação", `${falta} não disputou a Série A ${ref} nos dados disponíveis.`, { fonte: FONTE_PARTIDAS });
    }
    return resposta("estatistica", `${a} × ${b} ${ref}`,
      `${ref[0].toUpperCase()}${ref.slice(1)}, ${a} fez ${ra.P} pontos (${pct(ra.aprov)}) e ${b} fez ${rb.P} (${pct(rb.aprov)}).` +
        (ano ? ` Posições: ${a} ${ra.pos}º e ${b} ${rb.pos}º.` : " Totais acumulados dependem de quantas temporadas cada equipe disputou."),
      { tabela: tabelaLinhas(["Equipe", "P", "J", "V", "E", "D", "SG", "Aprov."], [ra, rb].map((r) => [r.equipe, r.P, r.J, r.V, r.E, r.D, r.SG, pct(r.aprov)])),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html" });
  }

  function rConfronto(a, b, ano) {
    const lista = jogos.filter((j) => (!ano || j.ano === ano) && ((j.mandante === a && j.visitante === b) || (j.mandante === b && j.visitante === a)));
    if (!lista.length) return resposta("sem_dados", `${a} × ${b}`, `Não há confrontos entre ${a} e ${b}${ano ? ` em ${ano}` : ""} nos dados.`, { fonte: FONTE_PARTIDAS });
    let va = 0, vb = 0, emp = 0, ga = 0, gb = 0;
    for (const j of lista) {
      const [x, y] = j.mandante === a ? [j.gm, j.gv] : [j.gv, j.gm];
      ga += x; gb += y;
      if (x > y) va += 1; else if (x < y) vb += 1; else emp += 1;
    }
    return resposta("estatistica", `Confrontos: ${a} × ${b}`,
      `Em ${lista.length} jogos${ano ? ` em ${ano}` : ` de ${anos[0]} a ${ultimoAno}`}, ${a} venceu ${va}, ${b} venceu ${vb} e houve ${emp} empates. Gols: ${a} ${ga} × ${gb} ${b}.`,
      { tabela: tabelaLinhas(["Data", "Mandante", "Placar", "Visitante"], lista.map((j) => [dataBR(j.data), j.mandante, `${j.gm} × ${j.gv}`, j.visitante])),
        fonte: FONTE_PARTIDAS });
  }

  function rMando(equipe, ano) {
    const t = linhas(ano);
    const alvo = equipe ? t.filter((r) => r.equipe === equipe) : t;
    if (!alvo.length) return resposta("sem_dados", "Mando de campo", `${equipe} não disputou a Série A${ano ? ` em ${ano}` : ""} nos dados.`, { fonte: FONTE_PARTIDAS });
    const s = alvo.reduce((acc, r) => ({ cj: acc.cj + r.casaJ, cp: acc.cp + r.casaP, fj: acc.fj + r.foraJ, fp: acc.fp + r.foraP }), { cj: 0, cp: 0, fj: 0, fp: 0 });
    const ref = ano ? ` em ${ano}` : ` de ${anos[0]} a ${ultimoAno}`;
    const sujeito = equipe ? `${equipe}${ref} fez` : `As equipes${ref} fizeram`;
    return resposta("estatistica", `Mando de campo${equipe ? `: ${equipe}` : ""}`,
      `${sujeito} ${fmt(s.cp / s.cj, 2)} pontos por jogo em casa e ${fmt(s.fp / s.fj, 2)} fora.`,
      { tabela: tabelaLinhas(["Mando", "Jogos", "Pontos por jogo"], [["Em casa", s.cj, fmt(s.cp / s.cj, 2)], ["Fora", s.fj, fmt(s.fp / s.fj, 2)]]),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html" });
  }

  function rGols(ano, goleadas) {
    const lista = jogos.filter((j) => !ano || j.ano === ano);
    const total = lista.reduce((s, j) => s + j.gm + j.gv, 0);
    const ref = ano ? `em ${ano}` : `de ${anos[0]} a ${ultimoAno}`;
    if (goleadas) {
      const top = lista.slice().sort((a, b) => Math.abs(b.gm - b.gv) - Math.abs(a.gm - a.gv) || b.gm + b.gv - (a.gm + a.gv)).slice(0, 5);
      return resposta("estatistica", `Maiores goleadas ${ref}`,
        `A maior goleada ${ref} foi ${top[0].mandante} ${top[0].gm} × ${top[0].gv} ${top[0].visitante}, em ${dataBR(top[0].data)}.`,
        { tabela: tabelaLinhas(["Data", "Mandante", "Placar", "Visitante"], top.map((j) => [dataBR(j.data), j.mandante, `${j.gm} × ${j.gv}`, j.visitante])), fonte: FONTE_PARTIDAS });
    }
    const porAno = anos.filter((a) => !ano || a === ano).map((a) => {
      const l = jogos.filter((j) => j.ano === a);
      return [a, l.length, fmt(l.reduce((s, j) => s + j.gm + j.gv, 0) / l.length, 2)];
    });
    return resposta("estatistica", `Gols por partida ${ref}`,
      `Foram ${fmt(total)} gols em ${fmt(lista.length)} partidas ${ref}: média de ${fmt(total / lista.length, 2)} gols por partida.`,
      { tabela: tabelaLinhas(["Temporada", "Partidas", "Gols por partida"], porAno), fonte: FONTE_PARTIDAS });
  }

  const TIPOS_SEQ = {
    invicta: { rot: "sem perder", regra: (p) => p >= 1 },
    vitorias: { rot: "de vitórias", regra: (p) => p === 3 },
    derrotas: { rot: "de derrotas", regra: (p) => p === 0 },
    sem_vencer: { rot: "sem vencer", regra: (p) => p <= 1 },
  };

  function rSequencia(tipo, equipe, ano) {
    const t = TIPOS_SEQ[tipo];
    const alvos = equipe ? [equipe] : equipes;
    const res = alvos.map((e) => sequencia(e, ano, t.regra)).filter((r) => r.melhor > 0).sort((a, b) => b.melhor - a.melhor);
    const ref = ano ? `em ${ano}` : `de ${anos[0]} a ${ultimoAno}`;
    if (!res.length) return resposta("sem_dados", "Sequências", `Não há sequências ${t.rot} para esse filtro.`, { fonte: FONTE_PARTIDAS });
    const top = res[0];
    return resposta("estatistica", `Maior sequência ${t.rot} ${ref}`,
      `${top.equipe} teve a maior sequência ${t.rot} ${ref}: ${top.melhor} jogos seguidos, de ${dataBR(top.ini)} a ${dataBR(top.fim)}.` +
        (ano ? "" : " Sem filtro de temporada, a sequência pode atravessar o fim de uma temporada."),
      { tabela: tabelaLinhas(["Equipe", "Jogos", "Início", "Fim"], res.slice(0, 5).map((r) => [r.equipe, r.melhor, dataBR(r.ini), dataBR(r.fim)])), fonte: FONTE_PARTIDAS });
  }

  const CATEGORIAS_DESTAQUE = {
    artilheiro: "Artilheiro",
    craque: "Craque do Brasileirão",
    goleiro: "Melhor goleiro",
  };

  function rDestaque(categoria, ano) {
    const lista = destaques.filter((d) => d.ano === ano && d.categoria === categoria);
    const fonteWiki = lista[0]?.fonte;
    if (!lista.length) {
      return resposta("sem_dados", `${CATEGORIAS_DESTAQUE[categoria]} ${ano}`,
        `${SEM_INFORMACAO} A fonte consultada (Wikipédia) não registra o ${CATEGORIAS_DESTAQUE[categoria].toLowerCase()} de ${ano}.`, { fonte: "Wikipédia em português" });
    }
    const nomes = lista.map((d) => `${d.jogador} (${d.clube})`).join(" e ");
    let texto;
    if (categoria === "artilheiro") texto = `${nomes} ${lista.length > 1 ? "dividiram a artilharia" : "foi o artilheiro"} de ${ano}, com ${lista[0].gols} gols.`;
    else if (categoria === "craque") texto = `${nomes} recebeu o prêmio de Craque do Brasileirão de ${ano}, escolhido oficialmente pela CBF.`;
    else texto = `${nomes} recebeu o prêmio de melhor goleiro de ${ano}, escolhido oficialmente pela CBF. Os dados não têm gols sofridos por goleiro; pergunte pela melhor defesa para ver os gols sofridos pelos clubes.`;
    const comFoto = lista.find((d) => d.foto);
    return resposta("estatistica", `${CATEGORIAS_DESTAQUE[categoria]} ${ano}`, texto, {
      fonte: `Wikipédia em português, página da temporada ${ano}`,
      link: fonteWiki || null,
      imagem: comFoto ? comFoto.foto : null,
      credito: comFoto ? `Foto: ${comFoto.credito} · Wikimedia Commons` : "Sem foto com licença livre disponível.",
      pagina: "dashboard.html",
    });
  }

  function rPrevisao(equipe) {
    const lista = modelo.previsoes.filter((p) => p[0] === equipe);
    if (!lista.length) {
      return resposta("sem_dados", `Previsão: ${equipe}`, `${SEM_INFORMACAO} Não há previsões para ${equipe}: as previsões cobrem apenas as equipes de ${modelo.ano_teste}.`, { fonte: "Previsões do modelo" });
    }
    const [, data, prev, inf, sup, real] = lista[lista.length - 1];
    const erros = lista.filter((p) => p[5] !== null).map((p) => Math.abs(p[2] - p[5]));
    const mae = erros.reduce((s, e) => s + e, 0) / erros.length;
    return resposta("estatistica", `Previsão: ${equipe}`,
      `Na última previsão de ${modelo.ano_teste} (${dataBR(data)}), o modelo estimou ${fmt(prev, 2)} ponto por jogo para os 5 jogos seguintes, numa faixa de ${fmt(inf, 2)} a ${fmt(sup, 2)}.` +
        (real !== null ? ` O resultado real foi ${fmt(real, 2)}.` : "") +
        ` Nas ${lista.length} previsões de ${equipe} em ${modelo.ano_teste}, o erro médio foi ${fmt(mae, 2)}. É uma estimativa retrospectiva, não uma certeza.`,
      { tabela: tabelaLinhas(["Data", "Previsto", "Faixa de 90%", "Real"], lista.slice(-6).map((p) => [dataBR(p[1]), fmt(p[2], 2), `${fmt(p[3], 2)} a ${fmt(p[4], 2)}`, p[5] === null ? "—" : fmt(p[5], 2)])),
        fonte: `Previsões do modelo ${modelo.modelo_nome} (${modelo.versao}), teste com ${modelo.ano_teste}`, pagina: "dashboard.html" });
  }

  // ---------- base de conhecimento ----------
  const indice = conhecimento.map((item) => {
    const termos = new Map();
    const add = (t, peso) => { if (t.length > 1) termos.set(t, Math.max(termos.get(t) || 0, peso)); };
    for (const t of palavras(item.titulo)) add(t, 1.5);
    for (const p of item.perguntas) for (const t of palavras(p)) add(t, 1);
    for (const t of item.palavras || []) for (const u of palavras(t)) add(u, 2);
    return { item, termos, perguntas: item.perguntas.map(normalizar) };
  });

  function buscar(texto) {
    const q = palavras(texto);
    const qn = normalizar(texto);
    if (!q.length) return [];
    return indice
      .map(({ item, termos, perguntas }) => {
        let s = 0;
        for (const t of q) {
          if (termos.has(t)) { s += termos.get(t); continue; }
          let melhor = 0;
          for (const [termo, peso] of termos) {
            if (t.length >= 5 && termo.length >= 5 && t.slice(0, 5) === termo.slice(0, 5)) melhor = Math.max(melhor, peso * 0.7);
            else if (t.length >= 5 && distancia(t, termo) <= 1) melhor = Math.max(melhor, peso * 0.6);
          }
          s += melhor;
        }
        if (perguntas.includes(qn)) s += 6;
        return { item, score: s / Math.sqrt(q.length) };
      })
      .filter((r) => r.score > 0)
      .sort((a, b) => b.score - a.score);
  }

  function rConhecimento(item) {
    const tipo = item.id === "xg" ? "sem_dados" : "conhecimento";
    const relacionados = (item.relacionados || [])
      .map((id) => conhecimento.find((c) => c.id === id))
      .filter(Boolean)
      .map((c) => c.perguntas[0]);
    return resposta(tipo, item.titulo, item.resposta, { fonte: item.fonte, relacionados, pagina: item.pagina, categoria: item.categoria });
  }

  // ---------- roteamento ----------
  // Casa radicais e expressões no início de palavra (evita "acao" dentro de "classificacao").
  const tem = (n, ...radicais) => radicais.some((r) => ` ${n} `.includes(` ${r}`));

  function noDominio(n, toks, ents) {
    if (ents.equipes.length || ents.ambiguos.length || ents.anos.length) return true;
    return toks.some((t) => DOMINIO.some((d) => t.startsWith(d)));
  }

  function responder(pergunta, filtros = {}) {
    const n = normalizar(pergunta);
    const toks = n.split(" ").filter(Boolean);
    if (n.length < 3) return resposta("esclarecimento", "Pergunta muito curta", "Escreva uma pergunta com pelo menos uma palavra sobre o campeonato, os dados ou os modelos.");
    const det = detectarEquipes(pergunta);
    const ents = { ...det, anos: detectarAnos(pergunta) };
    const kb = buscar(pergunta);
    const dominio = noDominio(n, toks, ents) || Boolean(filtros.equipe || filtros.ano) || (kb.length > 0 && kb[0].score >= 1.5);
    if (!dominio || (tem(n, ...FORA) && !ents.equipes.length && !toks.some((t) => ["campeonato", "brasileirao", "modelo", "dashboard", "projeto"].includes(t)))) {
      return resposta("fora_tema", "Assunto fora do tema", FORA_DO_TEMA, { relacionados: sugestoes(3) });
    }
    if (ents.anos.length > 1 && !tem(n, "entre", " a ")) {
      return resposta("esclarecimento", "Mais de uma temporada", `A pergunta cita ${ents.anos.join(" e ")}. Escolha uma temporada por pergunta.`);
    }
    const ano = ents.anos[0] || (filtros.ano ? Number(filtros.ano) : null);
    const invalido = validarAno(ano);
    if (invalido) return invalido;
    let times = ents.equipes;
    if (!times.length && filtros.equipe && !ents.ambiguos.length) times = [filtros.equipe];
    const conceito = CONCEITO.some((c) => n.includes(c));

    if (conceito && kb.length && kb[0].score >= 1.6) return rConhecimento(kb[0].item);

    const anoOuUltimo = ano || ultimoAno;
    const pedeEquipe = (fn) => {
      if (ents.ambiguos.length && !times.length) {
        return resposta("esclarecimento", "Qual equipe?", `Encontrei mais de uma equipe com esse nome: ${ents.ambiguos[0].join(", ")}. Escreva o nome completo.`);
      }
      return fn();
    };

    // métricas que não existem nos dados
    if (tem(n, "xg", "expected goals", "gols esperados", "finaliza", "chutes", "posse de bola", "escanteio", "cartao", "cartoes", "torcida", "torcedor", "publico", "salario", "valor de mercado", "elenco", "tecnico")) {
      const xg = conhecimento.find((c) => c.id === "xg");
      return resposta("sem_dados", "Informação indisponível", xg ? xg.resposta : SEM_INFORMACAO, { fonte: xg?.fonte, relacionados: sugestoes(3) });
    }
    // destaques individuais
    if (tem(n, "artilh", "goleador")) return rDestaque("artilheiro", anoOuUltimo);
    if (tem(n, "craque", "melhor jogador", "bola de ouro")) return rDestaque("craque", anoOuUltimo);
    if (tem(n, "melhor goleiro", "goleiro")) return rDestaque("goleiro", anoOuUltimo);
    // previsões
    if (tem(n, "previs", "preve", "vai fazer", "proximos jogos") && !conceito) {
      return pedeEquipe(() => (times.length ? rPrevisao(times[0]) : (kb.length ? rConhecimento(kb[0].item) : rConhecimento(conhecimento.find((c) => c.id === "como-preve")))));
    }
    // classificação
    if (tem(n, "classific", "tabela", "campea", "campeoes", "lider", "venceu o campeonato", "ganhou o campeonato", "rebaix", "g4", "z4") && !conceito) {
      return rClassificacao(anoOuUltimo, { topo: tem(n, "campea", "campeoes", "lider", "ganhou", "venceu") ? 5 : 20, rebaixados: tem(n, "rebaix", "z4") });
    }
    // dois times
    if (times.length >= 2) {
      if (tem(n, "confront", "contra", "x ", "versus", "historico entre", "jogos entre", "duelo", "classico")) return rConfronto(times[0], times[1], ano);
      return rComparar(times[0], times[1], ano);
    }
    // rankings
    const ranking = [
      [["pior ataque"], "pior_ataque"], [["pior defesa", "mais vazad", "mais gols sofrid", "sofreu mais"], "pior_defesa"],
      [["melhor ataque", "mais gols marcad", "marcou mais", "mais gols"], "ataque"], [["melhor defesa", "menos vazad", "menos gols sofrid", "sofreu menos"], "defesa"],
      [["saldo"], "saldo"], [["mais vitorias", "venceu mais"], "vitorias"], [["mais empates", "empatou mais"], "empates"],
      [["mais derrotas", "perdeu mais"], "derrotas"], [["melhor mandante", "melhor em casa"], "mandante"], [["melhor visitante", "melhor fora"], "visitante"],
    ];
    if (!times.length && !conceito) {
      for (const [chaves, metrica] of ranking) if (tem(n, ...chaves)) return rRanking(metrica, anoOuUltimo);
    }
    // mando
    if (tem(n, "mandante", "visitante", "em casa", "fora de casa", "mando") && !conceito) return pedeEquipe(() => rMando(times[0], ano));
    // sequências
    if (tem(n, "sequenc", "invict", "seguidas", "seguidos", "serie de")) {
      const tipo = tem(n, "derrota", "perdeu", "perder") && !tem(n, "sem perder", "invict") ? "derrotas" : tem(n, "sem vencer", "sem ganhar") ? "sem_vencer" : tem(n, "vitoria", "venceu", "ganhou") ? "vitorias" : "invicta";
      return pedeEquipe(() => rSequencia(tipo, times[0], ano));
    }
    // gols
    if (tem(n, "goleada", "maior placar", "maiores placares")) return rGols(ano, true);
    if (tem(n, "gols por jogo", "gols por partida", "media de gols", "quantos gols") && !times.length) return rGols(ano, false);
    // equipe sozinha
    const pedeResumo = tem(n, "desempenho", "campanha", "como foi", "como esta", "resumo", "temporada", "pontos", "posicao", "terminou", "historico", "estatistic", "numeros", "aproveitamento", "vitorias", "jogos")
      || palavras(pergunta).filter((t) => !/^\d{4}$/.test(t)).length <= 2;
    if (times.length === 1 && !conceito && pedeResumo && (kb.length === 0 || kb[0].score < 2.5)) return rResumo(times[0], ano);
    if (ents.ambiguos.length && !times.length && !conceito) return pedeEquipe(() => null);
    // base de conhecimento
    if (kb.length && kb[0].score >= 1.2) return rConhecimento(kb[0].item);
    return resposta("sem_dados", "Sem informação suficiente", SEM_INFORMACAO, {
      relacionados: kb.slice(0, 3).map((r) => r.item.perguntas[0]).concat(kb.length ? [] : sugestoes(3)),
    });
  }

  function sugestoes(n = 8) {
    return conhecimento.filter((c) => c.sugerir).map((c) => c.perguntas[0]).slice(0, n);
  }

  return { responder, buscar, detectarEquipes, detectarAnos, linhas, sugestoes, anos, equipes };
}
