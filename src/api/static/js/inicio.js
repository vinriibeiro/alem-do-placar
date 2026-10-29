import { api, definirTexto, el, fmt, iniciarPagina, $ } from "./comum.js";

iniciarPagina();

function marcarIndisponivel(ids) {
  for (const id of ids) definirTexto(id, "—");
}

async function indicadores() {
  try {
    const c = await api("/api/contexto");
    definirTexto("kpi-partidas", fmt.inteiro(c.partidas));
    definirTexto("kpi-partidas-nota", `${c.periodo || ""}`.replace("–", " a "));
    definirTexto("kpi-temporadas", fmt.inteiro(c.temporadas));
    definirTexto("kpi-temporadas-nota", `${fmt.inteiro(c.equipes.length)} equipes no histórico`);
    if (c.mae_global != null) {
      definirTexto("kpi-mae", fmt.decimal(c.mae_global));
      const base = c.mae_baseline != null ? `Referência simples: ${fmt.decimal(c.mae_baseline)}` : "Holdout 2025";
      definirTexto("kpi-mae-nota", base);
    } else {
      marcarIndisponivel(["kpi-mae"]);
    }
    if (c.cobertura != null) definirTexto("kpi-cobertura", fmt.percentual(c.cobertura));
    else marcarIndisponivel(["kpi-cobertura"]);
  } catch {
    marcarIndisponivel(["kpi-partidas", "kpi-temporadas", "kpi-mae", "kpi-cobertura"]);
  }
}

async function sugestoes() {
  const alvo = $("#sugestoes");
  try {
    const { sugestoes: lista } = await api("/api/sugestoes");
    for (const pergunta of lista.slice(0, 6)) {
      alvo.append(el("a", { classe: "chip", href: `/assistente?q=${encodeURIComponent(pergunta)}`, texto: pergunta }));
    }
  } catch {
    alvo.append(el("a", { classe: "chip", href: "/assistente", texto: "Abrir o assistente" }));
  }
}

indicadores();
sugestoes();
