import { $, el, iniciarPagina } from "./comum.js";

const status = $("#dash-status");
const moldura = $("#dash-moldura");
const vazio = $("#dash-vazio");

function mostrarVazio() {
  moldura.hidden = true;
  vazio.hidden = false;
  status.textContent = "Em publicação";
}

function mostrarRelatorio(url) {
  const quadro = el("iframe", {
    title: "Dashboard Além do Placar no Power BI",
    src: url,
    allowfullscreen: true,
    referrerpolicy: "no-referrer",
    loading: "lazy",
  });
  quadro.addEventListener("load", () => {
    const aviso = $("#dash-carregando");
    if (aviso) aviso.remove();
    status.textContent = "Power BI conectado";
  });
  moldura.append(quadro);
  $("#dash-acoes").hidden = false;
  $("#dash-nova-aba").href = url;
  $("#dash-tela-cheia").addEventListener("click", () => {
    if (quadro.requestFullscreen) quadro.requestFullscreen();
  });
}

const cfg = await iniciarPagina();
if (cfg && cfg.powerbi_embed_url) mostrarRelatorio(cfg.powerbi_embed_url);
else mostrarVazio();
