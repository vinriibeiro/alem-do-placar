import { $, el, iniciarPagina, obter } from "./comum.js";
import { criarMotor } from "./motor.js";

iniciarPagina();

const ROTULO_TIPO = {
  estatistica: ["Estatística", "selo--ia"],
  conhecimento: ["Explicação", "selo"],
  sem_dados: ["Sem dados suficientes", "selo--aviso"],
  fora_tema: ["Fora do tema", "selo--aviso"],
  esclarecimento: ["Precisa de detalhe", "selo--basico"],
};
const HISTORICO = "alem-do-placar:historico";
let motor = null;

function lerHistorico() {
  try {
    return JSON.parse(sessionStorage.getItem(HISTORICO) || "[]");
  } catch {
    return [];
  }
}

function salvarHistorico(lista) {
  try {
    sessionStorage.setItem(HISTORICO, JSON.stringify(lista.slice(0, 8)));
  } catch {
    /* armazenamento indisponível: o histórico só não persiste */
  }
}

function desenharHistorico() {
  const lista = lerHistorico();
  $("#historico-card").hidden = lista.length === 0;
  $("#historico").replaceChildren(...lista.map((p) => el("li", {}, botaoPergunta(p, "link-pergunta"))));
}

function botaoPergunta(texto, classe = "chip") {
  const b = el("button", { type: "button", classe, texto });
  b.addEventListener("click", () => consultar(texto));
  return b;
}

function tabela(t) {
  const cab = el("tr", {}, t.colunas.map((c) => el("th", { scope: "col", texto: c })));
  const corpo = t.linhas.map((l) => el("tr", {}, l.map((v) => el("td", { classe: typeof v === "number" ? "num" : "", texto: v ?? "—" }))));
  return el("div", { classe: "tabela-rolagem", tabindex: "0", role: "region", "aria-label": "Tabela" }, el("table", {}, el("thead", {}, cab), el("tbody", {}, corpo)));
}

function cartao(res, pergunta) {
  const [rotulo, classe] = ROTULO_TIPO[res.tipo] || ROTULO_TIPO.conhecimento;
  const topo = el("div", { classe: "resposta__topo" }, el("span", { classe: `selo ${classe}`, texto: rotulo }), res.categoria ? el("span", { classe: "resposta__cat", texto: res.categoria }) : null);
  const partes = [topo, el("p", { classe: "resposta__pergunta", texto: pergunta }), el("h2", { classe: "resposta__titulo", texto: res.titulo })];
  const corpo = [el("p", { classe: "resposta__texto", texto: res.texto })];
  const imagem = res.imagem || res.escudo;
  if (imagem) {
    const fig = el("figure", { classe: res.imagem ? "resposta__foto" : "resposta__escudo" }, el("img", { src: imagem, alt: res.imagem ? `Foto: ${res.titulo}` : "Escudo do clube", loading: "lazy" }));
    if (res.credito) fig.append(el("figcaption", { texto: res.credito }));
    partes.push(el("div", { classe: "resposta__corpo" }, fig, el("div", {}, corpo)));
  } else {
    if (res.credito) corpo.push(el("p", { classe: "resposta__credito", texto: res.credito }));
    partes.push(...corpo);
  }
  if (res.tabela) partes.push(tabela(res.tabela));
  const rodape = [];
  if (res.fonte) {
    const fonte = el("p", { classe: "resposta__fonte" }, el("strong", { texto: "Origem: " }), res.fonte);
    if (res.link) fonte.append(" · ", el("a", { href: res.link, rel: "noopener", target: "_blank", texto: "ver a fonte" }));
    rodape.push(fonte);
  }
  if (res.pagina) rodape.push(el("a", { classe: "resposta__link", href: res.pagina, texto: "Ver no projeto →" }));
  if (rodape.length) partes.push(el("div", { classe: "resposta__rodape" }, rodape));
  if (res.relacionados && res.relacionados.length) {
    partes.push(el("div", { classe: "resposta__relacionados" }, el("span", { texto: "Relacionadas:" }), ...res.relacionados.map((p) => botaoPergunta(p))));
  }
  return el("article", { classe: `card resposta resposta--${res.tipo}` }, partes);
}

function consultar(texto, rolar = true) {
  texto = (texto || "").trim();
  if (!motor || !texto) return;
  $("#pergunta").value = texto;
  const filtros = { ano: $("#ano").value || null, equipe: $("#equipe").value || null };
  const res = motor.responder(texto, filtros);
  $("#resultado").replaceChildren(cartao(res, texto));
  $("#bloco-sugestoes").hidden = true;
  const hist = [texto, ...lerHistorico().filter((p) => p !== texto)];
  salvarHistorico(hist);
  desenharHistorico();
  if (rolar) $("#resultado").scrollIntoView({ behavior: "smooth", block: "start" });
}

function categorias(conhecimento) {
  const grupos = new Map();
  for (const item of conhecimento) {
    if (!grupos.has(item.categoria)) grupos.set(item.categoria, []);
    grupos.get(item.categoria).push(item);
  }
  return [...grupos.entries()].map(([nome, itens], i) =>
    el("details", { classe: "categoria", open: i === 0 }, el("summary", { texto: `${nome} (${itens.length})` }), el("ul", {}, itens.map((it) => el("li", {}, botaoPergunta(it.perguntas[0], "link-pergunta"))))),
  );
}

async function iniciar() {
  try {
    const nomes = ["partidas", "modelo", "destaques", "escudos", "conhecimento"];
    const lidos = await Promise.all(nomes.map((n) => obter(n)));
    const dados = Object.fromEntries(nomes.map((n, i) => [n, lidos[i]]));
    motor = criarMotor(dados);
    for (const ano of [...motor.anos].reverse()) $("#ano").append(el("option", { value: ano, texto: ano }));
    for (const eq of motor.equipes) $("#equipe").append(el("option", { value: eq, texto: eq }));
    $("#categorias").replaceChildren(...categorias(dados.conhecimento));
    $("#sugestoes").replaceChildren(...motor.sugestoes(8).map((p) => botaoPergunta(p)), botaoPergunta("Qual equipe teve o melhor ataque em 2025?"), botaoPergunta("Quem foi o artilheiro de 2025?"));
    $("#bloco-sugestoes").hidden = false;
    $("#estado").textContent = `${motor.anos.length} temporadas e ${dados.partidas.partidas.length.toLocaleString("pt-BR")} partidas carregadas.`;
    desenharHistorico();
    const q = new URLSearchParams(location.search).get("q");
    if (q) consultar(q.slice(0, 300), false);
  } catch {
    $("#estado").textContent = "Não foi possível carregar os dados do projeto. Recarregue a página.";
  }
}

$("#form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  consultar($("#pergunta").value);
});

iniciar();
