---
name: pipeline-step5
description: Quality Hardening — 4 parallel deep audits (performance, stability, accessibility, security), fix, regress, loop until user ships. After Step 4.
---

# Pipeline Step 5 — Quality Hardening

Run four deep parallel audits (Performance, Stability, Accessibility, Security), evaluate each for honesty, compile findings, fix issues by priority, run regression, and loop until the user says ship.

---

## 1. Gate Check

Read `docs/pipeline/status.md` in the current project directory.

- **File does not exist or Step < 4 complete:** Abort. Tell the user: "Step 4 must be complete before hardening. Run `/pipeline-step4` first."
- **Step 4 complete (all milestones built):** Proceed.
- **Step 5 already in progress:** Resume from the current sub-step / iteration.
- **Step 5 already complete:** Warn the user and offer `/pipeline-step6`.

---

## 2. Setup

### 2.0 Audit Target — PRODUCTION ONLY (mandatory)

**Hardening audits MUST run against the deployed production site, NOT a local dev server.**

Dev server hides real-world issues:
- No minification → bundle size lies
- No CDN, no compression → transfer size and TTFB lie
- No production env vars → some code paths don't execute
- No real CSP / security headers → security audit misses misconfigs
- HMR / source maps present → security audit can leak warnings about dev-only artifacts
- Localhost network is instant → CWV metrics are useless
- React dev mode adds extra checks/warnings → perf and stability profiles differ

**Pre-flight checklist (do BEFORE creating the team):**

1. **Find the real production URL — never guess.** Run:
   ```bash
   vercel ls 2>&1 | head -5             # find the latest Ready deployment
   vercel alias ls 2>&1 | head -10      # find the public alias(es)
   ```
   Pick the cleanest public alias (e.g. `<project>-<word>.vercel.app`). Save it as `PROD_URL`.
   Do NOT use a per-deployment URL like `<project>-<hash>-<team>.vercel.app` — those are behind Deployment Protection and return HTTP 401.
   Do NOT guess a "natural" alias like `<project>.vercel.app` without verifying — short subdomains are first-come-first-served across all Vercel users globally and may belong to a third party.

2. **Confirm the URL serves THIS project.** Verify the page title matches:
   ```bash
   curl -s "$PROD_URL" | grep -o '<title>[^<]*</title>'
   ```
   If the title is unfamiliar (e.g. "React App", a different brand, foreign content): the alias was claimed by someone else. Use the team-scoped alias instead (e.g. `<project>-<team>.vercel.app`).

3. **Confirm the production deploy is current.** Compare local HEAD against deployed commit:
   ```bash
   git log -1 --format="%H"             # local HEAD
   vercel inspect "$PROD_URL" 2>&1 | grep -i 'commit\|branch\|created'
   ```
   If stale: `git push` and wait for Vercel to redeploy. Check `vercel ls` until status is `● Ready`.

4. **Confirm HTTP 200**: `curl -I -s "$PROD_URL" | head -1`. Anything else → fix before auditing.

5. **Save `PROD_URL` for use in every auditor prompt.** Every auditor that hits the live app uses `PROD_URL`, not localhost.

### 2.1 Team setup

1. **Create team**: `TeamCreate({ team_name: "hardening-r{N}", description: "Quality Hardening — Round {N}" })`
   - `{N}` is the current iteration number (1 for first run, incremented on each loop)
2. **Create journal**: Write `docs/pipeline/hardening-r{N}-journal.md` with the Timeline header. First entry must record the verified `PROD_URL` and the commit SHA being audited.
3. **Create tasks** — 8 tasks total, 4 auditor + 4 evaluator (evaluators blocked by their auditor):
   - Task 1: "Performance Auditor" (no deps)
   - Task 2: "Stability Auditor" (no deps)
   - Task 3: "Accessibility Auditor" (no deps)
   - Task 4: "Security Auditor" (no deps)
   - Task 5: "Performance Evaluator" (blockedBy: Task 1)
   - Task 6: "Stability Evaluator" (blockedBy: Task 2)
   - Task 7: "Accessibility Evaluator" (blockedBy: Task 3)
   - Task 8: "Security Evaluator" (blockedBy: Task 4)

### Team Lead Rules

**The team lead NEVER writes code or fixes bugs during the audit phase.** The team lead only:
- Sets up the team, tasks, journal
- Dispatches auditors in parallel (all 4 at once)
- Dispatches evaluators as their auditors complete
- Compiles the consolidated report
- Implements fixes (or dispatches a Builder for fixes)
- Runs regression tests
- Presents results to the user

---

## 3. Phase 1 — FOUR AUDITORS (serialized browser access)

Dispatch the four auditors as team teammates. Each runs independently with full access to the codebase and live app, **but only ONE browser-using auditor can run at a time.**

### Dispatch order (REQUIRED)

Playwright MCP holds a single Chromium instance per project. If 3 browser-using auditors (Perf, Stability, A11y) all dispatch in parallel, they fight for the browser lock — two of them will silently fail Playwright calls and fall back to source-only audits (this has historically led to fabricated methodology claims, where an auditor's report states "browser_navigate, browser_evaluate..." but the transcript shows zero browser calls). Serialize them:

1. **Wave 1 (parallel):** Security auditor (no browser) + Performance auditor (browser)
2. **Wave 2 (after wave 1's browser auditor reports):** Stability auditor (browser)
3. **Wave 3 (after wave 2):** Accessibility auditor (browser)

Security can always run in parallel — it uses `npm audit` + `curl` + greps, not Playwright.

### Browser-use contract (REQUIRED for any auditor that claims Playwright in its report)

Every browser-using auditor MUST:
- As its very first action, call `browser_navigate({PROD_URL})` and include the response page title in its report header on a line `Session proof: navigated to {PROD_URL}, page title "{title}"`.
- Tally its browser tool calls at the end of the audit and include a `Tool usage: {N} browser_navigate, {M} browser_evaluate, {K} browser_take_screenshot` summary.
- If browser access is unavailable (lock contention, MCP offline), STOP and declare source-only fallback explicitly at the TOP of the report: `## Fallback: source-only audit — browser unavailable because ...`. Do NOT retain the Playwright methodology sentence in that case. Evaluator R2 auto-FAILs any audit whose header claims Playwright methodology but transcript shows zero browser calls.

**MANDATORY: ALL agent dispatches MUST use Agent Teams.** Never use bare `Agent()` calls.

### 3.1 Performance Auditor

```
Agent({
  name: "perf-auditor",
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..." // Performance auditor instructions below
})
```

**Primary method: BUILD TOOLS + PLAYWRIGHT MEASUREMENT + code for diagnosis only.**
The Performance Auditor measures real metrics first, then reads code only to explain
bottlenecks it found through measurement. It does NOT review code speculatively.

**Performance Auditor instructions:**

```
You are the Performance Auditor on team hardening-r{N}. Your task is Task #1.

Conduct a DEEP performance audit by MEASURING the app, not guessing from code.

App URL: {PROD_URL — verified production deploy, NOT a dev server}
Source code: {project source directory}
Spec: {path to spec.md}

## Your Method: MEASURE FIRST, DIAGNOSE SECOND

1. Run build tools and collect hard numbers
2. Run the app in Playwright and measure real metrics
3. ONLY THEN read source code to explain WHY a measured metric is bad

Do NOT grep source code looking for performance issues speculatively.
Every finding must start with a measurement, not a code review.

## Audit Areas (ALL mandatory)

### A. Bundle Analysis (build tools)
1. Run `npx vite build` and record output (chunk sizes, total bundle size)
2. Identify the largest chunks — what's in them?
3. Check for tree-shaking issues, duplicate dependencies
4. Report: total bundle size, largest chunks with sizes, unnecessary bloat

### B. Core Web Vitals (Playwright measurement)
1. Open the app in Playwright at each major screen
2. Measure using Performance API via browser_evaluate:
   - `performance.getEntriesByType('navigation')` → TTFB, domContentLoaded
   - `performance.getEntriesByType('paint')` → FCP
   - `new PerformanceObserver` for LCP, CLS
   - Long task detection for TBT
3. Report: metrics per screen, which screens are slow

### C. Runtime Profiling (Playwright stress test)
1. Navigate to the heaviest screen (full data loaded)
2. Measure FPS during interaction:
   ```js
   let frames = 0; const counter = () => { frames++; requestAnimationFrame(counter); };
   requestAnimationFrame(counter); // ... wait 5 seconds ... report frames/5
   ```
3. Measure memory: `performance.memory` or `performance.measureUserAgentSpecificMemory()`
4. Stress conditions: enable all features simultaneously, measure FPS + memory
5. Report: FPS under each condition, memory at each state

### D. Network Efficiency (Playwright interception)
1. Intercept all requests via page.route('**/*') during full user journey
2. Log: URL, size, timing, cache headers
3. Flag: duplicates, large payloads, sequential waterfalls, missing cache
4. Report: request count, total transfer, issues found

### E. Memory Leaks (Playwright endurance)
1. Navigate full journey 3 times without page refresh
2. Measure heap at each navigation point
3. Flag: growing heap, heap that doesn't shrink on navigation back
4. Report: heap growth pattern per cycle

### F. Diagnose (code reading — ONLY for measured bottlenecks)
For each CRITICAL or HIGH metric found above:
1. Read the relevant source file to understand why
2. Identify the root cause (e.g., "37K Polyline components because InfrastructureLayer
   maps every segment to a separate React component instead of using a single GeoJSON layer")
3. Suggest a specific fix with the right approach/library

## Output Format

Write your report to: docs/pipeline/hardening-r{N}-perf-report.md

Structure:
# Performance Audit Report — Round {N}

## Executive Summary
- Overall score: {A/B/C/D/F}
- Critical issues: {count}
- High issues: {count}
- Medium issues: {count}
- Low issues: {count}

## Measurements
{All raw numbers: bundle sizes, FPS, memory, CWV metrics, network stats}

## Issue List
| # | Severity | Metric | Measured Value | Target | File/Root Cause | Suggested Fix |
|---|----------|--------|---------------|--------|-----------------|---------------|

Severity: CRITICAL (app unusable), HIGH (major degradation), MEDIUM (noticeable), LOW (minor)

## Evidence
{Screenshots of slow screens, console output of measurements}

When complete:
1. Append a summary to docs/pipeline/hardening-r{N}-journal.md
2. Mark your task as completed via TaskUpdate
3. Send your report summary to the team lead
```

### 3.2 Stability Auditor

```
Agent({
  name: "stability-auditor",
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..." // Stability auditor instructions below
})
```

**Primary method: PLAYWRIGHT STRESS TESTING + code for root cause diagnosis.**
The Stability Auditor's job is to BREAK the app — crash it, hang it, corrupt its state.
It does this by running the app and attacking it, not by reading code speculatively.
Code is read only to diagnose crashes it actually triggered.

**Stability Auditor instructions:**

```
You are the Stability Auditor on team hardening-r{N}. Your task is Task #2.

Your job is to BREAK the app. Find every way it can crash, hang, or produce wrong results.
You do this by RUNNING the app and attacking it with Playwright.

App URL: {PROD_URL — verified production deploy, NOT a dev server}
Source code: {project source directory}
Spec: {path to spec.md}

## Your Method: BREAK FIRST, DIAGNOSE SECOND

1. Run the app in Playwright and try to crash/hang/corrupt it
2. For each crash or bug found, read the source code to find the root cause
3. Do NOT read code looking for theoretical issues — every finding must be reproducible

## Audit Areas (ALL mandatory)

### A. Network Failure Injection (Playwright page.route)
For EVERY external API call the app makes, inject failures:
1. Intercept with page.route() and return: 500, 429, timeout (30s delay), malformed JSON, empty response
2. **Verify the mock took effect BEFORE filing the finding.** After setting up `page.route()`, call the intercepted endpoint via `browser_evaluate(() => fetch('/api/...'))` and confirm the mocked value comes back. If the real server response still comes through (e.g., the app uses WebSockets or Supabase's own transport that bypasses fetch interception), the mock did not catch — discard or restate the finding with the correct diagnosis. Do NOT file a crash finding on a symptom you observed with a failed mock.
3. For EACH injection, record:
   - Does the app crash (white screen)? → CRITICAL
   - Does it show an error with retry option? → OK
   - Does the rest of the app still work after the error? → test by navigating
4. Take a screenshot of each crash/error state
5. THEN read the code to find the missing error handling

### B. Rapid Interaction Stress (Playwright clicks/keys)
1. Double-click every confirm button
2. Toggle every toggle 10+ times in 1 second
3. Open/close every panel/modal rapidly
4. Start a long operation → immediately trigger another
5. Resize viewport during animations/transitions
6. For each: check if the app crashes, hangs, or shows wrong state
7. Take screenshots of any broken state

### C. Navigation Abuse (Playwright)
1. Refresh page mid-operation (page.reload during pipeline)
2. Navigate back (page.goBack) from every screen
3. Go to deep URLs directly (skip the normal flow)
4. For each: does the app recover gracefully or crash?

### D. Data Edge Cases (Playwright page.route injection)
1. Inject minimal data: 1 item, 0 items, empty arrays
2. Inject maximal data: 10K items, deeply nested objects
3. Inject malformed data: NaN coordinates, missing required fields, null values
4. For each: does the app crash, show garbage, or handle it?
5. Take screenshots of every failure

### E. Viewport Stress (Playwright resize)
1. Resize to: 320px, 768px, 1920px, 3840px width
2. At each size, visit **every primary route** from the spec — for typical apps that means at least `/`, `/researchers` (or equivalent list), `/map`, `/stats`, `/themes`, `/admin`, `/login`. Do NOT stop at `/map` and call it a day; chart-heavy pages like `/stats` are a common blind spot for viewport regressions.
3. At each (breakpoint × page) pair, click through a short user journey and screenshot.
4. Flag as HIGH: overlapping elements, hidden controls, broken layouts, cut text, **chart tick labels overlapping or truncated to under 10 chars without a tooltip alternative** (e.g., 27 x-axis years rendered on top of each other, theme labels all showing `process...`).
5. Your report MUST include the screenshot + page name + breakpoint for every finding. "Flag: `/stats` line chart at 1280px — all 27 year labels overlap into an unreadable band" is a valid HIGH finding that historically none of the 4 auditors caught.

### F. Endurance (Playwright multi-session)
1. Run the full user journey 3 times without page refresh
2. After each run, check: memory growth, stale data visible, degraded performance
3. Report: does the app degrade over repeated use?

### G. Root Cause Diagnosis (code reading — ONLY for bugs found above)
For each CRITICAL or HIGH crash/bug found:
1. Read the relevant source code
2. Identify: missing error boundary, uncleaned listener, race condition, etc.
3. Suggest the specific fix

## Output Format

Write your report to: docs/pipeline/hardening-r{N}-stability-report.md

# Stability Audit Report — Round {N}

## Executive Summary
- Overall score: {A/B/C/D/F}
- Crashes found: {count}
- Hangs found: {count}
- State corruption found: {count}

## Crash Log
| # | Severity | Trigger | What Happened | Screenshot | Root Cause (file:line) | Fix |
|---|----------|---------|---------------|------------|----------------------|-----|

## Evidence
{Screenshots of every crash, hang, and corrupted state}

When complete:
1. Append a summary to docs/pipeline/hardening-r{N}-journal.md
2. Mark your task as completed via TaskUpdate
3. Send your report summary to the team lead
```

### 3.3 Accessibility Auditor

```
Agent({
  name: "a11y-auditor",
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..." // Accessibility auditor instructions below
})
```

**Primary method: PLAYWRIGHT (live app interaction as a user would experience it).**
Accessibility is about what the USER experiences, not what the code looks like.
This auditor lives in the browser — tabbing, injecting axe-core, checking focus,
measuring contrast. It reads source code only to verify ARIA attributes exist.

**Accessibility Auditor instructions:**

```
You are the Accessibility Auditor on team hardening-r{N}. Your task is Task #3.

Conduct a DEEP accessibility audit targeting WCAG 2.1 AA compliance.
You do this by USING the app the way a disabled user would — keyboard only,
screen reader simulation, contrast checking — all via Playwright.

App URL: {PROD_URL — verified production deploy, NOT a dev server}
Source code: {project source directory}
Spec: {path to spec.md}

## Your Method: USE THE APP, DON'T JUST READ CODE

1. Open the app in Playwright and interact with it using keyboard/accessibility tools
2. Inject axe-core and measure real violations
3. Read source code ONLY to check ARIA attributes or verify a finding

## Audit Areas (ALL mandatory)

### A. Automated Scan — axe-core (Playwright)
1. Inject axe-core into the page via browser_evaluate
2. Run `axe.run()` on EVERY major screen
3. Collect ALL violations — don't stop at the first screen
4. Take a screenshot of each screen before running axe
5. Report: violations per screen, grouped by WCAG criterion

### B. Keyboard Navigation (Playwright keyboard)
1. Start from page load. Navigate the ENTIRE app using ONLY:
   - page.keyboard.press('Tab') to move forward
   - page.keyboard.press('Shift+Tab') to move backward
   - page.keyboard.press('Enter') and page.keyboard.press('Space') to activate
   - page.keyboard.press('Escape') to dismiss
   - Arrow keys for lists, sliders, tabs
2. At each focusable element, take a screenshot showing the focus indicator
3. For each component, record:
   - Can it receive focus? Does Tab reach it?
   - Is the focus ring VISIBLE in the screenshot?
   - Can it be activated with Enter/Space?
   - Can modals/panels be dismissed with Escape?
   - Is tab order logical (not jumping around)?
4. Test focus trapping in modals — Tab should cycle within, not escape
5. Report: per-component results with screenshot evidence

### C. Screen Reader Simulation (Playwright DOM inspection)
1. Use browser_snapshot to read the accessibility tree
2. For every interactive element, check: does it have a role + accessible name?
3. Check landmarks: main, nav, complementary regions with names
4. Check heading hierarchy: h1 → h2 → h3, no skips
5. Check dynamic content: are loading states, errors, completions announced via aria-live?
6. For elements that fail: read the source to confirm the ARIA attribute is missing (not just rendering issue)
7. Report: missing roles, names, landmarks, announcements

### D. Color & Contrast (Playwright measurement)
1. For key text elements on each screen, use browser_evaluate to extract:
   - Computed color: `getComputedStyle(el).color`
   - Computed background: `getComputedStyle(el).backgroundColor`
   - Font size: `getComputedStyle(el).fontSize`
2. Calculate contrast ratio (WCAG AA: 4.5:1 normal, 3:1 large text 18px+)
3. Check color-only information: does any feature rely ONLY on color with no
   shape/label/pattern alternative? (e.g., hub tiers, flow volume, error states)
4. Take screenshots showing low-contrast elements
5. Report: contrast failures with specific ratios and element selectors

### E. Motion & Preferences (Playwright emulation)
1. Enable reduced motion: `page.emulateMedia({ reducedMotion: 'reduce' })`
2. Navigate the full app — are animations disabled/simplified?
3. Zoom to 200% — does the layout break?
4. Take screenshots at 200% zoom of every major screen
5. Report: motion respect status, zoom breakage

## Output Format

Write your report to: docs/pipeline/hardening-r{N}-a11y-report.md

# Accessibility Audit Report — Round {N}

## Executive Summary
- Overall WCAG AA compliance: {percentage estimate}
- Critical issues: {count} (app unusable for some users)
- High issues: {count} (WCAG AA failure)
- Medium issues: {count} (minor a11y gap)
- Low issues: {count} (best practice)

## Issue List
| # | Severity | WCAG Criterion | Issue | Element/Selector | Screenshot | Fix |
|---|----------|---------------|-------|-----------------|------------|-----|

## Evidence
{Screenshots: focus indicators, axe-core results, contrast failures, zoom breakage}

When complete:
1. Append a summary to docs/pipeline/hardening-r{N}-journal.md
2. Mark your task as completed via TaskUpdate
3. Send your report summary to the team lead
```

### 3.4 Security Auditor

```
Agent({
  name: "security-auditor",
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..." // Security auditor instructions below
})
```

**Primary method: CODE ANALYSIS + BUILD TOOLS. No browser needed.**
Security vulnerabilities live in the code — XSS sinks, hardcoded secrets, missing
sanitization, dependency CVEs, insecure configs. This auditor reads source files,
runs `npm audit`, and greps for patterns. It never opens a browser.

**Security Auditor instructions:**

```
You are the Security Auditor on team hardening-r{N}. Your task is Task #4.

Conduct a DEEP security audit by analyzing SOURCE CODE and BUILD CONFIGURATION.
You do NOT open a browser. Vulnerabilities are in the code, not the UI.

Source code: {project source directory}
Spec: {path to spec.md}

## Your Method: READ CODE, RUN TOOLS

1. Run dependency audit tools (npm audit)
2. Grep source code for vulnerability patterns
3. Read config files for misconfigurations
4. Do NOT use Playwright — security audit is code-only

## Audit Areas (ALL mandatory)

### A. Dependency Audit (npm audit + package analysis)
1. Run `npm audit` — record all vulnerabilities by severity
2. Read `package.json`: unnecessary dependencies? Unpinned versions?
3. Check for supply chain risk: low-download deps, unmaintained packages
4. Report: vulnerability count, risky dependencies with reasoning

### B. XSS & Injection (grep + code reading)
1. Grep for `dangerouslySetInnerHTML` — every instance is a potential XSS
2. Grep for `innerHTML`, `document.write`, `eval(`, `new Function(`
3. Find all user input points (search bars, form fields) — trace the data flow:
   where does the input go? Is it sanitized before rendering?
4. Find all external API data rendered in the UI — is it escaped?
5. Check URL parameter handling — are fragments/params used unsafely?
6. Report: each injection vector with file:line, whether it's protected, and how

### C. Secrets & Data Exposure (grep + file reading)
1. Grep for patterns: API keys, tokens, passwords, secrets in source files
   - Patterns: `/[A-Za-z0-9]{32,}/, /sk-/, /token/, /password/, /secret/`
2. Check `.env` files — are they gitignored? Referenced in client code?
3. Read all files that touch localStorage/sessionStorage/cookies — what data is stored?
4. Check `VITE_` prefixed env vars — these are exposed to the client
5. Report: every exposed secret or data leak with exact file:line

### D. Configuration Security (file reading)
1. Read Vite config: source maps in production? Dev code leaking?
2. Read deployment config (vercel.json, etc.): security headers? Open redirects?
3. Check for CSP configuration — where is it set? What does it allow?
4. Check for: `unsafe-inline`, `unsafe-eval`, wildcard origins, missing headers
5. Report: config issues with file:line and what should change

### E. External API Security (code reading)
1. Read every file that makes HTTP requests (fetch, axios, etc.)
2. For each API call: what data is sent? Are credentials exposed in URLs?
3. Check rate limiting implementation — is there retry logic that could storm?
4. Check error handling — do error messages leak stack traces or file paths?
5. Check CORS configuration
6. Report: per-API security posture

### F. Build Output (build tools)
1. Run `npx vite build` and inspect the output
2. Check: source maps generated? Console.log in production bundles?
3. Grep built output for leaked secrets (same patterns as section C)
4. Report: build security findings

## Output Format

Write your report to: docs/pipeline/hardening-r{N}-security-report.md

# Security Audit Report — Round {N}

## Executive Summary
- Overall risk: {LOW/MEDIUM/HIGH/CRITICAL}
- Vulnerabilities found: {count by severity}
- Dependencies with CVEs: {count}

## Issue List
| # | Severity | OWASP Category | Issue | File:Line | Evidence | Fix |
|---|----------|---------------|-------|-----------|----------|-----|

## Evidence
{Exact code snippets, grep output, npm audit output}

When complete:
1. Append a summary to docs/pipeline/hardening-r{N}-journal.md
2. Mark your task as completed via TaskUpdate
3. Send your report summary to the team lead
```

---

## 4. Phase 2 — EVALUATORS (one per auditor)

As each auditor completes, dispatch its evaluator. Evaluators run the same honesty check as Step 4:

- Read the auditor's transcript JSONL
- Check for rubber-stamping (did it actually run the tools it claims?)
- Check for fabricated findings (did it grep/read files it references?)
- Check for lazy coverage (did it audit ALL areas, or skip some?)
- Score 1-5, PASS >= 3

### Dispatch pattern

Use Agent Teams — same team `hardening-r{N}` from Phase 1. Evaluators are Tasks 5-8 (see Setup section):
- Performance Evaluator → Task 5 → reads perf-auditor transcript
- Stability Evaluator → Task 6 → reads stability-auditor transcript
- Accessibility Evaluator → Task 7 → reads a11y-auditor transcript
- Security Evaluator → Task 8 → reads security-auditor transcript

```
Agent({
  name: "perf-evaluator",            // or stability-, a11y-, security-
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..."   // Evaluator instructions below
})
```

### Locating the auditor transcript

Agent transcripts live at `~/.claude/projects/{project-slug}/{session-id}.jsonl`. The team lead already knows which auditor agent produced which transcript — pass the exact file path in the evaluator's prompt.

If you don't have the path, it can be found by:
1. Looking up the auditor's session ID via the team config at `~/.claude/teams/hardening-r{N}/`
2. Listing `~/.claude/projects/*/` for the most recent file matching that session ID

Step 4 Phase 1.5 has the same pattern — reuse that code if needed.

### Evaluator prompt template (adapt per domain)

Replace `{Domain}`, `{M}` (5, 6, 7, or 8), and `{transcript-path}` before dispatching.

```
You are the {Domain} Evaluator on team hardening-r{N}. Your task is Task #{M}.

Read the {Domain} Auditor's transcript and verify it did thorough, honest work.

Transcript path: {transcript-path}

## What to Check

1. TOOL USAGE: Did it actually run the tools it claims?
   - Performance: Did it run `vite build`, measure FPS, check memory?
   - Stability: Did it use page.route() to inject failures? How many?
   - Accessibility: Did it inject axe-core and run it? On how many screens?
   - Security: Did it run `npm audit`? Did it grep for secrets?

2. COVERAGE: Did it check ALL audit areas listed in its instructions?
   Count the areas covered vs total areas required.

3. FABRICATION: Do the findings reference real files/lines?
   Cross-reference a sample of findings against the actual codebase.

4. DEPTH: Are findings specific (file path + line number + exact issue)?
   Or generic ("some components lack error handling")?

## Verdict

**Fabrication gate (applied BEFORE scoring):** If the Auditor's stated methodology is materially false — e.g., report claims Playwright MCP calls but the transcript has zero `browser_navigate`/`browser_evaluate`/`browser_snapshot`; claims `axe-core` injection that never happened; claims live PROD audit but ran only against a dev server; claims measurements it never took — the verdict is **automatic FAIL** regardless of finding quality. Re-dispatch the Auditor with explicit instructions to either (a) actually run the missing tools, or (b) drop the false methodology line and declare source-only fallback. Do NOT score fabricated audits at 3/5 PASS even if the underlying findings turn out to be correct; dishonesty about method is its own failure mode because nothing downstream (fixes, regression, Step 6 docs) can trust the rest of the report.

Also auto-FAIL if:
- A browser-using audit has no `Session proof:` header (see Phase 1 browser-use contract).
- The `Tool usage:` tally claims Playwright calls that don't appear in the transcript.

If the Auditor passes the fabrication gate, score 1-5 (same scale as Step 4 Evaluator). PASS >= 3.

Write your evaluation to: docs/pipeline/hardening-r{N}-{domain}-eval.md
Append summary to: docs/pipeline/hardening-r{N}-journal.md

When complete:
1. Mark your task as completed via TaskUpdate
2. Send verdict + score to the team lead
```

**After all evaluators complete:**
- Any auditor that scored < 3 → re-dispatch that auditor. Max 2 retries.
- All auditors scored >= 3 → proceed to Phase 3.

---

## 5. Phase 3 — COMPILE & PRIORITIZE

Once all 4 auditors pass evaluation, the team lead compiles a unified report.

1. Read all four reports:
   - `docs/pipeline/hardening-r{N}-perf-report.md`
   - `docs/pipeline/hardening-r{N}-stability-report.md`
   - `docs/pipeline/hardening-r{N}-a11y-report.md`
   - `docs/pipeline/hardening-r{N}-security-report.md`

2. Merge all issue lists into one table, sorted by priority:
   - **CRITICAL** → fix immediately (app broken, security vulnerability, data loss)
   - **HIGH** → fix in this round (major degradation, WCAG AA failure, exposed data)
   - **MEDIUM** → fix if time permits (noticeable issues, minor a11y gaps)
   - **LOW** → skip (cosmetic, theoretical, nice-to-have)

3. Write consolidated report: `docs/pipeline/hardening-r{N}-consolidated.md`

4. Present summary to the user:
   > **Quality Hardening — Round {N} Results**
   > - Performance: {score} — {critical}/{high}/{medium}/{low} issues
   > - Stability: {score} — {critical}/{high}/{medium}/{low} issues
   > - Accessibility: {score} — {critical}/{high}/{medium}/{low} issues
   > - Security: {score} — {critical}/{high}/{medium}/{low} issues
   >
   > **{total critical + high} issues to fix this round.** {medium} medium issues deferred.

5. **Ask the user for report detail preference** before proceeding to fixes:
   > Would you like to see the **detailed report** before I start fixing? Options:
   > - **A) Detailed report** — Full breakdown of every issue by domain, with file paths, evidence, evaluator corrections, and priority ordering
   > - **B) Summary only** — The table above is enough, proceed to fixes
   >
   If the user picks **A**, present the detailed consolidated report organized by domain:
   - For each domain (Performance, Stability, Accessibility, Security):
     - Evaluator score and key corrections/notes
     - Every CRITICAL and HIGH issue with: description, exact file:line, root cause, suggested fix, and any evaluator caveats
     - MEDIUM issues listed briefly (one-liner each)
     - Notable LOW issues mentioned if interesting
   - Cross-domain patterns (e.g., "3 domains flagged the same useResearchers fetch")
   - Evaluator corrections applied (e.g., "A11y evaluator found btn-primary contrast was miscalculated — downgraded from Critical to verify-first")
   - After presenting, ask if they want to proceed to fixes or discuss specific findings
   
   If the user picks **B**, proceed directly to Phase 3b / Phase 4.

---

## 5b. Phase 3b — FULL E2E REGRESSION BASELINE

**After compiling the audit report and BEFORE fixing anything**, run the full E2E regression suite to establish a baseline.

This catches:
- Pre-existing failures unrelated to hardening
- Tests that were already broken before this round
- Missing test coverage (milestones without use-case docs or specs)

**Steps:**
1. Check that `tests/e2e/use-cases/m{N}-use-case.md` exists for EVERY milestone. If any are missing → create them first (dispatch a Builder to explore the app and write the use-case doc).
2. Run the full Playwright E2E suite: `cd {project source directory} && npx playwright test`
3. Record baseline results: which tests pass, which fail, which are missing.
4. Present baseline to user alongside the audit report:
   > **E2E Baseline (before fixes):** {X}/{Y} tests passing. {Z} milestones missing test coverage.
5. Any failures here are NOT caused by hardening fixes — they're pre-existing. Track them separately.

**This baseline is compared against the post-fix regression run in Phase 5 to ensure fixes don't introduce new failures.**

---

## 6. Phase 4 — FIX

Dispatch a Builder agent to fix all Critical and High issues:

```
Agent({
  name: "hardening-builder",
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..." // Include the consolidated issue list (Critical + High only)
})
```

**Builder instructions:**
- Fix issues in priority order (Critical first, then High)
- Each fix must be minimal — fix the issue, don't refactor
- After each fix, verify with the same method the auditor used to find it
- Log every fix: what was wrong, what file, what changed, how verified
- `npx vite build` must pass after all fixes

---

## 7. Phase 5 — REGRESSION

After the Builder completes fixes, dispatch a **Regression Tester** agent to run all tests. **The team lead NEVER runs tests directly** — the agent handles everything: unit tests, build, E2E, and fixing any failures.

Create a task for the regression tester, then dispatch:

```
Agent({
  name: "regression-tester",
  team_name: "hardening-r{N}",
  model: "sonnet",
  mode: "bypassPermissions",
  prompt: "..." // Regression tester instructions below
})
```

**Regression Tester instructions:**

The agent must run three layers of verification, in order:

### Layer 1: Unit Tests & Build
1. Run `npx vitest run` — all tests must pass
2. Run `npx vite build` — must complete with 0 errors, record chunk sizes
3. If unit tests fail due to intentionally changed behavior, update the test. If a real regression, fix the code.

### Layer 2: Run All E2E Tests

Run the full Playwright E2E test suite — these are the milestone exploration specs saved during Step 4 (`m1-explore.spec.ts` through `m6-explore.spec.ts`). They exercise every milestone's happy path and edge cases against the live app.

```bash
cd {project source directory} && npx playwright test
```

The project's `playwright.config.ts` already configures:
- `testDir: './tests/e2e'` — runs all milestone specs
- `testMatch: '**/*.spec.ts'` — matches all spec files
- `timeout: 180000` — 3 minutes per test (covers slow API calls)
- `reuseExistingServer: true` — uses the dev server started in Setup
- `screenshot: 'only-on-failure'` — captures evidence of failures
- `retries: 1` — one automatic retry for flaky tests

**This is the primary regression gate.** These specs were written and validated during Step 4. If they pass after hardening, the fixes didn't break existing functionality.

### Layer 3: Handle Failures & Re-run

If E2E tests fail:
- Read the failure output carefully
- **Real regression** (hardening fix broke working behavior): fix the code
- **Stale test expectation** (test expects old behavior intentionally changed by a fix): update the test, document why
- **Syntax/structural errors in test files**: fix the test file
- Re-run `npx playwright test` until all specs pass
- Keep all fixes minimal

### Regression Report

The agent writes a report to `docs/pipeline/hardening-r{N}-regression.md`:

```markdown
# Regression Test Report — Round {N}

## Summary
- Unit tests: {passed}/{total}
- Build: {status} ({main chunk size})
- E2E specs: {passed}/{total} ({test count} individual tests)
- Regressions found: {count}
- Test fixes needed: {count}

## E2E Test Results
| Spec | Tests | Passed | Failed | Notes |
|------|-------|--------|--------|-------|

## Failures & Fixes
{for each failure: test name, error, root cause, fix applied}
```

The agent marks its task complete and sends a summary to the team lead.

### Team Lead Action

After the regression tester reports back:
> Regression: {X} unit tests, {Y} E2E tests — all passing.
> {Z} regressions found and fixed. Build: {size} main chunk.

---

## 8. Phase 6 — USER DECISION

Present the round results to the user:

> **Round {N} Complete**
> - Fixed: {X} critical, {Y} high issues
> - Remaining: {Z} medium, {W} low issues
> - Regression: all tests passing
>
> **A)** Ship it — proceed to Step 6 (Story Reconciliation & Delivery)
> **B)** Another full round — re-run all 4 auditors to find new issues or verify fixes
> **C)** Fix medium issues too — dispatch Builder on remaining mediums, then re-run regression (no new audits)

- **A** → Write state, proceed to Step 6
- **B** → Increment `{N}` (round number), loop all the way back to **Section 3 (Phase 1 — Four Parallel Auditors)**. All 4 auditors + all 4 evaluators run again. Fresh team `hardening-r{N+1}`.
- **C** → Do NOT re-run auditors. Lower the fix threshold to include MEDIUM severity, dispatch the `hardening-builder` agent with the existing consolidated report, then jump directly to **Section 7 (Phase 5 — Regression)**. Loop back to this decision point when done.

---

## 9. State Updates

After each round:

**`docs/pipeline/status.md`**
```markdown
# Pipeline Status

- **Current step:** 5
- **Sub-step:** hardening round {N}
- **Last updated:** {date}
- **Summary:** Round {N} complete. {X} critical + {Y} high fixed. {Z} medium + {W} low remaining.
```

**`docs/pipeline/project-memory.md`** — Update rolling summary with hardening status.

---

## 10. Completion

When the user chooses to ship:

Update `docs/pipeline/status.md`:
```markdown
- **Current step:** 5
- **Sub-step:** complete
- **Summary:** Quality hardening complete after {N} rounds. {total} issues found, {fixed} fixed.
```

> Step 5 done — {N} hardening rounds, {fixed} issues fixed across performance, stability, accessibility, and security.
> Run `/pipeline-step6` when you're ready for story reconciliation.
