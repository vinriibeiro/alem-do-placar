// Utilitários compartilhados. Todo texto dinâmico entra via textContent, nunca como HTML.

export const $ = (seletor, raiz = document) => raiz.querySelector(seletor);

export function el(tag, atributos = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(atributos)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "classe") e.className = v;
    else if (k === "texto") e.textContent = String(v);
    else e.setAttribute(k, v === true ? "" : String(v));
  }
  for (const f of filhos.flat()) {
    if (f === null || f === undefined) continue;
    e.append(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  return e;
}

export class ErroApi extends Error {
  constructor(status, mensagem) {
    super(mensagem);
    this.status = status;
  }
}

export async function api(caminho, opcoes = {}) {
  let resposta;
  try {
    resposta = await fetch(caminho, {
      headers: { "Content-Type": "application/json" },
      ...opcoes,
    });
  } catch {
    throw new ErroApi(0, "Sem conexão com o servidor.");
  }
  let corpo = null;
  try {
    corpo = await resposta.json();
  } catch {
    /* corpo vazio ou inválido */
  }
  if (!resposta.ok && !(corpo && typeof corpo.texto === "string")) {
    const detalhe = corpo && typeof corpo.detail === "string" ? corpo.detail : "";
    throw new ErroApi(resposta.status, detalhe);
  }
  return corpo;
}

const numero = (casas) =>
  new Intl.NumberFormat("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

export const fmt = {
  inteiro: (n) => new Intl.NumberFormat("pt-BR").format(n),
  decimal: (n, casas = 3) => numero(casas).format(n),
  percentual: (frac, casas = 1) => `${numero(casas).format(frac * 100)}%`,
};

export function definirTexto(id, texto) {
  const alvo = document.getElementById(id);
  if (alvo) alvo.textContent = texto;
}

function iniciarMenu() {
  const botao = $(".menu-btn");
  const nav = $("#nav");
  if (!botao || !nav) return;
  botao.addEventListener("click", () => {
    const aberto = nav.classList.toggle("aberto");
    botao.setAttribute("aria-expanded", String(aberto));
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && nav.classList.contains("aberto")) {
      nav.classList.remove("aberto");
      botao.setAttribute("aria-expanded", "false");
      botao.focus();
    }
  });
}

/** Lê um arquivo de dados públicos (``dados/<nome>.json``), servido pelo site estático ou pela API. */
export async function obter(nome) {
  let resposta;
  try {
    resposta = await fetch(`dados/${nome}.json`);
  } catch {
    throw new ErroApi(0, "Sem conexão.");
  }
  if (!resposta.ok) throw new ErroApi(resposta.status, "Dados indisponíveis.");
  return resposta.json();
}

async function iniciarRodape() {
  try {
    const cfg = await obter("config");
    if (cfg && cfg.repo_url) {
      const item = document.getElementById("rodape-repo");
      const link = item && item.querySelector("a");
      if (link) {
        link.href = cfg.repo_url;
        item.hidden = false;
      }
    }
    return cfg;
  } catch {
    return null;
  }
}

export function iniciarPagina() {
  iniciarMenu();
  return iniciarRodape();
}
