// Utilidades compartilhadas pelo motor da Central (sem DOM, sem rede).

export const FONTE_PARTIDAS = "Calculado a partir das partidas do OpenFootball (CC0)";

export const fmt = (n, casas = 0) =>
  Number(n).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
export const pct = (n) => `${fmt(n * 100, 1)}%`;
export const dataBR = (iso) => iso.split("-").reverse().join("/");
export const sinal = (n) => (n > 0 ? `+${n}` : String(n));
export const ordinal = (n) => `${n}º`;

export const resposta = (tipo, titulo, texto, extra = {}) => ({ tipo, titulo, texto, ...extra });
export const tabelaLinhas = (colunas, linhas, escudoColuna = null) => ({
  colunas,
  linhas,
  ...(escudoColuna === null ? {} : { escudoColuna }),
});

/** Resultado do ponto de vista de uma equipe: "V", "E" ou "D". */
export const resultado = (gp, gc) => (gp > gc ? "V" : gp === gc ? "E" : "D");
export const pontosDe = (gp, gc) => (gp > gc ? 3 : gp === gc ? 1 : 0);

/** Lista em português: "A, B e C". */
export function lista(itens) {
  if (itens.length <= 1) return itens.join("");
  return `${itens.slice(0, -1).join(", ")} e ${itens[itens.length - 1]}`;
}

export function plural(n, singular, pluralTxt) {
  return `${fmt(n)} ${n === 1 ? singular : pluralTxt}`;
}
