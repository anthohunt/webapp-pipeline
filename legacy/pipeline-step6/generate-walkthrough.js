#!/usr/bin/env node
/**
 * generate-walkthrough.js
 *
 * Deterministic generator for the User Journey Walkthrough HTML deliverable
 * (Step 6, Phase 5b). Parses use-case docs, embeds screenshots as base64 data
 * URIs, and produces a single self-contained HTML file.
 *
 * Usage:
 *   node generate-walkthrough.js <project-dir>
 *
 * Where <project-dir> contains:
 *   tests/e2e/use-cases/m*-use-case.md        (source of truth for steps)
 *   docs/pipeline/spec-final.md               (story classifications)
 *   docs/delivery/screenshots/<name>.png      (captured screenshots)
 *
 * Output:
 *   docs/delivery/user-journey-walkthrough.html
 *
 * No agents, no LLM calls. Deterministic. Run it twice, get identical bytes.
 */

const fs = require('fs');
const path = require('path');

// ─── arg parsing ────────────────────────────────────────────────────────────
const projectDir = process.argv[2];
if (!projectDir) {
  console.error('Usage: node generate-walkthrough.js <project-dir>');
  process.exit(1);
}

const useCaseDir = path.join(projectDir, 'tests', 'e2e', 'use-cases');
const screenshotsDir = path.join(projectDir, 'docs', 'delivery', 'screenshots');
const specFinalPath = path.join(projectDir, 'docs', 'pipeline', 'spec-final.md');
const outputPath = path.join(projectDir, 'docs', 'delivery', 'user-journey-walkthrough.html');
// Optionnels : notes par capture (ex. provenance) et fragment HTML d'introduction.
const notesPath = path.join(projectDir, 'docs', 'delivery', 'screenshots-notes.json');
const introPath = path.join(projectDir, 'docs', 'delivery', 'walkthrough-intro.html');
const NOTES = fs.existsSync(notesPath) ? JSON.parse(fs.readFileSync(notesPath, 'utf8')) : {};
const INTRO = fs.existsSync(introPath) ? fs.readFileSync(introPath, 'utf8') : '';
let LANG = 'en';
let APP_NAME = null;
try {
  const cfg = JSON.parse(fs.readFileSync(path.join(projectDir, 'docs', 'pipeline', 'config.json'), 'utf8'));
  if (cfg.language) LANG = cfg.language;
  APP_NAME = cfg.appName || cfg.projectName || null;
} catch (e) { /* config absente : défauts */ }
if (!APP_NAME) {
  try {
    const t = fs.readFileSync(path.join(projectDir, 'index.html'), 'utf8').match(/<title>([^<]+)<\/title>/);
    if (t) APP_NAME = t[1].trim().replace(/&amp;/g, "&");
  } catch (e) { /* pas d'index.html */ }
}
const L = LANG === 'fr' ? {
  journey: 'Parcours utilisateur', toc: 'Sommaire', top: '↑ Haut de page', missing: 'Capture absente', justified: 'Étape non rejouée (raison ci-dessous)',
  subtitle: "Chaque histoire livrée, étape par étape, avec la capture de l'appli finale",
  milestones: 'jalons', stories: 'histoires', steps: 'étapes', storiesLower: 'histoires',
  cls: { UNCHANGED: 'inchangée', MODIFIED: 'modifiée', NEW: 'nouvelle', REMOVED: 'retirée', PARTIAL: 'partielle' },
} : {
  journey: 'User Journey', toc: 'Table of Contents', top: '↑ Back to top', missing: 'Screenshot missing', justified: 'Step not replayed (reason below)',
  subtitle: 'Complete documentation of every feature, user story, and edge case',
  milestones: 'milestones', stories: 'stories', steps: 'steps', storiesLower: 'stories',
  cls: { UNCHANGED: 'UNCHANGED', MODIFIED: 'MODIFIED', NEW: 'NEW', REMOVED: 'REMOVED', PARTIAL: 'PARTIAL' },
};

if (!fs.existsSync(useCaseDir)) {
  console.error(`Use-case directory not found: ${useCaseDir}`);
  process.exit(1);
}
if (!fs.existsSync(screenshotsDir)) {
  console.error(`Screenshots directory not found: ${screenshotsDir}`);
  process.exit(1);
}

// ─── spec-final parsing (story classifications) ─────────────────────────────
const classifications = {};
if (fs.existsSync(specFinalPath)) {
  const spec = fs.readFileSync(specFinalPath, 'utf8');
  // Match: "US-X.X ... [UNCHANGED]" or "US-NEW-N ... [NEW]" etc.
  const re = /((?:US|V)-[A-Z0-9.-]+)[^\n]*?\[(UNCHANGED|MODIFIED|NEW|REMOVED|PARTIAL)\]/g;
  let m;
  while ((m = re.exec(spec)) !== null) {
    classifications[m[1]] = m[2];
  }
}

// ─── use-case parsing ───────────────────────────────────────────────────────
function parseUseCase(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const lines = raw.split('\n');

  const milestone = { title: '', intro: '', stories: [] };
  let currentStory = null;
  let inStartingPoint = false;
  let startingPoint = '';

  // Format « plan de cas d'usage » (pipeline web app, 2026-10) :
  //   "# Jalon N — Titre : plan de cas d'usage", intro "**Démonstration** : …",
  //   "## US-X.X — Titre" / "## V-X.X — Titre", étapes "N. texte — capture `nom.png`",
  //   transverses "- **US-A11Y-001 — Titre** : 1. … — capture `a.png` ; 2. … — capture `b.png`".
  const CAPTURE_RE = /^(.*?)\s*—\s*capture\s*`([^`]+?)(?:\.png)?`\s*$/;
  const ID_RE = '((?:US|V)-[A-Z0-9.-]+)';
  let pendingSection = null;

  for (const line of lines) {
    // Milestone title
    if (line.startsWith('# Milestone') || line.startsWith('# Jalon')) {
      milestone.title = line.replace(/^#\s*/, '').replace(/\s*:\s*plan de cas d'usage\s*$/i, '').trim();
      continue;
    }
    const demo = line.match(/^\*\*Démonstration\*\*\s*:\s*(.+)$/);
    if (demo && !milestone.intro) {
      milestone.intro = demo[1].trim();
      continue;
    }
    // "## ID — Titre" (niveau 2) ou "## Section libre"
    if (/^##\s/.test(line) && !line.startsWith('## Starting point')) {
      let m2 = line.match(new RegExp(`^##\\s+${ID_RE}\\s*(?:—|-)\\s*(.+)$`));
      if (m2) {
        currentStory = { id: m2[1], title: m2[2].trim(), isEdgeCase: /\.E\d/.test(m2[1]), steps: [] };
        milestone.stories.push(currentStory);
      } else {
        // Section libre : ses puces déclarent leurs propres histoires ; si elle porte des étapes
        // numérotées, elle devient une histoire à l'id synthétisé (créée à la première étape).
        currentStory = null;
        pendingSection = line.replace(/^##\s+/, '').trim();
      }
      continue;
    }
    // Puce transverse qui porte son histoire et ses étapes
    const tb = line.match(new RegExp(`^-\\s+\\*\\*${ID_RE}\\s*—\\s*(.+?)\\*\\*\\s*:\\s*(.*)$`));
    if (tb) {
      const story = { id: tb[1], title: tb[2].trim(), isEdgeCase: false, steps: [] };
      for (const part of tb[3].split(/\s;\s(?=\d+\.)/)) {
        const cm = part.replace(/^\d+\.\s*/, '').match(CAPTURE_RE);
        if (cm) story.steps.push({ screenshot: cm[2].trim(), description: cm[1].trim() });
      }
      milestone.stories.push(story);
      continue;
    }
    // Étape numérotée "N. texte — capture `nom.png`"
    const cap = line.match(/^\d+\.\s+(.*)$/);
    if (cap && !currentStory && pendingSection && CAPTURE_RE.test(cap[1])) {
      currentStory = { id: `SECTION-${pendingSection.replace(/[^\w]+/g, '-').toLowerCase()}`, title: pendingSection, isEdgeCase: false, steps: [] };
      milestone.stories.push(currentStory);
      pendingSection = null;
    }
    if (cap && currentStory) {
      const cm = cap[1].match(CAPTURE_RE);
      if (cm) {
        currentStory.steps.push({ screenshot: cm[2].trim(), description: cm[1].trim() });
        continue;
      }
    }
    // Starting point
    if (line.startsWith('## Starting point')) {
      inStartingPoint = true;
      continue;
    }
    if (inStartingPoint && line.startsWith('## ')) {
      inStartingPoint = false;
      milestone.intro = startingPoint.trim();
    }
    if (inStartingPoint && line.trim()) {
      startingPoint += line + ' ';
    }
    // Story section — multiple accepted formats:
    //   "### US-X.X — Title"                (primary story, dash separator)
    //   "### US-X.X Edge Cases"             (edge cases bundled under a story)
    //   "### Accessibility (US-A11Y)"       (accessibility section)
    //   "### US-A11Y-001 — Title"           (accessibility story by id)
    if (line.startsWith('### ')) {
      if (inStartingPoint) {
        inStartingPoint = false;
        milestone.intro = startingPoint.trim();
      }
      let id = null;
      let title = null;
      // Format 1: "### US-X.X — Title" or "### US-X.X - Title"
      let m = line.match(/^###\s+(US-[A-Z0-9.-]+)\s*(?:—|-)\s*(.+)$/);
      if (m) {
        id = m[1];
        title = m[2].trim();
      } else {
        // Format 2: "### US-X.X Edge Cases"  (no dash, just space)
        m = line.match(/^###\s+(US-[A-Z0-9.-]+)\s+(.+)$/);
        if (m) {
          id = `${m[1]}-edge`;
          title = m[2].trim();
        } else {
          // Format 3: "### Accessibility (US-A11Y)" or any "### <anything> (US-X)"
          m = line.match(/^###\s+(.+?)\s*\((US-[A-Z0-9.-]+)\)\s*$/);
          if (m) {
            id = m[2];
            title = m[1].trim();
          } else {
            // Format 4: bare "### Accessibility" or similar — synthesize an id
            const bareMatch = line.match(/^###\s+(.+)$/);
            if (bareMatch) {
              const synth = bareMatch[1].trim().replace(/[^\w]/g, '-').toLowerCase();
              id = `SECTION-${synth}`;
              title = bareMatch[1].trim();
            }
          }
        }
      }
      if (id && title) {
        const isEdgeCase = /edge case/i.test(title);
        currentStory = {
          id,
          title,
          isEdgeCase,
          steps: [],
        };
        milestone.stories.push(currentStory);
      }
      continue;
    }
    // Step line with screenshot
    const stepMatch = line.match(/^\d+\.\s*\[screenshot:\s*([^\]]+)\]\s*(.*)$/);
    if (stepMatch && currentStory) {
      const [, screenshot, description] = stepMatch;
      currentStory.steps.push({
        screenshot: screenshot.trim(),
        description: description.trim(),
      });
      continue;
    }
    // Bullet line with screenshot (edge case format)
    const bulletMatch = line.match(/^-\s*\[screenshot:\s*([^\]]+)\]\s*(.*)$/);
    if (bulletMatch && currentStory) {
      const [, screenshot, description] = bulletMatch;
      currentStory.steps.push({
        screenshot: screenshot.trim(),
        description: description.trim(),
      });
    }
  }

  return milestone;
}

// ─── screenshot → base64 ────────────────────────────────────────────────────
function embedScreenshot(name) {
  const filePath = path.join(screenshotsDir, `${name}.png`);
  if (!fs.existsSync(filePath)) {
    return null;
  }
  const data = fs.readFileSync(filePath);
  return `data:image/png;base64,${data.toString('base64')}`;
}

// ─── html generation ────────────────────────────────────────────────────────
const MILESTONE_COLORS = [
  '#c17b47', // M1 terracotta
  '#7a9b6e', // M2 sage
  '#4a7c8a', // M3 teal
  '#b8806a', // M4 clay
  '#5f7a5f', // M5 moss
  '#8a6d4a', // M6 bronze
];

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function badgeClass(cls) {
  if (cls === 'MODIFIED') return 'badge-modified';
  if (cls === 'NEW') return 'badge-new';
  if (cls === 'REMOVED') return 'badge-removed';
  if (cls === 'PARTIAL') return 'badge-modified';
  return 'badge-unchanged';
}

function renderStep(step, index, milestoneColor) {
  const img = embedScreenshot(step.screenshot);
  const imgHtml = img
    ? `<img src="${img}" alt="${escapeHtml(step.screenshot)}" loading="lazy" />`
    : NOTES[step.screenshot]
      ? `<div class="justified-screenshot">${L.justified} : ${escapeHtml(step.screenshot)}</div>`
      : `<div class="missing-screenshot">${L.missing} : ${escapeHtml(step.screenshot)}</div>`;
  const note = NOTES[step.screenshot] ? `<p class="step-note">${escapeHtml(NOTES[step.screenshot])}</p>` : '';
  return `
    <div class="step">
      <div class="step-num" style="background:${milestoneColor}">${index + 1}</div>
      <div class="step-body">
        <p class="step-description">${escapeHtml(step.description)}</p>
        <div class="step-screenshot">${imgHtml}</div>
        ${note}
      </div>
    </div>
  `;
}

function renderStory(story, milestoneColor) {
  const classification = classifications[story.id] || 'UNCHANGED';
  const badge = `<span class="badge ${badgeClass(classification)}">${L.cls[classification] || classification}</span>`;
  const steps = story.steps
    .map((s, i) => renderStep(s, i, milestoneColor))
    .join('\n');
  return `
    <section class="story" id="${story.id}">
      <h3 class="story-title">
        <span class="story-id">${story.id}</span>
        ${escapeHtml(story.title)}
        ${badge}
      </h3>
      <div class="story-steps">
        ${steps}
      </div>
    </section>
  `;
}

function renderMilestone(milestone, index) {
  const color = MILESTONE_COLORS[index] || MILESTONE_COLORS[0];
  const mid = `m${index + 1}`;
  const storiesHtml = milestone.stories
    .map((s) => renderStory(s, color))
    .join('\n');
  return `
    <article class="milestone" id="${mid}" style="--milestone-color:${color}">
      <header class="milestone-header">
        <h2>${escapeHtml(milestone.title)}</h2>
        <p class="milestone-intro">${escapeHtml(milestone.intro)}</p>
        <p class="milestone-meta">${milestone.stories.length} ${L.storiesLower}</p>
      </header>
      ${storiesHtml}
      <a class="back-to-top" href="#top">${L.top}</a>
    </article>
  `;
}

function renderToc(milestones) {
  return milestones
    .map((m, i) => {
      const mid = `m${i + 1}`;
      const storyLinks = m.stories
        .map((s) => `<li><a href="#${s.id}">${s.id} — ${escapeHtml(s.title)}</a></li>`)
        .join('');
      return `
        <div class="toc-milestone">
          <a class="toc-milestone-link" href="#${mid}" style="--ms-color:${MILESTONE_COLORS[i]}">${escapeHtml(m.title)}</a>
          <ul class="toc-stories">${storyLinks}</ul>
        </div>
      `;
    })
    .join('\n');
}

function renderHtml(milestones, projectName) {
  const title = `${projectName} — ${L.journey}`;
  const tocHtml = renderToc(milestones);
  const milestonesHtml = milestones.map((m, i) => renderMilestone(m, i)).join('\n');
  const totalStories = milestones.reduce((acc, m) => acc + m.stories.length, 0);
  const totalSteps = milestones.reduce(
    (acc, m) => acc + m.stories.reduce((a, s) => a + s.steps.length, 0),
    0
  );

  return `<!DOCTYPE html>
<html lang="${LANG}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #faf9f6;
    --surface: #ffffff;
    --border: #e5e2dc;
    --text: #2d2a26;
    --text-sec: #6b6660;
    --text-muted: #8a8580;
    --accent: #4a7c59;
    --radius: 10px;
    --shadow: 0 2px 8px rgba(0,0,0,0.04);
    --shadow-lg: 0 4px 16px rgba(0,0,0,0.08);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    font-family: 'DM Sans', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    font-size: 15px;
  }
  h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }

  /* Layout */
  .layout {
    display: flex;
    min-height: 100vh;
  }
  .toc {
    position: sticky;
    top: 0;
    width: 280px;
    height: 100vh;
    overflow-y: auto;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 24px 20px;
    flex-shrink: 0;
  }
  .toc-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 16px;
  }
  .toc-milestone { margin-bottom: 20px; }
  .toc-milestone-link {
    display: block;
    font-weight: 600;
    font-size: 13px;
    color: var(--ms-color, var(--text));
    text-decoration: none;
    padding: 6px 0;
    border-bottom: 2px solid var(--ms-color, var(--border));
    margin-bottom: 6px;
  }
  .toc-milestone-link:hover { opacity: 0.8; }
  .toc-stories { list-style: none; padding-left: 0; }
  .toc-stories li { margin: 3px 0; }
  .toc-stories a {
    display: block;
    font-size: 12px;
    color: var(--text-sec);
    text-decoration: none;
    padding: 3px 6px;
    border-radius: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .toc-stories a:hover {
    background: var(--bg);
    color: var(--text);
  }

  /* Main content */
  .main {
    flex: 1;
    padding: 48px 56px;
    max-width: 900px;
  }
  .header {
    margin-bottom: 48px;
    padding-bottom: 24px;
    border-bottom: 2px solid var(--border);
  }
  .header h1 {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 8px;
  }
  .header .subtitle {
    font-size: 16px;
    color: var(--text-sec);
  }
  .header .stats {
    margin-top: 16px;
    display: flex;
    gap: 24px;
    font-size: 13px;
    color: var(--text-muted);
  }
  .header .stat strong {
    color: var(--text);
    font-weight: 600;
  }

  /* Milestone */
  .milestone {
    margin-bottom: 64px;
    padding-top: 24px;
  }
  .milestone-header {
    border-left: 4px solid var(--milestone-color);
    padding-left: 20px;
    margin-bottom: 32px;
  }
  .milestone-header h2 {
    font-size: 28px;
    color: var(--milestone-color);
    margin-bottom: 8px;
  }
  .milestone-intro {
    color: var(--text-sec);
    font-size: 15px;
    max-width: 640px;
  }
  .milestone-meta {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 6px;
  }

  /* Story */
  .story {
    margin-bottom: 40px;
    padding: 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
  }
  .story-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .story-id {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: var(--text-muted);
    background: var(--bg);
    padding: 3px 10px;
    border-radius: 4px;
  }
  .badge {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 4px;
  }
  .badge-unchanged { background: #e8f0e4; color: #3a6b2e; }
  .badge-modified { background: #fff0d6; color: #9b5b00; }
  .badge-new { background: #d9e8f5; color: #1a5a8f; }
  .badge-removed { background: #f5d9d9; color: #8f1a1a; }

  /* Step */
  .step {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  .step:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }
  .step-num {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    color: white;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .step-body { flex: 1; min-width: 0; }
  .step-description {
    font-size: 14px;
    color: var(--text);
    margin-bottom: 12px;
  }
  .step-screenshot img {
    max-width: 100%;
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow-lg);
    display: block;
  }
  .step-note { font-size: 12px; color: var(--text-muted); margin-top: 8px; font-style: italic; }
  .intro { margin-top: 20px; font-size: 14px; color: var(--text-sec); }
  .intro ul { margin: 8px 0 0 20px; }
  .justified-screenshot { padding: 16px; background: #f6f4ef; border: 1px dashed #b8b2a7; border-radius: 8px; color: var(--text-sec); font-size: 13px; }
  .missing-screenshot {
    padding: 20px;
    background: #fff5f5;
    border: 1px dashed #dc2626;
    border-radius: 8px;
    color: #8f1a1a;
    font-size: 13px;
    font-family: monospace;
  }

  /* Back to top */
  .back-to-top {
    display: inline-block;
    margin-top: 32px;
    font-size: 13px;
    color: var(--text-muted);
    text-decoration: none;
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--surface);
  }
  .back-to-top:hover {
    background: var(--bg);
    color: var(--text);
  }

  /* Mobile */
  @media (max-width: 900px) {
    .layout { flex-direction: column; }
    .toc {
      position: relative;
      width: 100%;
      height: auto;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }
    .main { padding: 32px 20px; }
  }
</style>
</head>
<body>
<a id="top"></a>
<div class="layout">
  <nav class="toc">
    <div class="toc-title">${L.toc}</div>
    ${tocHtml}
  </nav>
  <main class="main">
    <div class="header">
      <h1>${escapeHtml(title)}</h1>
      <p class="subtitle">${L.subtitle}</p>
      ${INTRO}
      <div class="stats">
        <div class="stat"><strong>${milestones.length}</strong> ${L.milestones}</div>
        <div class="stat"><strong>${totalStories}</strong> ${L.stories}</div>
        <div class="stat"><strong>${totalSteps}</strong> ${L.steps}</div>
      </div>
    </div>
    ${milestonesHtml}
  </main>
</div>
</body>
</html>
`;
}

// ─── main ────────────────────────────────────────────────────────────────────
function main() {
  const files = fs
    .readdirSync(useCaseDir)
    .filter((f) => /^m\d+-use-case\.md$/.test(f))
    .sort();

  if (files.length === 0) {
    console.error(`No m*-use-case.md files found in ${useCaseDir}`);
    process.exit(1);
  }

  const milestones = files.map((f) => parseUseCase(path.join(useCaseDir, f)));

  // Count screenshots
  let totalSteps = 0;
  let missingScreenshots = 0;
  let justifiedScreenshots = 0;
  for (const m of milestones) {
    for (const s of m.stories) {
      for (const step of s.steps) {
        totalSteps++;
        if (!fs.existsSync(path.join(screenshotsDir, `${step.screenshot}.png`))) {
          // Une absence expliquée dans screenshots-notes.json est justifiée, pas manquante.
          if (NOTES[step.screenshot]) justifiedScreenshots++;
          else missingScreenshots++;
        }
      }
    }
  }

  // Infer project name from dir
  const projectName = APP_NAME || path.basename(projectDir).replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const html = renderHtml(milestones, projectName);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, 'utf8');

  const sizeBytes = fs.statSync(outputPath).size;
  const sizeMB = (sizeBytes / 1024 / 1024).toFixed(2);

  console.log(`✓ Generated ${outputPath}`);
  console.log(`  Milestones: ${milestones.length}`);
  console.log(`  Stories: ${milestones.reduce((a, m) => a + m.stories.length, 0)}`);
  console.log(`  Steps: ${totalSteps}`);
  console.log(`  Missing screenshots: ${missingScreenshots}`);
  console.log(`  Justified absences (noted): ${justifiedScreenshots}`);
  console.log(`  File size: ${sizeMB} MB`);

  if (missingScreenshots > 0) {
    console.warn(`\n⚠  ${missingScreenshots} screenshots are missing — HTML shows placeholders for those.`);
    process.exit(2);
  }
}

main();
