import { $, api, el, ErroApi, fmt, iniciarPagina } from "./comum.js";

iniciarPagina();

const lista = $("#lista");
const form = $("#form");
const campo = $("#pergunta");
const enviar = $("#enviar");
let ocupado = false;

const ROTULOS = {
  equipe: "Equipe", posicao: "Pos.", jogos: "Jogos", pontos: "Pts", vitorias: "V", empates: "E",
  derrotas: "D", gols_pro: "GP", gols_contra: "GC", saldo: "SG", aproveitamento: "Aprov. (%)",
  temporada: "Temporada", partidas: "Partidas", gols_por_jogo: "Gols/jogo",
  vitorias_mandante_pct: "Vit. mandante (%)", empates_pct: "Empates (%)", mando: "Mando",
  pontos_por_jogo: "Pts/jogo", vitorias_pct: "Vitórias (%)", gols_pro_por_jogo: "GP/jogo",
  gols_contra_por_jogo: "GC/jogo", maior_sequencia: "Maior sequência", inicio: "Início", fim: "Fim",
  data: "Data", mandante: "Mandante", placar: "Placar", metrica: "Métrica", valor: "Valor",
  media_atual: "Média atual", media_anterior: "Média anterior", variacao: "Variação",
  previsao: "Previsão", limite_inferior: "Limite inferior", limite_superior: "Limite superior",
  atributo: "Variável", delta_mae_media: "Impacto no erro (ΔMAE)", delta_mae_desvio: "Desvio",
  escopo: "Escopo", mae: "MAE", rmse: "RMSE", vies: "Viés", n: "N", desvio: "Desvio",
};
const rotulo = (c) => ROTULOS[c] || c.replace(/_/g, " ").replace(/^./, (m) => m.toUpperCase());

function celula(valor) {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor === "number") return Number.isInteger(valor) ? fmt.inteiro(valor) : fmt.decimal(valor, 2);
  return String(valor);
}

function tabela(linhas) {
  const colunas = Object.keys(linhas[0]);
  const cabeca = el("tr", {}, colunas.map((c) => el("th", { scope: "col", classe: typeof linhas[0][c] === "number" ? "num" : "", texto: rotulo(c) })));
  const corpo = linhas.map((l) =>
    el("tr", {}, colunas.map((c) => el("td", { classe: typeof l[c] === "number" ? "num" : "", texto: celula(l[c]) }))),
  );
  const t = el("table", {}, el("thead", {}, cabeca), el("tbody", {}, corpo));
  return el("div", { classe: "tabela-rolagem", tabindex: "0", role: "region", "aria-label": "Tabela de dados" }, t);
}

function detalhes(d) {
  const itens = [];
  if (d.fonte) itens.push(el("dt", { texto: "Fonte" }), el("dd", { texto: d.fonte }));
  if (d.periodo) itens.push(el("dt", { texto: "Período" }), el("dd", { texto: d.periodo }));
  if (d.modelo) itens.push(el("dt", { texto: "Modelo" }), el("dd", { texto: `${d.modelo} (${d.versao_modelo || "s/ versão"})` }));
  const partes = [el("summary", { texto: "Fonte, período e limitações" })];
  if (itens.length) partes.push(el("dl", {}, itens));
  if (Array.isArray(d.limitacoes) && d.limitacoes.length) {
    partes.push(el("ul", {}, d.limitacoes.map((l) => el("li", { texto: l }))));
  }
  return el("details", { classe: "fonte" }, partes);
}

function rolarFim() {
  lista.scrollTop = lista.scrollHeight;
}

function adicionar(no, desdeInicio = false) {
  const vazio = $("#vazio");
  if (vazio) vazio.remove();
  lista.append(no);
  if (desdeInicio) lista.scrollTop = Math.max(0, no.offsetTop - 12);
  else rolarFim();
  return no;
}

function mensagemUsuario(texto) {
  return adicionar(el("div", { classe: "msg msg--usuario", texto }));
}

function mensagemBot(d) {
  const ia = d.modo === "llm";
  const meta = el("div", { classe: "msg__meta" }, el("span", { classe: `selo ${ia ? "selo--ia" : "selo--basico"}`, texto: ia ? "Resposta com IA" : "Consulta direta" }));
  const corpo = [meta, el("p", { classe: "msg__texto", texto: d.texto })];
  if (Array.isArray(d.dados) && d.dados.length) corpo.push(tabela(d.dados));
  corpo.push(detalhes(d));
  return adicionar(el("div", { classe: "msg msg--bot" }, corpo), true);
}

function mensagemErro(texto) {
  return adicionar(el("div", { classe: "msg msg--bot msg--erro", role: "alert" }, el("p", { classe: "msg__texto", texto })));
}

function digitando() {
  return adicionar(
    el("div", { classe: "msg msg--bot", role: "status", "aria-label": "O assistente está respondendo" }, el("span", { classe: "digitando" }, el("i"), el("i"), el("i"))),
  );
}

function textoErro(e) {
  if (!(e instanceof ErroApi)) return "Algo deu errado. Tente novamente.";
  if (e.status === 429) return "Muitas perguntas em pouco tempo. Aguarde um minuto e tente de novo.";
  if (e.status === 422) return "Pergunta inválida. Use de 3 a 500 caracteres.";
  if (e.status === 413) return "A pergunta é grande demais.";
  if (e.status === 0) return "Sem conexão com o servidor. Verifique a internet e tente de novo.";
  return "O assistente está indisponível no momento. Tente novamente em instantes.";
}

async function perguntar(texto) {
  texto = texto.trim();
  if (ocupado || texto.length < 3) return;
  ocupado = true;
  enviar.disabled = true;
  mensagemUsuario(texto);
  const espera = digitando();
  const corpo = { pergunta: texto };
  if ($("#ano").value) corpo.ano = Number($("#ano").value);
  if ($("#equipe").value) corpo.equipe = $("#equipe").value;
  try {
    const d = await api("/api/pergunta", { method: "POST", body: JSON.stringify(corpo) });
    espera.remove();
    mensagemBot(d);
  } catch (e) {
    espera.remove();
    mensagemErro(textoErro(e));
  } finally {
    ocupado = false;
    enviar.disabled = false;
    campo.focus({ preventScroll: true });
  }
}

function ajustarAltura() {
  campo.style.height = "auto";
  campo.style.height = `${Math.min(campo.scrollHeight, 140)}px`;
}

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const texto = campo.value;
  campo.value = "";
  ajustarAltura();
  perguntar(texto);
});
campo.addEventListener("input", ajustarAltura);
campo.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) {
    ev.preventDefault();
    form.requestSubmit();
  }
});

function chip(texto) {
  const b = el("button", { classe: "chip", type: "button", texto });
  b.addEventListener("click", () => perguntar(texto));
  return b;
}

async function carregar() {
  try {
    const [ctx, sug] = await Promise.all([api("/api/contexto"), api("/api/sugestoes")]);
    for (const ano of [...ctx.anos].reverse()) $("#ano").append(el("option", { value: ano, texto: ano }));
    for (const eq of ctx.equipes) $("#equipe").append(el("option", { value: eq, texto: eq }));
    $("#sugestoes").append(...sug.sugestoes.map(chip));
    $("#temas").append(
      ...ctx.temas.map((t) =>
        el("li", {}, el("strong", { texto: t.categoria }), t.exemplos.map((ex) => el("div", {}, (() => {
          const b = el("button", { type: "button", texto: ex });
          b.addEventListener("click", () => perguntar(ex));
          return b;
        })()))),
      ),
    );
  } catch {
    $("#vazio").append(el("p", { classe: "msg--erro", texto: "Não foi possível carregar os dados do projeto. Recarregue a página." }));
  }
  const q = new URLSearchParams(location.search).get("q");
  if (q) perguntar(q.slice(0, 500));
}

carregar();
