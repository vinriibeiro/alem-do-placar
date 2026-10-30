// Imprime respostas reais da Central para conferência manual.
// Uso: CENTRAL_DADOS=<pasta> node scripts/ver_respostas.mjs "pergunta 1" "pergunta 2" ...
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { criarMotor } from "../src/api/static/js/motor.js";

const pasta = process.env.CENTRAL_DADOS;
const dados = Object.fromEntries(["partidas", "modelo", "destaques", "escudos", "conhecimento"].map((n) => [n, JSON.parse(readFileSync(join(pasta, `${n}.json`), "utf-8"))]));
const motor = criarMotor(dados);
for (const p of process.argv.slice(2)) {
  const r = motor.responder(p);
  console.log(`\n### ${p}\n[${r.tipo}] ${r.titulo}\n${r.texto}`);
  if (r.kpis) console.log("KPIs:", r.kpis.map((k) => k.join("=")).join(" | "));
  if (r.tabela) console.log(`Tabela (${r.tabela.linhas.length} linhas): ${r.tabela.colunas.join(" | ")}\n  ${r.tabela.linhas[0].join(" | ")}`);
  if (r.nota) console.log("Nota:", r.nota);
  if (r.relacionados) console.log("Relacionadas:", r.relacionados.join(" // "));
}
