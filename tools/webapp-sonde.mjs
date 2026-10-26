// Relevé d'une page d'app web pour le tournage automatique (tools/webapp-tourner.py) : l'arbre d'accessibilité
// (rôles et noms, ce que visent les gestes du YAML de tournage) et une capture, après une suite de clics facultative.
//
//   node webapp-sonde.mjs <url> <capture.png> [--taille 1600x900] [--zoom 1.5] [--clic "role:nom"]... [--tape "role:nom=texte"]...
//
// Chaque --clic / --tape est joué dans l'ordre (premier élément de ce rôle et de ce nom), avec 1,2 s d'attente après.
// Le navigateur est le Chromium de Playwright (TOURNAGE_CHROMIUM, sinon le plus récent de ~/.cache/ms-playwright),
// sans profil : l'app s'ouvre à neuf.
import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// playwright-core est pris dans les scripts de tournage (TOURNAGE_SKILL_HOME), sinon à côté de ce fichier.
const require = createRequire(path.join(process.env.TOURNAGE_SKILL_HOME || path.dirname(new URL(import.meta.url).pathname), "package.json"));
const { chromium } = require("playwright-core");

const args = process.argv.slice(2);
const [url, capture] = args;
if (!url || !capture) {
  console.error('usage : node webapp-sonde.mjs <url> <capture.png> [--taille 1600x900] [--zoom 1.5] [--clic "role:nom"]... [--tape "role:nom=texte"]...');
  process.exit(2);
}
function chrome() {
  if (process.env.TOURNAGE_CHROMIUM) return process.env.TOURNAGE_CHROMIUM;
  const base = path.join(os.homedir(), ".cache", "ms-playwright");
  const dirs = fs.readdirSync(base).filter((d) => /^chromium-\d+$/.test(d)).sort((a, b) => Number(b.split("-")[1]) - Number(a.split("-")[1]));
  for (const d of dirs) { const f = path.join(base, d, "chrome-linux64", "chrome"); if (fs.existsSync(f)) return f; }
  throw new Error("Chromium de Playwright introuvable");
}
const i = args.indexOf("--taille");
const [w, h] = (i >= 0 ? args[i + 1] : "1600x900").split("x").map(Number);
// même cadrage que le tournage (zoom de webapp-tourner.py) : ce que l'agent voit est ce qui sera filmé
const iz = args.indexOf("--zoom");
const z = Number(iz >= 0 ? args[iz + 1] : 1.5);
const b = await chromium.launch({ executablePath: chrome(), headless: true });
const p = await b.newPage({ viewport: { width: Math.round(w / z), height: Math.round(h / z) }, deviceScaleFactor: z });
await p.goto(url, { waitUntil: "networkidle", timeout: 45000 }).catch(() => {});
await p.waitForTimeout(1500);
const cible = (s) => { const k = s.indexOf(":"); return p.getByRole(s.slice(0, k), { name: s.slice(k + 1) }).first(); };
for (let k = 2; k < args.length; k++) {
  try {
    if (args[k] === "--clic") { await cible(args[++k]).click({ timeout: 10000 }); await p.waitForTimeout(1200); }
    else if (args[k] === "--tape") { const [c, t] = args[++k].split(/=(.*)/s); await cible(c).fill(t, { timeout: 10000 }); await p.waitForTimeout(1200); }
  } catch (e) { console.log(`ÉCHEC sur ${args[k]} : ${String(e.message).split("\n")[0]}`); break; }
}
console.log(`url : ${p.url()}`);
console.log(await p.locator("body").ariaSnapshot());
await p.screenshot({ path: capture });
await b.close();
