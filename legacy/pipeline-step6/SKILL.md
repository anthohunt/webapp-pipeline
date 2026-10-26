---
name: pipeline-step6
description: Story reconciliation & delivery — reconcile planned vs built, final verification with screenshots, produce human + AI documentation, deliver. After Step 5. Final step.
---

# Pipeline Step 6 — Story Reconciliation & Delivery

Reconcile what was planned (Step 2 Project Kit) against what was built (Steps 4-5), update all documentation, run final verification with screenshots, produce the delivery package, and hand off.

---

## 1. Gate Check

Read `docs/pipeline/status.md` in the current project directory.

- **File does not exist:** Tell the user to run `/pipeline-step1` first.
- **Step < 5 complete:** Tell the user to finish earlier steps. Step 5 = Quality Hardening.
- **Step 5 complete:** Proceed to Phase 1.
- **Step 6 in progress:** Resume from the last completed phase.
- **Step 6 complete:** Warn and offer `/pipeline-step1` for a new iteration.

---

## 2. Phase 1 — Reconciliation

Read the original Step 2 Project Kit and compare against the built app.

**Inputs:**
- `docs/pipeline/spec.md` (original user stories from Step 2)
- `docs/pipeline/plan.md`, `tasks.md`, `rules.md`
- `docs/pipeline/design/` (Step 1 — canvas artboards, design system, screens.json)
- `docs/pipeline/system-architecture.html` (Step 2)
- All application source code
- `tests/e2e/use-cases/m*-use-case.md` (written in Step 2, filled in during Step 4)
- Git log (`git log --oneline`)
- Hardening reports (`docs/pipeline/hardening-r*-consolidated.md`)

**Per story, classify as:**
- `[UNCHANGED]` — built exactly as specced
- `[MODIFIED]` — feature exists but behavior differs. Explain what changed and why. If partially implemented (not all acceptance criteria met), classify as MODIFIED with the delta noted.
- `[NEW]` — exists in code but has no story in spec.md. Write a new story.
- `[REMOVED]` — in spec but not implemented. Explain why.

**Verify every hardening claim against HEAD source, not against the audit report.** `hardening-r*-consolidated.md` lists issues the auditor *found*; `hardening-r*-fixes.md` lists fixes the Fixer *applied*; git log + current source tells you what *actually shipped*. These can disagree — a hardening-consolidated entry marked "deferred" may in fact have been fixed in a later commit. Before classifying a story as MODIFIED because of a hardening fix, open the referenced file at HEAD (not the audit snapshot) and confirm the change is still there. Rule of thumb: `hardening-r*-fixes.md` supersedes `hardening-r*-consolidated.md`, and git HEAD supersedes both.

**Test coverage status:** For each story, note whether it has a Playwright E2E test.

**Present the report to the user** before proceeding. Wait for acknowledgment.

**Output:** `docs/pipeline/reconciliation-report.md`

Update `docs/pipeline/status.md`:
```markdown
- **Current step:** 6
- **Sub-step:** Phase 1 complete — reconciliation
```

---

## 3. Phase 2 — Update AI Documentation

Based on the reconciliation report, update and create all AI-facing documentation. Every file in this phase is a deliverable.

### 2a. spec-final.md

Ground truth of what the app actually does. Lives at `docs/pipeline/spec-final.md`. This is a NEW file created here; `spec.md` (the original plan) stays untouched as the historical record.

- `[UNCHANGED]` stories carried over as-is
- `[MODIFIED]` stories get updated acceptance criteria reflecting actual behavior
- `[NEW]` stories get full user story format (As a… I want… So that… + acceptance criteria)
- `[REMOVED]` stories listed in a "Removed" section with reason

### 2b. project-memory.md

Updated rolling summary of the project state at `docs/pipeline/project-memory.md`. Max 2000 chars. Covers: concept, milestones, final state, key changes from original plan.

### 2c. Use-case docs

Update `tests/e2e/use-cases/m*-use-case.md` for any modified/new stories. Remove steps for removed stories.

### 2d. decisions-log.md

NEW file at `docs/pipeline/decisions-log.md`. Compiled from hardening artifacts:
- `docs/pipeline/hardening-r*-journal.md`
- `docs/pipeline/hardening-r*-*-report.md`
- `docs/pipeline/hardening-r*-fixes.md`
- Git log for context

Distilled into useful decisions: what changed, why, what was tried, what worked. Not a raw dump of the journals — extract the "why" behind each significant change so future agents understand the reasoning.

### 2e. Knowledge graph

Run `/graphify` on the project source directory + docs. Output to `docs/delivery/knowledge-graph/`.

- If graphify is unavailable (not installed, errors out, etc.), log the failure in `docs/pipeline/final-verification.md` and continue. The knowledge graph is a nice-to-have, not a gate.
- Can run in parallel with Phase 3.
- If Phase 3 fixes code, re-run graphify after Phase 3 completes so the graph reflects the final state.

**Output:** Updated spec-final.md, project-memory.md, use-case docs, decisions-log.md, knowledge graph

Update status:
```markdown
- **Sub-step:** Phase 2 complete — AI docs updated
```

---

## 4. Phase 3 — Builder (Final Verification + Screenshots)

Dispatch a Builder agent (via Agent Teams) that walks through every user story and every edge case against the live app with Playwright MCP, and captures a screenshot for each step.

**App URL:** Same dev server from Step 5 (e.g., `http://localhost:5199`). Verify it's running before starting. If not, start with `npx vite --port 5199`.

### Dispatch pattern (MANDATORY — Agent Teams)

All agent dispatches in this phase go through Agent Teams. No bare `Agent()` calls.

```
TeamCreate({ team_name: "step6-delivery", description: "Step 6 final verification" })
TaskCreate({ subject: "Final verification build", description: "..." })
Agent({
  name: "final-builder",
  team_name: "step6-delivery",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..."   // Builder instructions below
})
```

See the "Model conventions" note at the end of this skill for which model to assign which role.

### Builder instructions

For each user story and edge case in spec-final.md:
1. Navigate to the required app state
2. Perform the user action
3. Capture a screenshot as evidence
4. Report PASS or FAIL with notes

**Screenshot location:** `tests/e2e/final/US-{section}.{story}-{NN}-{description}.png`

This is the canonical Step 6 screenshot directory. It is DIFFERENT from Step 4's `tests/e2e/exploration/` — that one holds build-time exploration artifacts, this one holds the final verified delivery set. Keep them separate.

**COMPLETENESS IS NON-NEGOTIABLE:**
- The Builder MUST capture a screenshot for every `[screenshot:]` tag in every use-case doc. The exact count is `grep -c '\[screenshot:' tests/e2e/use-cases/m*-use-case.md` summed across files.
- Time is NOT a factor. If APIs are slow, wait. If injection is needed, do it.
- Do NOT make judgment calls to skip items. Step 4's exploration phase may dedupe screenshots via DOM fingerprinting during the build — Step 6 does NOT. Every tag = one file.
- Step 4 exploration screenshots do NOT count as Step 6 delivery screenshots. Phase 3 is a fresh pass against the final app.
- If the agent cannot finish in one session, it must report exactly what's missing so a follow-up agent continues. Never silently stop.
- Missing screenshots = automatic Auditor FAIL.

**Required coverage checklist:**
- [ ] Every `[screenshot:]` tag from `m1-use-case.md` through `m6-use-case.md`
- [ ] All happy path steps for all user stories
- [ ] All edge cases (injection-based and UI-based)
- [ ] All NEW stories from the reconciliation report
- [ ] All accessibility stories (keyboard nav, focus management, ARIA)
- [ ] Before/after pairs for toggle features (3D, split view, layers, flows, overlays)
- [ ] Responsive viewport screenshots (mobile 320px, tablet 768px)
- [ ] Error states (error boundary, network failure, validation errors)

**If any story FAILS:**
- Builder fixes the code
- Re-runs the failing stories
- Max 3 fix-rerun cycles. If still failing, surface to user with option to skip or investigate.

**Output:** `tests/e2e/final/` (complete screenshot set) + `docs/pipeline/final-verification.md`

Update status:
```markdown
- **Sub-step:** Phase 3 complete — Builder verification
```

---

## 5. Phase 3b — Screenshot Describer

Before the Auditor reviews screenshots, dispatch a fast Haiku agent to read every PNG and produce a text manifest. This offloads expensive vision token costs from the Opus Auditor.

```
Agent({
  name: "final-screenshot-describer",
  team_name: "step6-delivery",
  model: "haiku",
  mode: "bypassPermissions",
  prompt: "..."   // Describer instructions below
})
```

### Describer instructions

Same pattern as Step 4's Screenshot Describer, adapted for Step 6:
- Screenshot directory: `tests/e2e/final/`
- Output manifest: `tests/e2e/final/screenshot-manifest.md`
- Read EVERY PNG, describe what you see in 2-3 sentences
- For toggle/mode features, describe the specific visual state and note whether before/after pairs look visually different
- Do NOT judge correctness — just describe

**After the Describer completes**, verify `tests/e2e/final/screenshot-manifest.md` exists before proceeding to the Auditor. If the manifest is missing or the Describer failed, re-dispatch before running the Auditor — the Auditor relies on this manifest.

---

## 6. Phase 4 — Auditor

Dispatch a fresh agent (never saw the Builder's work) that reviews the Builder's transcript and the screenshot manifest.

```
Agent({
  name: "final-auditor",
  team_name: "step6-delivery",
  mode: "bypassPermissions",
  prompt: "..."   // Auditor uses the default model (Opus) — see model conventions
})
```

### Auditor checks

1. **Transcript honesty** — did the Builder actually run the Playwright tools it claims?
2. **Screenshot completeness** — does every user story + edge case have a screenshot?
3. **Screenshot accuracy (VISUAL CONTENT VERIFICATION)** — the Auditor MUST read the screenshot manifest at `tests/e2e/final/screenshot-manifest.md` produced by the Haiku Describer in Phase 3b. Do NOT read PNG files directly — that burns vision tokens. For each manifest entry:
   - Verify the described visual content matches what the story describes
   - **Toggle/mode features (CRITICAL):** For any feature that toggles a mode (3D projection, split view, flow animation, layer on/off, overlay on/off), compare before and after entries. If they describe IDENTICAL content — same map, only a button label changed — that is a FAIL.
     - 3D projection: map must show tilted perspective with hubs at different heights (not flat)
     - Split view: TWO separate map containers must be visible side by side
     - Flow animation: animated lines/particles must be visible on map edges
     - Layer toggle off: markers/lines must be GONE from the map
     - Infrastructure/boundary overlays: lines/polygons must be VISIBLE on the map
   - If the Describer's text cannot prove the feature works, that is a FAIL
4. **Coverage** — is every story in spec-final.md accounted for?

### Scoring rubric

- **5** — every story tested with clear evidence, all visual diffs verified, all tools verified
- **4** — all stories covered, minor evidence gaps (1-2 manifest entries unclear)
- **3** — most stories covered (>90%), some evidence gaps but no fabrication
- **2** — significant coverage gaps or evidence of shortcuts (e.g., passing features that visually don't work)
- **1** — minimal testing, fabricated evidence, or most stories untested

**PASS >= 3.**

**If FAIL:**
- Re-dispatch Builder to address gaps identified by Auditor
- Re-run Auditor
- Max 2 retries, then surface to user

**Output:** `docs/pipeline/final-audit.md`

Update status:
```markdown
- **Sub-step:** Phase 4 complete — Auditor passed (score: {N})
```

---

## 7. Phase 5 — Human Documentation

Only runs after Auditor passes. Produces the User Journey Walkthrough HTML — the comprehensive doc that shows every user story and edge case with real screenshots.

### User Journey Walkthrough HTML

A comprehensive documentation of every milestone, every user story, every edge case — with detailed steps and real screenshots from the live app. This is the complete proof that every feature works, updated to reflect all Step 5 changes.

This is NOT a quick tour. It is a detailed reference document covering the entire app.

**CRITICAL: Use the deterministic generator script. Do NOT dispatch an LLM agent to build this HTML by hand.**

#### Why a script, not an agent

A previous implementation dispatched an LLM agent to read use-case docs, encode PNGs to base64, and write the HTML. It worked but was:
- **Non-deterministic** — different runs produced different structure, styling, missing/extra items
- **Expensive** — re-encoding 200+ screenshots through the LLM context burns tokens
- **Error-prone** — agent judgment calls produced incomplete sets (e.g., missed "Edge Cases" subsections)
- **Slow** — 15+ minutes of agent time per run

A Node.js script solves all of these. Deterministic, free, fast (seconds), correct every time.

#### The generator script

Location: `~/.claude/skills/pipeline-step6/generate-walkthrough.js`

What it does:
1. Parses `tests/e2e/use-cases/m*-use-case.md` for every `[screenshot: id]` tag and its description
2. Reads `docs/pipeline/spec-final.md` for story classifications (UNCHANGED/MODIFIED/NEW)
3. Base64-encodes every PNG in `docs/delivery/screenshots/` referenced by a tag
4. Generates a single self-contained HTML file with:
   - Sticky TOC sidebar with anchor links per milestone and per story
   - One chapter per milestone with a colored accent
   - Story sections with status badges
   - Numbered steps showing description + embedded screenshot
   - Edge case sub-sections (parses `### US-X.X Edge Cases` format)
   - Accessibility sections (parses `### Accessibility (US-A11Y)` format)
   - Pipeline artifact neutral style (DM Sans + Space Grotesk, `#faf9f6` bg, earthy colors)
   - Responsive layout (mobile: TOC becomes top nav)

Output: `docs/delivery/user-journey-walkthrough.html`

#### Running it

Before running: copy (or symlink) the verified screenshots from `tests/e2e/final/` into `docs/delivery/screenshots/`. The script reads from the delivery path so the output HTML is self-contained with the rest of the delivery package.

```bash
cp tests/e2e/final/*.png docs/delivery/screenshots/
node ~/.claude/skills/pipeline-step6/generate-walkthrough.js /path/to/project
```

The script prints a summary:
```
✓ Generated ...user-journey-walkthrough.html
  Milestones: 6
  Stories: 55
  Steps: 211
  Missing screenshots: 0
  File size: 57.96 MB
```

**Exit code 0** = all screenshots present and embedded.
**Exit code 2** = some screenshots missing (still writes HTML with placeholders). Do not ship if exit code is 2 — go back to Phase 3.

#### If the use-case format changes

The script parses these section header formats:
- `### US-X.X — Title` (primary story, em-dash or dash)
- `### US-X.X Edge Cases` (edge cases for a story)
- `### Accessibility (US-A11Y)` (parenthesized ID)
- `### Bare Section Name` (synthesized id)

And these line formats for steps:
- `N. [screenshot: id] description` (numbered journey steps)
- `- [screenshot: id] description` (bullet edge cases)

It also reads the French "plan de cas d'usage" format of the web app pipeline (flux `webapp`): `# Jalon N — Titre`, `**Démonstration** : …` (intro), `## US-X.X — Titre` / `## V-X.X — Titre`, steps `N. texte — capture \`nom.png\``, transverse bullets `- **US-A11Y-001 — Titre** : 1. … — capture \`a.png\` ; 2. …`, and free `## Section` headings whose numbered steps become a story with a synthesized id. Optional inputs: `docs/delivery/screenshots-notes.json` (`{capture: note}` shown under the image, e.g. provenance; a capture absent from disk but present here is rendered as a justified non-replay and does not count as missing — use it only for absences the Auditor accepted) and `docs/delivery/walkthrough-intro.html` (fragment under the title). Labels follow `language` in `docs/pipeline/config.json`; the app name comes from `appName` there, else `<title>` of `index.html`.

If a project uses a different format, **update the script**, don't bypass it. The script is the single source of truth for walkthrough generation.

### Deploy

If code was fixed during Phase 3, run a final deploy to ensure the deployed version matches verified code.

**Before pushing, run `npm run build` (not `vite build`).** Vercel runs `tsc -b && vite build` which does strict TypeScript checking. Local `npx vite build` alone skips type checking and WILL let TypeScript errors through that then fail on Vercel. Always verify with the real build command before pushing.

Deploy paths:
- If `deployment` in config → push to git remote, Vercel auto-deploys via webhook
- If `gitRemoteUrl` only → git push
- If local only → skip

**After deploy, verify it's live:**
1. Use `vercel ls` to find the latest deployment
2. Check status — if `● Error`, run `vercel inspect <url> --logs` and fix the errors
3. Unique per-deploy URLs (e.g. `<project>-<hash>-<team>.vercel.app`) are behind Vercel Deployment Protection and return HTTP 401. The PUBLIC URL is the main production alias (e.g. `<project>.vercel.app`). Test with `curl -I https://<project>.vercel.app` — should return HTTP 200.

Update status:
```markdown
- **Sub-step:** Phase 5 complete — documentation built
```

---

## 8. Phase 6 — Handoff

Present the delivery package to the user:

**For humans:**
- User Journey Walkthrough HTML (`docs/delivery/user-journey-walkthrough.html`)

**For AI:**
- `docs/pipeline/spec-final.md` (ground truth)
- `docs/pipeline/project-memory.md` (project summary)
- `docs/pipeline/decisions-log.md` (why things were built this way)
- `docs/delivery/knowledge-graph/` (if graphify ran successfully)
- Updated use-case docs (`tests/e2e/use-cases/m*-use-case.md`)

**For verification:**
- All E2E tests passing
- Complete screenshot set in `tests/e2e/final/`
- `docs/pipeline/final-verification.md` + `docs/pipeline/final-audit.md`

---

## 9. Write Final State

### `docs/pipeline/status.md`
```markdown
# Pipeline Status

- **Current step:** 6
- **Sub-step:** complete
- **Last updated:** {date}
- **Summary:** Story reconciliation & delivery complete. {X} unchanged, {Y} modified, {Z} new, {W} removed stories. All verified. Delivery package ready.
```

### `docs/pipeline/project-memory.md`
Rewrite with final delivered state (max 2000 chars).

---

## 10. Announce Completion

Post: `✅ Step 6 done — {X} unchanged, {Y} modified, {Z} new, {W} removed stories. All verified. Delivery package ready.`

NOTE: The `✅ Step 6 done` prefix (with the checkmark emoji) is NOT a style choice — it is a detection trigger. Pipeline-System (`bot.js`) greps for this exact string to auto-post the step-advance menu. Do not change the wording or drop the emoji or the automation breaks.

Offer: `Run /pipeline-step1 to start a new iteration.`

---

## Model conventions (Step 6)

| Role | Model | Why |
|---|---|---|
| Builder (Phase 3) | `sonnet` | Cheap and fast enough for driving Playwright through 200+ steps |
| Screenshot Describer (Phase 3b) | `haiku` | Vision description is a rote task; cheapest model is plenty |
| Auditor (Phase 4) | default (Opus) | Judgment + harsh critique benefits from the strongest model |

If you need to override these, say so explicitly — do not change them silently.

---

## Process Flow

```
Phase 1: Reconciliation (compare planned vs built)
    ↓
Phase 2: Update AI Docs + Graphify
    ↓
Phase 3: Builder — Sonnet (test + screenshots + fix loop, max 3) ←──┐
    ↓                                                                 │
Phase 3b: Screenshot Describer — Haiku (manifest)                    │
    ↓                                                                 │
Phase 4: Auditor — default model (verify via manifest, max 2 retries)│
    ↓ PASS                                FAIL ──────────────────────┘
Phase 5: Human Documentation (script) + Deploy
    ↓
Phase 6: Handoff
```
