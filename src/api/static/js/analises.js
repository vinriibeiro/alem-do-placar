// Análises da Central de Consulta calculadas a partir das partidas (e das previsões do modelo).
// Cada função devolve um objeto de resposta pronto para a interface; nada é estimado.

import {
  FONTE_PARTIDAS, dataBR, fmt, lista, ordinal, pct, plural, pontosDe, resposta, resultado, sinal, tabelaLinhas,
} from "./util.js";

export function criarAnalises({ jogos, anos, equipes, escudos, modelo, destaques, linhas, sequencia }) {
  const ultimoAno = anos[anos.length - 1];
  const refAno = (ano) => (ano ? `em ${ano}` : `de ${anos[0]} a ${ultimoAno}`);
  const noAno = (equipe, ano) => jogos.some((j) => j.ano === ano && (j.mandante === equipe || j.visitante === equipe));
  const anosDe = (equipe) => anos.filter((a) => noAno(equipe, a));
  const placar = (j) => `${j.mandante} ${j.gm} × ${j.gv} ${j.visitante}`;
  const semDados = (titulo, texto, extra = {}) => resposta("sem_dados", titulo, texto, { fonte: FONTE_PARTIDAS, ...extra });

  const jogosDe = (equipe, ano) =>
    jogos
      .filter((j) => (!ano || j.ano === ano) && (j.mandante === equipe || j.visitante === equipe))
      .map((j) => {
        const casa = j.mandante === equipe;
        const gp = casa ? j.gm : j.gv;
        const gc = casa ? j.gv : j.gm;
        return { ...j, casa, adversario: casa ? j.visitante : j.mandante, gp, gc, saldo: gp - gc, res: resultado(gp, gc) };
      });

  const tabelaJogos = (lst) =>
    tabelaLinhas(
      ["Temporada", "Data", "Rod.", "Mandante", "Placar", "Visitante"],
      lst.map((j) => [j.ano, dataBR(j.data), j.rodada ?? "—", j.mandante, `${j.gm} × ${j.gv}`, j.visitante]),
    );

  const relacionadosEquipe = (equipe, ano) => [
    `Melhor jogo do ${equipe}${ano ? ` em ${ano}` : ""}`,
    `Últimos 5 jogos do ${equipe}`,
    `Maior sequência invicta do ${equipe}`,
    `Em que ano o ${equipe} foi melhor?`,
    `${equipe} como mandante e visitante`,
  ];

  // ---------- jogos de uma equipe ----------
  function jogoDestaque(equipe, ano, tipo) {
    const todos = jogosDe(equipe, ano);
    if (!todos.length) return semDados(equipe, `${equipe} não disputou a Série A ${refAno(ano)} nos dados disponíveis.`);
    const ordens = {
      melhor: (a, b) => b.saldo - a.saldo || b.gp - a.gp || b.data.localeCompare(a.data),
      pior: (a, b) => a.saldo - b.saldo || b.gc - a.gc || b.data.localeCompare(a.data),
      gols: (a, b) => b.gp + b.gc - (a.gp + a.gc) || b.data.localeCompare(a.data),
      ultimo: (a, b) => b.data.localeCompare(a.data),
      primeiro: (a, b) => a.data.localeCompare(b.data),
    };
    const ord = todos.slice().sort(ordens[tipo]);
    const j = ord[0];
    const quando = `em ${dataBR(j.data)}${j.rodada ? ` (rodada ${j.rodada}${ano ? "" : ` de ${j.ano}`})` : ""}`;
    const local = j.casa ? "em casa" : "fora de casa";
    const verbo = j.res === "V" ? "venceu" : j.res === "E" ? "empatou com" : "perdeu para";
    const descricoes = {
      melhor: ["Melhor jogo", "maior vitória por saldo de gols"],
      pior: ["Pior jogo", "maior derrota por saldo de gols"],
      gols: ["Jogo com mais gols", "maior número de gols somados"],
      ultimo: ["Último jogo", "partida mais recente nos dados"],
      primeiro: ["Primeiro jogo", "partida mais antiga nos dados"],
    };
    const [rotulo, criterio] = descricoes[tipo];
    return resposta("estatistica", `${rotulo} do ${equipe} ${refAno(ano)}`,
      `${rotulo} do ${equipe} ${refAno(ano)}: ${verbo} o ${j.adversario} por ${j.gp} × ${j.gc}, ${local}, ${quando}.`,
      {
        kpis: [["Placar", `${j.gm} × ${j.gv}`], ["Adversário", j.adversario], ["Local", j.casa ? "Em casa" : "Fora"], ["Data", dataBR(j.data)]],
        tabela: tabelaJogos(ord.slice(0, 5)),
        nota: `Critério: ${criterio}. "Melhor" e "pior" não medem a importância do jogo, só o placar.`,
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null,
        relacionados: relacionadosEquipe(equipe, ano).filter((p) => !p.startsWith(rotulo)).slice(0, 4),
      });
  }

  function formaRecente(equipe, n, ano) {
    const todos = jogosDe(equipe, ano).sort((a, b) => b.data.localeCompare(a.data));
    if (!todos.length) return semDados(equipe, `${equipe} não disputou a Série A ${refAno(ano)} nos dados disponíveis.`);
    const ult = todos.slice(0, n);
    const pts = ult.reduce((s, j) => s + pontosDe(j.gp, j.gc), 0);
    const seq = ult.map((j) => j.res).join(" ");
    const v = ult.filter((j) => j.res === "V").length;
    const e = ult.filter((j) => j.res === "E").length;
    const d = ult.filter((j) => j.res === "D").length;
    return resposta("estatistica", `Últimos ${ult.length} jogos do ${equipe}`,
      `Nos últimos ${ult.length} jogos${ano ? ` de ${ano}` : " dos dados"}, ${equipe} somou ${pts} de ${3 * ult.length} pontos (${seq}, do mais recente ao mais antigo): ${v} vitórias, ${e} empates e ${d} derrotas.`,
      {
        kpis: [["Pontos", `${pts} de ${3 * ult.length}`], ["Aproveitamento", pct(pts / (3 * ult.length))], ["V · E · D", `${v} · ${e} · ${d}`], ["Gols", `${ult.reduce((s, j) => s + j.gp, 0)} × ${ult.reduce((s, j) => s + j.gc, 0)}`]],
        tabela: tabelaLinhas(["Data", "Adversário", "Local", "Placar", "Resultado"], ult.map((j) => [dataBR(j.data), j.adversario, j.casa ? "Casa" : "Fora", `${j.gp} × ${j.gc}`, j.res === "V" ? "Vitória" : j.res === "E" ? "Empate" : "Derrota"]), 1),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null,
        relacionados: relacionadosEquipe(equipe, ano).filter((p) => !p.startsWith("Últimos")).slice(0, 4),
      });
  }

  // ---------- resumo (campanha de um ano ou história) ----------
  /** Frase que responde direto ao número que a pergunta pediu (vitórias, gols, pontos...). */
  function direta(foco, d, equipe, ref, comPosicao) {
    const f = ` ${foco} `;
    if (/ vitori/.test(f)) return `${equipe} teve ${plural(d.V, "vitória", "vitórias")} ${ref}.`;
    if (/ empat/.test(f)) return `${equipe} teve ${plural(d.E, "empate", "empates")} ${ref}.`;
    if (/ derrot/.test(f)) return `${equipe} teve ${plural(d.D, "derrota", "derrotas")} ${ref}.`;
    if (/ (sofrid|sofreu|levou)/.test(f)) return `${equipe} sofreu ${plural(d.GC, "gol", "gols")} ${ref}.`;
    if (/ (gols|marcou|fez gols)/.test(f)) return `${equipe} marcou ${plural(d.GP, "gol", "gols")} ${ref}.`;
    if (/ pontos/.test(f)) return `${equipe} fez ${plural(d.P, "ponto", "pontos")} ${ref}.`;
    if (/ (jogos|partidas)/.test(f)) return `${equipe} disputou ${plural(d.J, "jogo", "jogos")} ${ref}.`;
    if (comPosicao && / (posicao|colocacao|terminou|ficou)/.test(f)) return `${equipe} terminou ${ref} em ${ordinal(d.pos)} lugar.`;
    return "";
  }

  function resumoEquipe(equipe, ano, foco = "") {
    if (ano) {
      if (!noAno(equipe, ano)) return semDados(equipe, `${equipe} não disputou a Série A em ${ano} nos dados disponíveis.`);
      const t = linhas(ano);
      const r = t.find((x) => x.equipe === equipe);
      const meus = jogosDe(equipe, ano);
      const melhor = meus.slice().sort((a, b) => b.saldo - a.saldo || b.gp - a.gp)[0];
      const pior = meus.slice().sort((a, b) => a.saldo - b.saldo || b.gc - a.gc)[0];
      const inv = sequencia(equipe, ano, (p) => p >= 1);
      const marcante = [...meus.slice().sort((a, b) => b.saldo - a.saldo || b.gp - a.gp).slice(0, 3).map((j) => ["Maior vitória", j]),
        ...meus.slice().sort((a, b) => a.saldo - b.saldo || b.gc - a.gc).slice(0, 3).map((j) => ["Maior derrota", j])];
      const zona = r.pos <= 4 ? " (zona de Libertadores)" : r.pos >= 17 ? " (zona de rebaixamento)" : "";
      const leadAno = direta(foco, r, equipe, `em ${ano}`, true);
      return resposta("estatistica", `${equipe} em ${ano}`,
        `${leadAno ? `${leadAno} ` : ""}${equipe} terminou ${ano} em ${ordinal(r.pos)} lugar${zona}, com ${r.P} pontos, ${r.V} vitórias, ${r.E} empates e ${r.D} derrotas (${pct(r.aprov)} de aproveitamento). Marcou ${r.GP} gols (${fmt(r.GP / r.J, 2)} por jogo) e sofreu ${r.GC} (${fmt(r.GC / r.J, 2)}), saldo ${sinal(r.SG)}. ` +
          `Melhor jogo: ${melhor.res === "V" ? "venceu" : "marcou"} ${melhor.adversario} por ${melhor.gp} × ${melhor.gc}; pior: ${pior.res === "D" ? "perdeu para" : "enfrentou"} ${pior.adversario} por ${pior.gp} × ${pior.gc}. Maior sequência sem perder: ${inv.melhor} jogos.`,
        {
          kpis: [["Posição", ordinal(r.pos)], ["Pontos", r.P], ["Aproveitamento", pct(r.aprov)], ["V · E · D", `${r.V} · ${r.E} · ${r.D}`], ["Gols pró × contra", `${r.GP} × ${r.GC}`], ["Em casa", `${fmt(r.casaP / r.casaJ, 2)} pts/jogo`], ["Fora", `${fmt(r.foraP / r.foraJ, 2)} pts/jogo`], ["Sem perder", `${inv.melhor} jogos`]],
          tabela: tabelaLinhas(["Tipo", "Data", "Rod.", "Adversário", "Local", "Placar"], marcante.map(([tp, j]) => [tp, dataBR(j.data), j.rodada ?? "—", j.adversario, j.casa ? "Casa" : "Fora", `${j.gp} × ${j.gc}`]), 3),
          fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null,
          relacionados: relacionadosEquipe(equipe, ano).slice(0, 4),
        });
    }
    const porAno = anosDe(equipe).map((a) => ({ ano: a, ...linhas(a).find((x) => x.equipe === equipe) }));
    const tot = porAno.reduce((s, r) => ({ J: s.J + r.J, P: s.P + r.P, V: s.V + r.V, E: s.E + r.E, D: s.D + r.D, GP: s.GP + r.GP, GC: s.GC + r.GC }), { J: 0, P: 0, V: 0, E: 0, D: 0, GP: 0, GC: 0 });
    const melhor = porAno.slice().sort((a, b) => a.pos - b.pos || b.P - a.P)[0];
    const titulos = porAno.filter((r) => r.pos === 1).map((r) => r.ano);
    const rebaixamentos = porAno.filter((r) => r.pos >= 17).length;
    const leadHist = direta(foco, tot, equipe, `de ${anos[0]} a ${ultimoAno}`, false);
    return resposta("estatistica", `${equipe} de ${anos[0]} a ${ultimoAno}`,
      `${leadHist ? `${leadHist} ` : ""}${equipe} disputou ${porAno.length} das ${anos.length} temporadas: ${tot.J} jogos, ${tot.V} vitórias, ${tot.E} empates e ${tot.D} derrotas, ${tot.P} pontos (${pct(tot.P / (3 * tot.J))} de aproveitamento) e saldo ${sinal(tot.GP - tot.GC)}. ` +
        `Melhor campanha: ${ordinal(melhor.pos)} lugar em ${melhor.ano}. ${titulos.length ? `Campeão em ${lista(titulos)}.` : "Não foi campeão no período."}${rebaixamentos ? ` Terminou na zona de rebaixamento ${plural(rebaixamentos, "vez", "vezes")}.` : ""}`,
      {
        kpis: [["Temporadas", `${porAno.length} de ${anos.length}`], ["Títulos", titulos.length], ["Melhor posição", `${ordinal(melhor.pos)} (${melhor.ano})`], ["Aproveitamento", pct(tot.P / (3 * tot.J))], ["V · E · D", `${tot.V} · ${tot.E} · ${tot.D}`], ["Gols pró × contra", `${tot.GP} × ${tot.GC}`]],
        tabela: tabelaLinhas(["Temporada", "Pos.", "P", "V", "E", "D", "SG", "Aprov."], porAno.map((r) => [r.ano, r.pos, r.P, r.V, r.E, r.D, r.SG, pct(r.aprov)])),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null,
        relacionados: relacionadosEquipe(equipe, null).slice(0, 4),
      });
  }

  function melhorAno(equipe, pior = false) {
    const anosEq = anosDe(equipe);
    if (!anosEq.length) return semDados(equipe, `${equipe} não disputou a Série A nos dados disponíveis.`);
    const porAno = anosEq.map((a) => ({ ano: a, ...linhas(a).find((x) => x.equipe === equipe) }));
    const ord = porAno.slice().sort((a, b) => (pior ? b.pos - a.pos || a.P - b.P : a.pos - b.pos || b.P - a.P));
    const t = ord[0];
    return resposta("estatistica", `${pior ? "Pior" : "Melhor"} temporada do ${equipe}`,
      `${pior ? "A pior" : "A melhor"} temporada do ${equipe} nos dados foi ${t.ano}: ${ordinal(t.pos)} lugar, com ${t.P} pontos, ${t.V} vitórias e saldo ${sinal(t.SG)}. Critério: posição final e, em caso de empate de posição, pontos.`,
      {
        kpis: [["Temporada", t.ano], ["Posição", ordinal(t.pos)], ["Pontos", t.P], ["Aproveitamento", pct(t.aprov)]],
        tabela: tabelaLinhas(["Temporada", "Pos.", "P", "V", "E", "D", "SG", "Aprov."], porAno.map((r) => [r.ano, r.pos, r.P, r.V, r.E, r.D, r.SG, pct(r.aprov)])),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null,
        relacionados: relacionadosEquipe(equipe, t.ano).slice(0, 3),
      });
  }

  // ---------- campeões e títulos ----------
  function campeoes(ano, vice = false) {
    const linhasAno = anos.map((a) => {
      const t = linhas(a);
      return { ano: a, c: t[0], v: t[1], t: t[2] };
    });
    const contagem = new Map();
    for (const l of linhasAno) contagem.set(l.c.equipe, (contagem.get(l.c.equipe) || 0) + 1);
    const maior = Math.max(...contagem.values());
    const multi = [...contagem].filter(([, n]) => n === maior).map(([e]) => e);
    if (ano) {
      const l = linhasAno.find((x) => x.ano === ano);
      const abertura = vice ? `O vice-campeão de ${ano} foi ${l.v.equipe}, com ${l.v.P} pontos, ${l.c.P - l.v.P} atrás do campeão ${l.c.equipe} (${l.c.P}). ` : "";
      return resposta("estatistica", vice ? `Campeão e vice de ${ano}` : `Campeão de ${ano}`,
        `${abertura}${l.c.equipe} foi campeão de ${ano} com ${l.c.P} pontos (${pct(l.c.aprov)}), ${l.c.P - l.v.P} à frente do vice ${l.v.equipe} (${l.v.P}). Em terceiro ficou ${l.t.equipe} (${l.t.P}).`,
        {
          kpis: [["Campeão", l.c.equipe], ["Pontos", l.c.P], ["Vice", l.v.equipe], ["Vantagem", `${l.c.P - l.v.P} pts`]],
          tabela: tabelaLinhas(["Pos.", "Equipe", "P", "V", "SG"], [l.c, l.v, l.t].map((r) => [r.pos, r.equipe, r.P, r.V, r.SG]), 1),
          fonte: `${FONTE_PARTIDAS}. Desempate: pontos, vitórias, saldo e gols marcados.`, pagina: "dashboard.html", escudo: escudos[l.c.equipe] || null,
          relacionados: [`Classificação de ${ano}`, `Artilheiro de ${ano}`, `Melhor ataque de ${ano}`, `Quem foi rebaixado em ${ano}?`],
        });
    }
    return resposta("estatistica", `Campeões de ${anos[0]} a ${ultimoAno}`,
      `${lista(multi)} ${multi.length > 1 ? "foram os maiores campeões" : "foi o maior campeão"} do período, com ${plural(maior, "título", "títulos")}. O campeão mais recente é ${linhasAno[linhasAno.length - 1].c.equipe} (${ultimoAno}).`,
      {
        kpis: [["Mais títulos", lista(multi)], ["Títulos", maior], ["Campeões diferentes", contagem.size], ["Temporadas", anos.length]],
        tabela: tabelaLinhas(["Temporada", "Campeão", "P", "Vice", "P", "Diferença"], linhasAno.map((l) => [l.ano, l.c.equipe, l.c.P, l.v.equipe, l.v.P, `${l.c.P - l.v.P} pts`]), 1),
        fonte: `${FONTE_PARTIDAS}. Campeão = 1º colocado pela classificação calculada.`, pagina: "dashboard.html",
        relacionados: ["Quem foi o campeão de 2025?", "Quais clubes foram rebaixados em 2025?", "Quem mais evoluiu em 2025?"],
      });
  }

  function titulosEquipe(equipe) {
    const anosEq = anosDe(equipe);
    if (!anosEq.length) return semDados(equipe, `${equipe} não disputou a Série A nos dados disponíveis.`);
    const porAno = anosEq.map((a) => ({ ano: a, ...linhas(a).find((x) => x.equipe === equipe) }));
    const titulos = porAno.filter((r) => r.pos === 1);
    const vice = porAno.filter((r) => r.pos === 2);
    const g4 = porAno.filter((r) => r.pos <= 4);
    const z4 = porAno.filter((r) => r.pos >= 17);
    return resposta("estatistica", `Títulos e posições do ${equipe}`,
      `${titulos.length ? `${equipe} foi campeão ${plural(titulos.length, "vez", "vezes")} entre ${anos[0]} e ${ultimoAno} (${titulos.map((r) => r.ano).join(", ")})` : `${equipe} não foi campeão entre ${anos[0]} e ${ultimoAno}`}. ` +
        `Foi vice ${plural(vice.length, "vez", "vezes")}, terminou entre os 4 primeiros ${plural(g4.length, "vez", "vezes")} e na zona de rebaixamento ${plural(z4.length, "vez", "vezes")}, em ${plural(porAno.length, "temporada disputada", "temporadas disputadas")}.`,
      {
        kpis: [["Títulos", titulos.length], ["Vice", vice.length], ["Top 4", g4.length], ["Rebaixamento", z4.length]],
        tabela: tabelaLinhas(["Temporada", "Pos.", "P", "Zona"], porAno.map((r) => [r.ano, r.pos, r.P, r.pos === 1 ? "Campeão" : r.pos <= 4 ? "Libertadores" : r.pos <= 6 ? "Pré-Libertadores" : r.pos <= 12 ? "Sul-Americana" : r.pos >= 17 ? "Rebaixamento" : "—"])),
        nota: "O período dos dados é 2018–2025; títulos anteriores não são contados.",
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null,
        relacionados: relacionadosEquipe(equipe, null).slice(0, 3),
      });
  }

  function entradasSaidas(ano, modo) {
    if (ano === anos[0]) {
      return semDados(`Temporada ${ano}`, `${modo === "subiram" ? "Não dá para saber quem subiu" : "Não dá para saber quem caiu"} em ${ano}: os dados começam nessa temporada e não há ano anterior para comparar.`);
    }
    const atual = new Set(equipes.filter((e) => noAno(e, ano)));
    const anterior = new Set(equipes.filter((e) => noAno(e, ano - 1)));
    const lst = modo === "subiram" ? [...atual].filter((e) => !anterior.has(e)) : [...anterior].filter((e) => !atual.has(e));
    const posAnterior = new Map(linhas(ano - 1).map((r) => [r.equipe, r.pos]));
    const posAtual = new Map(linhas(ano).map((r) => [r.equipe, r.pos]));
    const titulo = modo === "subiram" ? `Clubes que entraram na Série A em ${ano}` : `Clubes que deixaram a Série A depois de ${ano - 1}`;
    return resposta("estatistica", titulo,
      modo === "subiram"
        ? `${lista(lst.sort())} não disputaram a Série A de ${ano - 1} e entraram em ${ano} (acesso da Série B).`
        : `${lista(lst.sort())} disputaram a Série A de ${ano - 1} e não estão em ${ano} (rebaixados).`,
      {
        tabela: modo === "subiram"
          ? tabelaLinhas(["Equipe", `Posição em ${ano}`], lst.sort().map((e) => [e, ordinal(posAtual.get(e))]), 0)
          : tabelaLinhas(["Equipe", `Posição em ${ano - 1}`], lst.sort().map((e) => [e, ordinal(posAnterior.get(e))]), 0),
        fonte: `${FONTE_PARTIDAS}. Comparação entre as equipes de ${ano - 1} e ${ano}.`, pagina: "dashboard.html",
        relacionados: [`Classificação de ${ano}`, `Quem foi o campeão de ${ano}?`],
      });
  }

  function variacaoAnos(ano, tipo, equipe) {
    if (ano === anos[0]) return semDados(`Temporada ${ano}`, `Não há temporada anterior a ${ano} nos dados para calcular a evolução.`);
    const ant = new Map(linhas(ano - 1).map((r) => [r.equipe, r]));
    const lst = linhas(ano).filter((r) => ant.has(r.equipe)).map((r) => ({ equipe: r.equipe, antes: ant.get(r.equipe), agora: r, dif: r.P - ant.get(r.equipe).P }));
    if (equipe) {
      const x = lst.find((l) => l.equipe === equipe);
      if (!x) return semDados(equipe, `${equipe} não disputou a Série A em ${ano - 1} e em ${ano}, então não há comparação.`);
      return resposta("estatistica", `${equipe}: ${ano - 1} → ${ano}`,
        `${equipe} ${x.dif >= 0 ? "somou" : "perdeu"} ${Math.abs(x.dif)} pontos ${x.dif >= 0 ? "a mais" : "a menos"} em ${ano} (${x.agora.P}) do que em ${ano - 1} (${x.antes.P}) e foi do ${ordinal(x.antes.pos)} para o ${ordinal(x.agora.pos)} lugar.`,
        {
          kpis: [[`Pontos ${ano - 1}`, x.antes.P], [`Pontos ${ano}`, x.agora.P], ["Variação", `${sinal(x.dif)} pts`], ["Posição", `${ordinal(x.antes.pos)} → ${ordinal(x.agora.pos)}`]],
          fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[equipe] || null, relacionados: relacionadosEquipe(equipe, ano).slice(0, 3),
        });
    }
    lst.sort((a, b) => (tipo === "caiu" ? a.dif - b.dif : b.dif - a.dif));
    const topo = lst[0];
    return resposta("estatistica", `${tipo === "caiu" ? "Maior queda" : "Maior evolução"} de ${ano - 1} para ${ano}`,
      `${topo.equipe} ${tipo === "caiu" ? "teve a maior queda" : "teve a maior evolução"} entre ${ano - 1} e ${ano}: ${sinal(topo.dif)} pontos (de ${topo.antes.P} para ${topo.agora.P}) e do ${ordinal(topo.antes.pos)} para o ${ordinal(topo.agora.pos)} lugar. Foram comparadas as ${lst.length} equipes que disputaram os dois anos.`,
      {
        tabela: tabelaLinhas(["Equipe", `P ${ano - 1}`, `P ${ano}`, "Variação", "Posição"], lst.slice(0, 6).map((x) => [x.equipe, x.antes.P, x.agora.P, `${sinal(x.dif)} pts`, `${ordinal(x.antes.pos)} → ${ordinal(x.agora.pos)}`]), 0),
        nota: "Compara pontos finais da temporada anterior com os da temporada escolhida.",
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[topo.equipe] || null,
        relacionados: [tipo === "caiu" ? `Quem mais evoluiu em ${ano}?` : `Quem mais caiu em ${ano}?`, `Classificação de ${ano}`],
      });
  }

  // ---------- rodadas ----------
  const temRodadas = jogos.some((j) => j.rodada != null);

  function rodadaValida(rodada, ano) {
    if (!temRodadas) return semDados("Rodadas", "Os dados carregados não trazem o número da rodada.");
    const max = Math.max(...jogos.filter((j) => j.ano === ano && j.rodada != null).map((j) => j.rodada));
    if (!(rodada >= 1 && rodada <= max)) return semDados(`Rodada ${rodada}`, `A rodada ${rodada} não existe em ${ano}: a temporada tem rodadas de 1 a ${max}.`);
    return null;
  }

  function classificacaoApos(rodada, ano, topo = 10) {
    const erro = rodadaValida(rodada, ano);
    if (erro) return erro;
    const t = linhas(ano, rodada);
    const l = t[0];
    return resposta("estatistica", `Classificação de ${ano} após a rodada ${rodada}`,
      `Depois da rodada ${rodada} de ${ano}, ${l.equipe} liderava com ${l.P} pontos em ${l.J} jogos${t[1] ? `, ${l.P - t[1].P} à frente do segundo colocado, ${t[1].equipe}` : ""}. O último colocado era ${t[t.length - 1].equipe}.`,
      {
        kpis: [["Líder", l.equipe], ["Pontos", l.P], ["Jogos", l.J], ["Rodada", rodada]],
        tabela: tabelaLinhas(["Pos.", "Equipe", "P", "J", "V", "E", "D", "SG"], t.slice(0, topo).map((r) => [r.pos, r.equipe, r.P, r.J, r.V, r.E, r.D, r.SG]), 1),
        nota: "Jogos adiados podem fazer o número de jogos variar entre equipes. A rodada segue o calendário original dos dados.",
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: escudos[l.equipe] || null,
        relacionados: [`Classificação de ${ano}`, `Jogos da rodada ${rodada} de ${ano}`],
      });
  }

  function jogosDaRodada(rodada, ano) {
    const erro = rodadaValida(rodada, ano);
    if (erro) return erro;
    const lst = jogos.filter((j) => j.ano === ano && j.rodada === rodada).sort((a, b) => a.data.localeCompare(b.data));
    const gols = lst.reduce((s, j) => s + j.gm + j.gv, 0);
    const mand = lst.filter((j) => j.gm > j.gv).length;
    const emp = lst.filter((j) => j.gm === j.gv).length;
    return resposta("estatistica", `Rodada ${rodada} de ${ano}`,
      `A rodada ${rodada} de ${ano} teve ${lst.length} jogos e ${gols} gols (${fmt(gols / lst.length, 2)} por jogo): ${mand} vitórias de mandantes, ${emp} empates e ${lst.length - mand - emp} de visitantes.`,
      { tabela: tabelaJogos(lst), fonte: FONTE_PARTIDAS, pagina: "dashboard.html", relacionados: [`Classificação de ${ano} após a rodada ${rodada}`] });
  }

  // ---------- mando de campo ----------
  function mando(equipe, ano) {
    const base = equipe
      ? jogosDe(equipe, ano)
      : jogos.filter((j) => !ano || j.ano === ano).flatMap((j) => [
        { casa: true, gp: j.gm, gc: j.gv, res: resultado(j.gm, j.gv) },
        { casa: false, gp: j.gv, gc: j.gm, res: resultado(j.gv, j.gm) },
      ]);
    if (!base.length) return semDados("Mando de campo", `${equipe} não disputou a Série A ${refAno(ano)} nos dados disponíveis.`);
    const soma = (lst) => {
      const v = lst.filter((j) => j.res === "V").length;
      const e = lst.filter((j) => j.res === "E").length;
      const d = lst.length - v - e;
      const P = 3 * v + e;
      return { n: lst.length, v, e, d, P, ppj: P / lst.length, gp: lst.reduce((s, j) => s + j.gp, 0), gc: lst.reduce((s, j) => s + j.gc, 0), aprov: P / (3 * lst.length) };
    };
    const c = soma(base.filter((j) => j.casa));
    const f = soma(base.filter((j) => !j.casa));
    const sujeito = equipe ? `${equipe} ${refAno(ano)} fez` : `As equipes ${refAno(ano)} fizeram`;
    return resposta("estatistica", `Mando de campo${equipe ? `: ${equipe}` : ""}`,
      `${sujeito} ${fmt(c.ppj, 2)} pontos por jogo em casa (${pct(c.aprov)}) e ${fmt(f.ppj, 2)} fora (${pct(f.aprov)}). ` +
        `Em casa: ${c.v} vitórias, ${c.e} empates e ${c.d} derrotas, ${c.gp} gols marcados e ${c.gc} sofridos. Fora: ${f.v} vitórias, ${f.e} empates e ${f.d} derrotas, ${f.gp} gols marcados e ${f.gc} sofridos.`,
      {
        kpis: [["Em casa", `${fmt(c.ppj, 2)} pts/jogo`], ["Fora", `${fmt(f.ppj, 2)} pts/jogo`], ["Vitórias em casa", pct(c.v / c.n)], ["Vitórias fora", pct(f.v / f.n)]],
        tabela: tabelaLinhas(["Mando", "Jogos", "V", "E", "D", "GP", "GC", "Pts/jogo", "Aprov."], [["Em casa", c.n, c.v, c.e, c.d, c.gp, c.gc, fmt(c.ppj, 2), pct(c.aprov)], ["Fora", f.n, f.v, f.e, f.d, f.gp, f.gc, fmt(f.ppj, 2), pct(f.aprov)]]),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html", escudo: equipe ? escudos[equipe] || null : null,
        relacionados: equipe ? relacionadosEquipe(equipe, ano).filter((p) => !p.includes("mandante")).slice(0, 3) : ["Qual o melhor mandante de 2025?", "Qual o melhor visitante de 2025?"],
      });
  }

  // ---------- campeonato ----------
  function placarMaisComum(ano) {
    const lst = jogos.filter((j) => !ano || j.ano === ano);
    const cont = new Map();
    for (const j of lst) cont.set(`${j.gm} × ${j.gv}`, (cont.get(`${j.gm} × ${j.gv}`) || 0) + 1);
    const top = [...cont].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 8);
    const zero = cont.get("0 × 0") || 0;
    return resposta("estatistica", `Placares mais comuns ${refAno(ano)}`,
      `O placar mais comum ${refAno(ano)} foi ${top[0][0]} (mandante × visitante), em ${top[0][1]} de ${fmt(lst.length)} jogos (${pct(top[0][1] / lst.length)}). Houve ${plural(zero, "empate sem gols", "empates sem gols")}.`,
      {
        kpis: [["Mais comum", top[0][0]], ["Jogos", fmt(top[0][1])], ["0 × 0", zero], ["Partidas", fmt(lst.length)]],
        tabela: tabelaLinhas(["Placar (casa × fora)", "Jogos", "% das partidas"], top.map(([p, n]) => [p, n, pct(n / lst.length)])),
        fonte: FONTE_PARTIDAS,
      });
  }

  function maisGols(ano) {
    const lst = jogos.filter((j) => !ano || j.ano === ano).sort((a, b) => b.gm + b.gv - (a.gm + a.gv) || b.data.localeCompare(a.data));
    const t = lst[0];
    return resposta("estatistica", `Jogos com mais gols ${refAno(ano)}`,
      `O jogo com mais gols ${refAno(ano)} foi ${placar(t)}, com ${t.gm + t.gv} gols, em ${dataBR(t.data)}.`,
      { kpis: [["Gols no jogo", t.gm + t.gv], ["Placar", `${t.gm} × ${t.gv}`], ["Data", dataBR(t.data)]], tabela: tabelaJogos(lst.slice(0, 5)), fonte: FONTE_PARTIDAS });
  }

  function estatisticasCampeonato(ano) {
    const lst = jogos.filter((j) => !ano || j.ano === ano);
    const total = lst.reduce((s, j) => s + j.gm + j.gv, 0);
    const m = lst.filter((j) => j.gm > j.gv).length;
    const e = lst.filter((j) => j.gm === j.gv).length;
    const v = lst.length - m - e;
    const porAno = anos.filter((a) => !ano || a === ano).map((a) => {
      const l = jogos.filter((j) => j.ano === a);
      const g = l.reduce((s, j) => s + j.gm + j.gv, 0);
      return [a, l.length, g, fmt(g / l.length, 2), pct(l.filter((j) => j.gm > j.gv).length / l.length), pct(l.filter((j) => j.gm === j.gv).length / l.length), pct(l.filter((j) => j.gm < j.gv).length / l.length)];
    });
    return resposta("estatistica", `Gols por partida ${refAno(ano)}`,
      `Foram ${fmt(total)} gols em ${fmt(lst.length)} partidas ${refAno(ano)}: média de ${fmt(total / lst.length, 2)} gols por partida. Mandantes venceram ${pct(m / lst.length)} dos jogos, houve ${pct(e / lst.length)} de empates e ${pct(v / lst.length)} de vitórias de visitantes.`,
      {
        kpis: [["Partidas", fmt(lst.length)], ["Gols", fmt(total)], ["Gols por jogo", fmt(total / lst.length, 2)], ["Mandante vence", pct(m / lst.length)], ["Empates", pct(e / lst.length)], ["Visitante vence", pct(v / lst.length)]],
        tabela: tabelaLinhas(["Temporada", "Partidas", "Gols", "Gols/jogo", "Mandante", "Empate", "Visitante"], porAno),
        fonte: FONTE_PARTIDAS, pagina: "dashboard.html",
        relacionados: ["Quais foram as maiores goleadas?", "Qual o placar mais comum?", "Qual foi o jogo com mais gols?"],
      });
  }

  // ---------- destaques individuais e modelo ----------
  const NOMES_CAT = { artilheiro: "Artilheiros", craque: "Craques do Brasileirão", goleiro: "Melhores goleiros" };

  function listaDestaques(categoria) {
    const lst = destaques.filter((d) => d.categoria === categoria).sort((a, b) => a.ano - b.ano || a.jogador.localeCompare(b.jogador));
    const cont = new Map();
    for (const d of lst) cont.set(d.jogador, (cont.get(d.jogador) || 0) + 1);
    const max = Math.max(...cont.values());
    const repetidos = [...cont].filter(([, n]) => n === max && n > 1).map(([j]) => j);
    return resposta("estatistica", `${NOMES_CAT[categoria]} de cada temporada`,
      `Há ${lst.length} registros de ${NOMES_CAT[categoria].toLowerCase()} entre ${anos[0]} e ${ultimoAno} na fonte consultada.` +
        (repetidos.length ? ` ${lista(repetidos)} ${repetidos.length > 1 ? "aparecem" : "aparece"} mais vezes (${max}).` : "") +
        (categoria === "artilheiro" ? " Empates na artilharia listam todos os jogadores." : "") +
        ` Temporadas sem registro na fonte: ${anos.filter((a) => !lst.some((d) => d.ano === a)).join(", ") || "nenhuma"}.`,
      {
        tabela: tabelaLinhas(categoria === "artilheiro" ? ["Temporada", "Jogador", "Clube", "Gols"] : ["Temporada", "Jogador", "Clube"],
          lst.map((d) => (categoria === "artilheiro" ? [d.ano, d.jogador, d.clube, d.gols] : [d.ano, d.jogador, d.clube])), 2),
        fonte: "Wikipédia em português (páginas de cada temporada); prêmios oficiais da CBF", pagina: "dashboard.html",
      });
  }

  function errosDoModelo(ordem) {
    const porEquipe = new Map();
    for (const p of modelo.previsoes) {
      if (p[5] === null) continue;
      const a = porEquipe.get(p[0]) || { soma: 0, n: 0 };
      a.soma += Math.abs(p[2] - p[5]); a.n += 1;
      porEquipe.set(p[0], a);
    }
    const lst = [...porEquipe].map(([e, a]) => ({ e, mae: a.soma / a.n, n: a.n })).sort((x, y) => (ordem === "piores" ? y.mae - x.mae : x.mae - y.mae));
    return resposta("estatistica", `Equipes ${ordem === "piores" ? "mais difíceis" : "mais fáceis"} de prever (${modelo.ano_teste})`,
      `No teste de ${modelo.ano_teste}, a equipe com ${ordem === "piores" ? "maior" : "menor"} erro médio do modelo foi ${lst[0].e} (${fmt(lst[0].mae, 2)} ponto por jogo, em ${lst[0].n} previsões). ${ordem === "piores" ? "A mais fácil" : "A mais difícil"} foi ${lst[lst.length - 1].e} (${fmt(lst[lst.length - 1].mae, 2)}).`,
      {
        tabela: tabelaLinhas(["#", "Equipe", "Erro médio (MAE)", "Previsões"], lst.slice(0, 10).map((x, i) => [i + 1, x.e, fmt(x.mae, 3), x.n]), 1),
        nota: "Com cerca de 33 previsões por equipe, diferenças pequenas entre equipes não indicam qualidade do clube.",
        fonte: `Previsões do modelo ${modelo.modelo_nome} (${modelo.versao}), teste com ${modelo.ano_teste}`, pagina: "dashboard.html", escudo: escudos[lst[0].e] || null,
      });
  }

  function previsaoGeral() {
    const ultima = new Map();
    for (const p of modelo.previsoes) if (!ultima.has(p[0]) || p[1] > ultima.get(p[0])[1]) ultima.set(p[0], p);
    const lst = [...ultima.values()].sort((a, b) => b[2] - a[2]);
    return resposta("estatistica", `Última previsão do modelo para cada equipe (${modelo.ano_teste})`,
      `Na última data com previsão em ${modelo.ano_teste} (${dataBR(lst[0][1])}), o modelo esperava mais pontos de ${lst[0][0]} (${fmt(lst[0][2], 2)} por jogo) e menos de ${lst[lst.length - 1][0]} (${fmt(lst[lst.length - 1][2], 2)}). Veja também o resultado real dos 5 jogos seguintes. É uma estimativa retrospectiva, não uma certeza.`,
      {
        tabela: tabelaLinhas(["Equipe", "Data", "Previsto", "Faixa de 90%", "Real"], lst.map((p) => [p[0], dataBR(p[1]), fmt(p[2], 2), `${fmt(p[3], 2)} a ${fmt(p[4], 2)}`, p[5] === null ? "—" : fmt(p[5], 2)]), 0),
        fonte: `Previsões do modelo ${modelo.modelo_nome} (${modelo.versao}), teste com ${modelo.ano_teste}`, pagina: "dashboard.html",
        relacionados: ["Qual equipe o modelo mais errou?", "Qual é a previsão do Flamengo?"],
      });
  }

  // ---------- painel de curiosidades ----------
  function painel() {
    const cards = [];
    const ult = linhas(ultimoAno)[0];
    cards.push({ rotulo: `Campeão de ${ultimoAno}`, valor: ult.equipe, detalhe: `${ult.P} pontos · ${pct(ult.aprov)} de aproveitamento`, pergunta: `Quem foi o campeão de ${ultimoAno}?`, escudo: escudos[ult.equipe] || null });
    const gol = jogos.slice().sort((a, b) => Math.abs(b.gm - b.gv) - Math.abs(a.gm - a.gv) || b.gm + b.gv - (a.gm + a.gv))[0];
    cards.push({ rotulo: "Maior goleada", valor: `${gol.gm} × ${gol.gv}`, detalhe: `${gol.mandante} × ${gol.visitante} · ${dataBR(gol.data)}`, pergunta: "Quais foram as maiores goleadas?" });
    const cont = new Map();
    for (const a of anos) { const c = linhas(a)[0].equipe; cont.set(c, (cont.get(c) || 0) + 1); }
    const [tit, nTit] = [...cont].sort((a, b) => b[1] - a[1])[0];
    cards.push({ rotulo: "Mais títulos no período", valor: tit, detalhe: `${plural(nTit, "título", "títulos")} em ${anos.length} temporadas`, pergunta: "Quem foram os campeões de cada temporada?", escudo: escudos[tit] || null });
    let melhorSeq = { melhor: 0 };
    for (const e of equipes) { const s = sequencia(e, null, (p) => p >= 1); if (s.melhor > melhorSeq.melhor) melhorSeq = s; }
    cards.push({ rotulo: "Maior sequência sem perder", valor: `${melhorSeq.melhor} jogos`, detalhe: `${melhorSeq.equipe} · ${dataBR(melhorSeq.ini)} a ${dataBR(melhorSeq.fim)}`, pergunta: "Maior sequência invicta da história", escudo: escudos[melhorSeq.equipe] || null });
    const total = jogos.reduce((s, j) => s + j.gm + j.gv, 0);
    const mand = jogos.filter((j) => j.gm > j.gv).length;
    cards.push({ rotulo: "Gols por partida", valor: fmt(total / jogos.length, 2), detalhe: `${fmt(total)} gols em ${fmt(jogos.length)} jogos`, pergunta: "Quantos gols por jogo no histórico?" });
    cards.push({ rotulo: "Vantagem de jogar em casa", valor: pct(mand / jogos.length), detalhe: "dos jogos terminam com vitória do mandante", pergunta: "Como as equipes vão como mandante e visitante?" });
    return cards;
  }

  return {
    jogoDestaque, formaRecente, resumoEquipe, melhorAno, campeoes, titulosEquipe, entradasSaidas, variacaoAnos,
    classificacaoApos, jogosDaRodada, placarMaisComum, maisGols, estatisticasCampeonato, listaDestaques,
    errosDoModelo, previsaoGeral, painel, relacionadosEquipe, mando,
  };
}
