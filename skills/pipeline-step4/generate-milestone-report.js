#!/usr/bin/env node
/**
 * generate-milestone-report.js
 *
 * Generates a self-contained HTML delivery report for a pipeline milestone.
 *
 * Usage:
 *   node generate-milestone-report.js --project-dir /path/to/project --milestone 1 --production-url https://example.com --commit abc123
 */

'use strict';

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      const value = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
      args[key] = value;
    }
  }
  return args;
}

const args = parseArgs(process.argv);

const projectDir = args['project-dir'];
const milestoneNum = args['milestone'];
const productionUrl = args['production-url'] || '';
const commitHash = args['commit'] || '';

if (!projectDir || !milestoneNum) {
  console.error('Usage: node generate-milestone-report.js --project-dir /path --milestone N [--production-url URL] [--commit HASH]');
  process.exit(1);
}

const M = String(milestoneNum);

// ---------------------------------------------------------------------------
// File paths
// ---------------------------------------------------------------------------

const useCasePath = path.join(projectDir, 'tests', 'e2e', 'use-cases', `m${M}-use-case.md`);
const summaryPath = path.join(projectDir, 'tests', 'e2e', 'use-cases', `m${M}-summary.md`);
const specPath    = path.join(projectDir, 'docs', 'pipeline', 'spec.md');
const deliveryDir = path.join(projectDir, 'tests', 'e2e', 'delivery');
const explorationDir = path.join(projectDir, 'tests', 'e2e', 'exploration');
// Prefer annotated delivery screenshots; fall back to raw exploration screenshots
const screenshotDir = fs.existsSync(deliveryDir) ? deliveryDir : explorationDir;
const stepDescPath = path.join(deliveryDir, `m${M}-step-descriptions.json`);
const outputDir   = path.join(projectDir, 'docs', 'delivery');
const outputPath  = path.join(outputDir, `m${M}-delivery-report.html`);

// Load customer-friendly step descriptions if available
let stepDescriptions = {};
if (fs.existsSync(stepDescPath)) {
  try { stepDescriptions = JSON.parse(fs.readFileSync(stepDescPath, 'utf-8')); } catch (e) { /* ignore */ }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function readFileSafe(filePath) {
  if (!fs.existsSync(filePath)) {
    console.warn(`[WARN] File not found: ${filePath}`);
    return null;
  }
  return fs.readFileSync(filePath, 'utf8');
}

function encodeImageSafe(imgPath) {
  if (!fs.existsSync(imgPath)) {
    return null;
  }
  return `data:image/png;base64,${fs.readFileSync(imgPath).toString('base64')}`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ---------------------------------------------------------------------------
// Parse use-case markdown
// ---------------------------------------------------------------------------

/**
 * Returns an array of story objects:
 * {
 *   id: 'US-1.1',
 *   title: 'Dashboard Stats Display',
 *   happyPath: [ { step, action, expected, screenshot } ],
 *   edgeCases: [
 *     { id: 'E1', label: 'API Unreachable', steps: [ { step, action, expected, screenshot } ] }
 *   ]
 * }
 */
function parseUseCases(markdown) {
  const stories = [];
  if (!markdown) return stories;

  const lines = markdown.split('\n');
  let currentStory = null;
  let currentSection = null; // 'happy' | 'edge'
  let currentEdgeCase = null;
  let inTable = false;

  const tableRowRe = /^\|\s*(\d+)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|/;
  const storyHeadRe = /^##\s+(US-[\d.]+):\s+(.+)/;
  const happyPathRe = /^###\s+Happy Path/i;
  const edgeCaseRe  = /^###\s+Edge Case\s+(E\d+):\s*(.+)/i;

  for (const line of lines) {
    // Story header: ## US-1.1: Title
    const storyMatch = line.match(storyHeadRe);
    if (storyMatch) {
      currentStory = {
        id: storyMatch[1],
        title: storyMatch[2].trim(),
        happyPath: [],
        edgeCases: [],
      };
      stories.push(currentStory);
      currentSection = null;
      currentEdgeCase = null;
      inTable = false;
      continue;
    }

    if (!currentStory) continue;

    // Happy Path section
    if (happyPathRe.test(line)) {
      currentSection = 'happy';
      currentEdgeCase = null;
      inTable = false;
      continue;
    }

    // Edge Case section
    const edgeMatch = line.match(edgeCaseRe);
    if (edgeMatch) {
      currentSection = 'edge';
      currentEdgeCase = {
        id: edgeMatch[1],
        label: edgeMatch[2].trim(),
        steps: [],
      };
      currentStory.edgeCases.push(currentEdgeCase);
      inTable = false;
      continue;
    }

    // Table separator / header — skip
    if (line.startsWith('|---') || line.match(/^\|\s*Step\s*\|/i)) {
      inTable = true;
      continue;
    }

    // Table data row
    if (inTable && line.startsWith('|')) {
      const rowMatch = line.match(tableRowRe);
      if (rowMatch) {
        const step = {
          step: rowMatch[1].trim(),
          action: rowMatch[2].trim(),
          expected: rowMatch[3].trim(),
          screenshot: rowMatch[4].trim().replace(/`/g, '').trim(),
        };
        if (currentSection === 'happy') {
          currentStory.happyPath.push(step);
        } else if (currentSection === 'edge' && currentEdgeCase) {
          currentEdgeCase.steps.push(step);
        }
      }
      continue;
    }

    // Blank line or other: reset inTable if we leave the table
    if (!line.startsWith('|')) {
      inTable = false;
    }
  }

  return stories;
}

// ---------------------------------------------------------------------------
// Parse spec.md
// ---------------------------------------------------------------------------

/**
 * Returns a map: { 'US-1.1': { description, acceptanceCriteria: [], edgeCases: [] } }
 */
function parseSpec(markdown) {
  const specMap = {};
  if (!markdown) return specMap;

  const lines = markdown.split('\n');
  let currentUS = null;
  let section = null; // 'description' | 'ac' | 'edge'

  const storyHeadRe = /^###\s+(US-[\d.]+)\s*[—-]\s*(.+)/;
  const asARe = /^\*\*As a\*\*/i;
  const acHeadRe = /^####\s+Acceptance Criteria/i;
  const edgeHeadRe = /^####\s+Edge Cases/i;
  const acItemRe = /^\s*-\s+\*\*AC-\d+:\*\*\s+(.+)/;
  const edgeItemRe = /^\s*-\s+\*\*(US-[\d.]+-E\d+):\*\*\s+(.+)/;

  for (const line of lines) {
    const storyMatch = line.match(storyHeadRe);
    if (storyMatch) {
      currentUS = storyMatch[1];
      specMap[currentUS] = {
        title: storyMatch[2].trim(),
        description: '',
        acceptanceCriteria: [],
        edgeCases: {},
      };
      section = 'description';
      continue;
    }

    if (!currentUS) continue;

    if (asARe.test(line)) {
      specMap[currentUS].description = line.trim();
      continue;
    }

    if (acHeadRe.test(line)) {
      section = 'ac';
      continue;
    }

    if (edgeHeadRe.test(line)) {
      section = 'edge';
      continue;
    }

    if (section === 'ac') {
      const m = line.match(acItemRe);
      if (m) specMap[currentUS].acceptanceCriteria.push(m[1].trim());
    }

    if (section === 'edge') {
      const m = line.match(edgeItemRe);
      if (m) specMap[currentUS].edgeCases[m[1]] = m[2].trim();
    }
  }

  return specMap;
}

// ---------------------------------------------------------------------------
// Parse summary.md
// ---------------------------------------------------------------------------

/**
 * Returns { knownLimitations: string|null, whatsNext: string|null }
 * Captures the raw markdown content under each heading.
 */
function parseSummary(markdown) {
  if (!markdown) return { knownLimitations: null, whatsNext: null };

  const limitRe = /^##\s+Known Limitations/i;
  const nextRe  = /^##\s+What's (Coming )?Next/i;
  const otherH2 = /^##\s+/;

  const lines = markdown.split('\n');
  let section = null;
  const sections = { knownLimitations: [], whatsNext: [] };

  for (const line of lines) {
    if (limitRe.test(line)) { section = 'knownLimitations'; continue; }
    if (nextRe.test(line))  { section = 'whatsNext'; continue; }
    if (otherH2.test(line)) { section = null; continue; }
    if (section) sections[section].push(line);
  }

  return {
    knownLimitations: sections.knownLimitations.join('\n').trim() || null,
    whatsNext: sections.whatsNext.join('\n').trim() || null,
  };
}

// ---------------------------------------------------------------------------
// Convert simple markdown lists to HTML (for limitations/next sections)
// ---------------------------------------------------------------------------

function markdownListToHtml(md) {
  if (!md) return '';
  const lines = md.split('\n');
  let html = '';
  let inList = false;

  for (const line of lines) {
    const listMatch = line.match(/^\s*\d+\.\s+(.+)/);
    const bulletMatch = line.match(/^\s*[-*]\s+(.+)/);

    if (listMatch || bulletMatch) {
      if (!inList) { html += '<ul class="summary-list">'; inList = true; }
      html += `<li>${escapeHtml((listMatch || bulletMatch)[1])}</li>`;
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      const trimmed = line.trim();
      if (trimmed) html += `<p>${escapeHtml(trimmed)}</p>`;
    }
  }
  if (inList) html += '</ul>';
  return html;
}

// ---------------------------------------------------------------------------
// Extract milestone title from use case markdown
// ---------------------------------------------------------------------------

function extractMilestoneTitle(markdown) {
  if (!markdown) return `Milestone ${M}`;
  const match = markdown.match(/^#\s+M\d+\s+[^\n]+/m);
  if (!match) return `Milestone ${M}`;
  // "M1 Exploration Plan — Setup + Dashboard" → "Setup + Dashboard"
  const parts = match[0].replace(/^#\s+/, '').split(/[—-]/);
  if (parts.length >= 2) return parts.slice(1).join('—').trim();
  return parts[0].trim();
}

// ---------------------------------------------------------------------------
// Color palette for story sections
// ---------------------------------------------------------------------------

const PALETTE = [
  { light: '#e8f4fd', border: '#3498db', accent: '#2980b9' },
  { light: '#eafaf1', border: '#2ecc71', accent: '#27ae60' },
  { light: '#fef9e7', border: '#f39c12', accent: '#d68910' },
  { light: '#fdf2f8', border: '#9b59b6', accent: '#8e44ad' },
  { light: '#fef5e4', border: '#e67e22', accent: '#ca6f1e' },
  { light: '#eaf2ff', border: '#5dade2', accent: '#2471a3' },
];

// ---------------------------------------------------------------------------
// HTML generation helpers
// ---------------------------------------------------------------------------

function renderStepCard(step, idx, isEdge, screenshotBase64) {
  const badge = isEdge ? 'badge-edge' : 'badge-happy';
  const missingHtml = screenshotBase64
    ? `<img src="${screenshotBase64}" alt="${escapeHtml(step.screenshot)}" class="screenshot" loading="lazy">`
    : `<div class="screenshot-missing">Missing: ${escapeHtml(step.screenshot)}</div>`;

  // Use customer-friendly descriptions from step-descriptions.json if available
  const desc = stepDescriptions[step.screenshot];
  const actionText = desc ? desc.action : step.action;
  const expectedText = desc ? desc.expected : step.expected;

  const stepId = step.screenshot.replace(/\.png$/, '').replace(/[^a-zA-Z0-9-]/g, '_');

  return `
      <div class="step-card ${isEdge ? 'step-card--edge' : ''}" data-step-id="${escapeHtml(stepId)}">
        <div class="step-badge ${badge}">${escapeHtml(step.step)}</div>
        <div class="step-content">
          <div class="step-action"><strong>Action:</strong> ${escapeHtml(actionText)}</div>
          <div class="step-expected"><strong>Expected:</strong> ${escapeHtml(expectedText)}</div>
          ${missingHtml}
          <div class="step-feedback">
            <textarea class="fb-textarea" data-step-id="${escapeHtml(stepId)}" placeholder="Leave a comment..." rows="1"></textarea>
          </div>
        </div>
      </div>`;
}

function renderStory(story, specEntry, explorationDirPath, colorIdx, stats) {
  const color = PALETTE[colorIdx % PALETTE.length];
  const storyAnchor = `story-${story.id.replace(/\./g, '-')}`;

  // Acceptance criteria
  let acHtml = '';
  if (specEntry && specEntry.acceptanceCriteria.length > 0) {
    acHtml = `
      <div class="ac-section">
        <h4>Acceptance Criteria</h4>
        <ul class="ac-list">
          ${specEntry.acceptanceCriteria.map(ac => `<li>${escapeHtml(ac)}</li>`).join('\n          ')}
        </ul>
      </div>`;
  }

  // Happy path
  let happyHtml = '';
  if (story.happyPath.length > 0) {
    const stepsHtml = story.happyPath.map((step, i) => {
      stats.totalSteps++;
      const imgPath = path.join(explorationDirPath, step.screenshot);
      const b64 = encodeImageSafe(imgPath);
      if (b64) stats.embedded++; else stats.missing++;
      return renderStepCard(step, i, false, b64);
    }).join('');

    happyHtml = `
      <div class="subsection">
        <h4 class="subsection-title subsection-title--happy">Happy Path</h4>
        <div class="steps-list">${stepsHtml}</div>
      </div>`;
  }

  // Edge cases
  let edgesHtml = '';
  for (const ec of story.edgeCases) {
    const ecKey = `${story.id}-${ec.id}`;
    const ecDesc = (specEntry && specEntry.edgeCases[ecKey]) || '';

    const stepsHtml = ec.steps.map((step, i) => {
      stats.totalSteps++;
      const imgPath = path.join(explorationDirPath, step.screenshot);
      const b64 = encodeImageSafe(imgPath);
      if (b64) stats.embedded++; else stats.missing++;
      return renderStepCard(step, i, true, b64);
    }).join('');

    edgesHtml += `
      <div class="subsection">
        <h4 class="subsection-title subsection-title--edge">Edge Case ${escapeHtml(ec.id)}: ${escapeHtml(ec.label)}</h4>
        ${ecDesc ? `<p class="edge-desc">${escapeHtml(ecDesc)}</p>` : ''}
        <div class="steps-list">${stepsHtml}</div>
      </div>`;
  }

  const description = (specEntry && specEntry.description)
    ? `<p class="story-description">${escapeHtml(specEntry.description)}</p>`
    : '';

  return `
    <section class="story-section" id="${storyAnchor}" style="--story-light:${color.light};--story-border:${color.border};--story-accent:${color.accent}">
      <div class="story-header" style="border-left: 4px solid ${color.border}; background: ${color.light};">
        <span class="story-id">${escapeHtml(story.id)}</span>
        <h2 class="story-title">${escapeHtml(story.title)}</h2>
      </div>
      ${description}
      ${acHtml}
      ${happyHtml}
      ${edgesHtml}
    </section>`;
}

// ---------------------------------------------------------------------------
// Sidebar TOC
// ---------------------------------------------------------------------------

function renderToc(stories) {
  const items = stories.map(s => {
    const anchor = `story-${s.id.replace(/\./g, '-')}`;
    return `<li><a href="#${anchor}" class="toc-link" data-target="${anchor}">${escapeHtml(s.id)}: ${escapeHtml(s.title)}</a></li>`;
  }).join('\n        ');

  return `
    <nav class="sidebar" id="sidebar">
      <div class="toc-heading">Table of Contents</div>
      <ul class="toc-list">
        ${items}
        <li><a href="#section-limitations" class="toc-link" data-target="section-limitations">Known Limitations</a></li>
        <li><a href="#section-next" class="toc-link" data-target="section-next">What's Next</a></li>
      </ul>
    </nav>`;
}

// ---------------------------------------------------------------------------
// Full HTML document
// ---------------------------------------------------------------------------

function buildHtml({ milestoneTitle, stories, specMap, explorationDirPath, summary, productionUrl, commitHash, stats }) {
  const generationDate = new Date().toISOString().slice(0, 10);
  const toc = renderToc(stories);

  const storiesHtml = stories.map((story, idx) => {
    const specEntry = specMap[story.id] || null;
    return renderStory(story, specEntry, explorationDirPath, idx, stats);
  }).join('\n');

  const limitationsHtml = summary.knownLimitations
    ? `<section class="extras-section" id="section-limitations">
        <h2>Known Limitations</h2>
        ${markdownListToHtml(summary.knownLimitations)}
      </section>`
    : `<section class="extras-section" id="section-limitations" style="display:none"></section>`;

  const nextHtml = summary.whatsNext
    ? `<section class="extras-section" id="section-next">
        <h2>What's Next</h2>
        ${markdownListToHtml(summary.whatsNext)}
      </section>`
    : `<section class="extras-section" id="section-next" style="display:none"></section>`;

  const productionLinkHtml = productionUrl
    ? `<a href="${escapeHtml(productionUrl)}" class="header-link" target="_blank" rel="noopener">${escapeHtml(productionUrl)}</a>`
    : '';

  const commitHtml = commitHash
    ? `<span class="header-meta">commit: <code>${escapeHtml(commitHash.slice(0, 8))}</code></span>`
    : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Milestone ${escapeHtml(M)} Delivery Report — ${escapeHtml(milestoneTitle)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Poppins', sans-serif;
      background: #faf9f6;
      color: #212529;
      min-height: 100vh;
    }

    /* ── Header ─────────────────────────────────────────────── */
    .site-header {
      background: #0c1b33;
      color: #fff;
      padding: 18px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .header-left { display: flex; flex-direction: column; gap: 4px; }
    .header-milestone {
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: -0.01em;
    }
    .header-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      font-size: 0.85rem;
      opacity: 0.85;
    }
    .header-link {
      color: #74c0fc;
      text-decoration: none;
      font-weight: 500;
    }
    .header-link:hover { text-decoration: underline; }
    .header-meta { color: #adb5bd; }
    .header-meta code { color: #e9ecef; font-size: 0.8rem; }
    .header-date { color: #adb5bd; }
    .highlight-legend { display: flex; align-items: center; gap: 10px; padding: 10px 24px; background: #fff8f0; border: 1px solid #f5c6a0; border-radius: 6px; margin: 16px 24px 0; font-size: 13px; color: #6c584c; }
    .legend-icon { display: inline-block; width: 18px; height: 14px; border: 3px solid #dc3545; border-radius: 3px; box-shadow: 0 0 0 4px rgba(220, 53, 69, 0.2); flex-shrink: 0; }

    /* ── Layout ─────────────────────────────────────────────── */
    .layout {
      display: flex;
      min-height: calc(100vh - 64px);
    }

    /* ── Sidebar ─────────────────────────────────────────────── */
    .sidebar {
      width: 280px;
      min-width: 280px;
      background: #fff;
      border-right: 1px solid #dee2e6;
      padding: 24px 0;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      flex-shrink: 0;
    }
    .toc-heading {
      font-weight: 700;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #6c757d;
      padding: 0 20px 12px;
      border-bottom: 1px solid #dee2e6;
      margin-bottom: 8px;
    }
    .toc-list {
      list-style: none;
      padding: 0 8px;
    }
    .toc-list li { margin: 2px 0; }
    .toc-link {
      display: block;
      padding: 7px 12px;
      border-radius: 6px;
      text-decoration: none;
      color: #495057;
      font-size: 0.82rem;
      font-weight: 500;
      transition: background 0.15s, color 0.15s;
    }
    .toc-link:hover {
      background: #f1f3f5;
      color: #0d6efd;
    }
    .toc-link.active {
      background: #e7f1ff;
      color: #0d6efd;
      font-weight: 600;
    }

    /* ── Main ─────────────────────────────────────────────────── */
    .main-content {
      flex: 1;
      padding: 32px 40px;
      max-width: 960px;
    }

    /* ── Story section ───────────────────────────────────────── */
    .story-section {
      margin-bottom: 56px;
      scroll-margin-top: 24px;
    }
    .story-header {
      padding: 16px 20px;
      border-radius: 8px 8px 0 0;
      display: flex;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 16px;
    }
    .story-id {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--story-accent);
      white-space: nowrap;
    }
    .story-title {
      font-size: 1.2rem;
      font-weight: 600;
      color: #212529;
    }
    .story-description {
      color: #495057;
      font-size: 0.9rem;
      margin-bottom: 16px;
      font-style: italic;
    }

    /* ── Acceptance criteria ─────────────────────────────────── */
    .ac-section {
      background: #f8f9fa;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 20px;
    }
    .ac-section h4 {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #6c757d;
      margin-bottom: 10px;
    }
    .ac-list {
      list-style: none;
      padding: 0;
    }
    .ac-list li {
      font-size: 0.88rem;
      color: #343a40;
      padding: 4px 0 4px 20px;
      position: relative;
    }
    .ac-list li::before {
      content: '✓';
      position: absolute;
      left: 0;
      color: #2ecc71;
      font-weight: 700;
    }

    /* ── Subsections ─────────────────────────────────────────── */
    .subsection {
      margin-bottom: 24px;
    }
    .subsection-title {
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
      padding: 6px 12px;
      border-radius: 4px;
      display: inline-block;
    }
    .subsection-title--happy {
      background: #e7f1ff;
      color: #0d6efd;
    }
    .subsection-title--edge {
      background: #fff3cd;
      color: #9a5500;
    }
    .edge-desc {
      font-size: 0.88rem;
      color: #6c757d;
      margin-bottom: 12px;
      font-style: italic;
    }

    /* ── Feedback controls ───────────────────────────────────── */
    .step-feedback { margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; }
    .fb-textarea {
      width: 100%;
      font-family: inherit;
      font-size: 0.82rem;
      padding: 8px 10px;
      border: 1px solid #dee2e6;
      border-radius: 6px;
      resize: vertical;
      min-height: 36px;
      transition: border-color 0.15s;
    }
    .fb-textarea:focus { outline: none; border-color: #0d6efd; }
    .fb-textarea.has-comment { border-color: #fd7e14; background: #fff8f0; }
    /* Saved comments rendered as visible text */
    .fb-saved-comment {
      margin-top: 8px;
      padding: 8px 12px;
      background: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 6px;
      font-size: 0.82rem;
      color: #664d03;
      white-space: pre-wrap;
    }
    .fb-saved-comment::before { content: '\\u{1F4AC} Comment: '; font-weight: 600; }
    .save-feedback-bar {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #0c1b33;
      color: #fff;
      padding: 10px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 100;
      box-shadow: 0 -2px 12px rgba(0,0,0,0.15);
    }
    .save-feedback-bar .fb-summary { font-size: 0.85rem; opacity: 0.9; }
    .save-feedback-bar button {
      background: #28a745;
      color: #fff;
      border: none;
      padding: 8px 24px;
      border-radius: 6px;
      font-family: inherit;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
    }
    .save-feedback-bar button:hover { background: #218838; }

    /* ── Step cards ──────────────────────────────────────────── */
    .steps-list { display: flex; flex-direction: column; gap: 16px; }
    .step-card {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.05);
      display: flex;
      gap: 0;
      overflow: hidden;
    }
    .step-card--edge .step-badge { background: #e67e22; }
    .step-badge {
      background: #0d6efd;
      color: #fff;
      width: 48px;
      min-width: 48px;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding-top: 18px;
      font-size: 1rem;
      font-weight: 700;
    }
    .step-content {
      flex: 1;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .step-action { font-size: 0.88rem; color: #343a40; }
    .step-expected { font-size: 0.85rem; color: #495057; }
    .screenshot {
      max-width: 100%;
      border: 1px solid #dee2e6;
      border-radius: 4px;
      margin-top: 4px;
    }
    .screenshot-missing {
      background: #fff5f5;
      border: 2px dashed #f5c6cb;
      color: #842029;
      font-size: 0.82rem;
      font-weight: 600;
      padding: 10px 16px;
      border-radius: 4px;
      margin-top: 4px;
    }

    /* ── Extras (limitations / next) ────────────────────────── */
    .extras-section {
      background: #fff;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      padding: 24px 28px;
      margin-bottom: 32px;
      scroll-margin-top: 24px;
    }
    .extras-section h2 {
      font-size: 1.1rem;
      font-weight: 700;
      color: #212529;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 2px solid #dee2e6;
    }
    .summary-list {
      list-style: none;
      padding: 0;
    }
    .summary-list li {
      font-size: 0.88rem;
      color: #343a40;
      padding: 6px 0 6px 22px;
      position: relative;
      border-bottom: 1px solid #f1f3f5;
    }
    .summary-list li:last-child { border-bottom: none; }
    .summary-list li::before {
      content: '•';
      position: absolute;
      left: 6px;
      color: #adb5bd;
      font-size: 1.2em;
      line-height: 1;
      top: 7px;
    }
    .extras-section p { font-size: 0.88rem; color: #495057; margin-bottom: 8px; }

    /* ── Responsive ──────────────────────────────────────────── */
    @media (max-width: 768px) {
      .layout { flex-direction: column; }
      .sidebar {
        width: 100%;
        min-width: unset;
        height: auto;
        position: relative;
        border-right: none;
        border-bottom: 1px solid #dee2e6;
        padding: 12px 0;
        overflow-x: auto;
      }
      .toc-list { display: flex; gap: 4px; padding: 0 12px; }
      .toc-list li { white-space: nowrap; }
      .main-content { padding: 20px 16px; }
      .site-header { flex-direction: column; align-items: flex-start; }
      .header-right { align-items: flex-start; }
    }
  </style>
</head>
<body>

  <header class="site-header">
    <div class="header-left">
      <div class="header-milestone">Milestone ${escapeHtml(M)} — ${escapeHtml(milestoneTitle)}</div>
    </div>
    <div class="header-right">
      ${productionLinkHtml}
      ${commitHtml}
      <span class="header-date">Generated: ${generationDate}</span>
    </div>
  </header>

  <div class="highlight-legend">
    <span class="legend-icon"></span>
    <span>Red highlights in screenshots are editorial annotations showing the area of interest for each step. They are not part of the application's interface.</span>
  </div>

  <div class="layout">
    ${toc}
    <main class="main-content">
      ${storiesHtml}
      ${limitationsHtml}
      ${nextHtml}
    </main>
  </div>

  <div class="save-feedback-bar">
    <span class="fb-summary" id="fbSummary">Write comments on any step, then click Save to embed them in this file.</span>
    <button onclick="window.saveComments()">Save comments</button>
  </div>

  <script>
    // ── Feedback: comment per step, Save embeds into HTML, I read the file ──
    (function() {
      // On load: restore comments from data-comment attributes (previously saved)
      document.querySelectorAll('.fb-textarea').forEach(function(ta) {
        var card = ta.closest('.step-card');
        var saved = card ? card.getAttribute('data-comment') : null;
        if (saved) {
          ta.value = saved;
          ta.classList.add('has-comment');
        }
        ta.addEventListener('input', function() {
          ta.classList.toggle('has-comment', !!ta.value.trim());
          updateCount();
        });
      });

      function updateCount() {
        var count = 0;
        document.querySelectorAll('.fb-textarea').forEach(function(ta) {
          if (ta.value.trim()) count++;
        });
        document.getElementById('fbSummary').textContent = count > 0
          ? count + ' comment' + (count > 1 ? 's' : '') + ' — click Save to embed in file'
          : 'Write comments on any step, then click Save to embed them in this file.';
      }
      updateCount();

      window.saveComments = function() {
        // Write each comment into data-comment on the step-card
        document.querySelectorAll('.fb-textarea').forEach(function(ta) {
          var card = ta.closest('.step-card');
          if (!card) return;
          var comment = ta.value.trim();
          if (comment) {
            card.setAttribute('data-comment', comment);
            // Also add a visible saved-comment div if not already there
            var existing = card.querySelector('.fb-saved-comment');
            if (existing) { existing.textContent = comment; }
            else {
              var div = document.createElement('div');
              div.className = 'fb-saved-comment';
              div.textContent = comment;
              ta.parentNode.appendChild(div);
            }
          } else {
            card.removeAttribute('data-comment');
            var existing = card.querySelector('.fb-saved-comment');
            if (existing) existing.remove();
          }
        });

        // Download the entire HTML with comments embedded
        var html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
        var blob = new Blob([html], { type: 'text/html' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'm${escapeHtml(M)}-delivery-report.html';
        a.click();

        document.getElementById('fbSummary').textContent = 'Saved! Replace docs/delivery/m${escapeHtml(M)}-delivery-report.html with the downloaded file, then tell Claude to check.';
      };
    })();

    // Active TOC link on scroll
    (function() {
      var links = document.querySelectorAll('.toc-link');
      var sections = [];
      links.forEach(function(link) {
        var target = document.getElementById(link.dataset.target);
        if (target) sections.push({ link: link, el: target });
      });

      function onScroll() {
        var scrollY = window.scrollY + 80;
        var active = null;
        for (var i = sections.length - 1; i >= 0; i--) {
          if (sections[i].el.offsetTop <= scrollY) {
            active = sections[i].link;
            break;
          }
        }
        links.forEach(function(l) { l.classList.remove('active'); });
        if (active) active.classList.add('active');
      }

      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    })();
  </script>

</body>
</html>`;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  console.log(`Generating Milestone ${M} delivery report...`);

  const useCaseMd = readFileSafe(useCasePath);
  const specMd    = readFileSafe(specPath);
  const summaryMd = readFileSafe(summaryPath);

  if (!useCaseMd) {
    console.error(`[ERROR] Use case file not found: ${useCasePath}`);
    process.exit(1);
  }

  const milestoneTitle = extractMilestoneTitle(useCaseMd);
  const stories = parseUseCases(useCaseMd);
  const specMap = parseSpec(specMd);
  const summary = parseSummary(summaryMd);

  const stats = { totalSteps: 0, embedded: 0, missing: 0 };

  // Ensure output dir exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const html = buildHtml({
    milestoneTitle,
    stories,
    specMap,
    explorationDirPath: screenshotDir,
    summary,
    productionUrl,
    commitHash,
    stats,
  });

  fs.writeFileSync(outputPath, html, 'utf8');

  console.log(`Generated ${path.basename(outputPath)} — ${stories.length} stories, ${stats.totalSteps} steps, ${stats.embedded} screenshots embedded, ${stats.missing} missing`);

  if (stats.missing > 0) {
    process.exit(2);
  }
}

main();
