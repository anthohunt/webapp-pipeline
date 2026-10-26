---
name: pipeline-step4.1
description: Le bâtisseur (cycle par jalon de la web app en 3 étapes) — construit les histoires du jalon, déploie une préversion, explore l'app dans un vrai navigateur (bibliothèque Playwright) et rapporte ce qu'il a VU. Sous-skill de pipeline-step4 ; sert aussi au mode retours (4.3).
---

# Pipeline Step 4.1 — Builder + Explore

**Called by:** the chef (pipeline-step4), cycle K of milestone N — or the retours mode (4.3).
**Input:** Milestone number, use case plan, spec, parcours, existing code; at cycle K > 1, the
verifier's list of gaps (verbatim).
**Output:** Built features, a deployed PREVIEW, exploration screenshots and log, test snippets.

---

## Chef Instructions

Dispatch ONE fresh Builder with the Task (Agent) tool. The chef NEVER writes code.

```
Task({ description: "m{N} bâtisseur cycle {K}", subagent_type: "general-purpose",
       prompt: "..." })   // the Builder Prompt Template below, every {placeholder} filled
```

**Before dispatching:**
1. Dev server running on port 5199 (or start it).
2. `tests/e2e/use-cases/m{N}-use-case.md` exists; read it to count the required screenshots.
3. At cycle K > 1: paste the previous verifier's gap list, verbatim, under `## Gaps to fix`.

**After the Builder returns:**
1. Append its summary to `docs/pipeline/m{N}-journal.md` under `## Bâtisseur — cycle {K}`
   (with the preview URL it deployed).
2. Load `pipeline-step4.2` and dispatch a fresh verifier on that preview.

---

## Builder Prompt Template

Fill in all `{placeholders}` before dispatching.

```
You are the Builder of milestone {N}, cycle {K}. You run alone on a server: nobody answers
questions — decide, and write down why. Report briefly, result first.
When you encounter ANY issue, error, or uncertainty — search online FIRST (WebSearch/WebFetch). Before guessing, before trying random fixes, before claiming something is impossible.
Heavy CPU work (build, full Playwright suite) is prefixed with `$WEBAPP_LIMITEUR` when it is set (the machine's CPU limiter).

## Your Mission

Build all features for Milestone {N} and explore the running app to capture screenshots proving every user story works.

## Context

- **Primary test target:** the PREVIEW you deploy at the end of Phase A (Vercel: `npx vercel deploy --yes --token "$VERCEL_TOKEN"` without `--prod`; other targets: the staging described in `docs/pipeline/config.json` → `deployment`). Write its URL to `{project-dir}/docs/pipeline/m{N}-preview-url.txt`. Localhost is a convenience for iteration but the acceptance evidence (screenshots, edge-case verification) MUST come from the deployed preview hitting the real Supabase project. Production is deployed later, by the chef, after the verifier's PASS.
- Parcours: {project-dir}/docs/pipeline/parcours-utilisateur.json — the steps whose screen belongs to this milestone are the user's real journey; build them so they can be walked end to end.
- Mockup (canonical look and behaviour): {project-dir}/docs/pipeline/design/ (`screens.json`, `mockup-url.txt`)
- Stories of this milestone: {story ids from roadmap-approved.json}
{at cycle K > 1:}
## Gaps to fix
{the verifier's gap list, verbatim — fix every one, then re-explore the affected steps}
- Local dev URL (iteration only): http://localhost:5199
- Project directory: {project-dir}
- Spec: {project-dir}/docs/pipeline/spec.md
- Use case plan: {project-dir}/tests/e2e/use-cases/m{N}-use-case.md
- Rules: {project-dir}/docs/pipeline/rules.md
- Existing source: {project-dir}/src/
- Previous milestone code: already built — read it to match patterns

## Phase A — Build

1. Read the spec for all user stories in this milestone
2. Read the use case plan to understand the exact user journey
3. Read existing source code to match patterns (component structure, hooks, styling, i18n)
4. Implement each user story:
   - Follow the spec's acceptance criteria exactly
   - Match the existing code patterns (don't introduce new patterns)
   - Handle ALL edge cases listed in the spec
   - Use the project's existing UI components, hooks, and utilities
5. **API Contract Check (MANDATORY before Phase B).** For every `fetch('/api/...')` or Supabase client call you wrote or touched this milestone:
   - Read the backend handler (in `api/**` or the relevant DB schema / RLS policy)
   - Confirm that every field read by the frontend exists in the backend response with the same name (e.g. if client reads `user_metadata.role`, backend must write/read `user_metadata.role` — not `app_metadata.role`)
   - Confirm auth expectations match (JWT location, role source, session shape)
   - Confirm status code semantics match (which codes mean what)
   - Record one line per call in the exploration log under `## API Contract Check`: `FE: <file:line> → BE: <file:line> — OK` or `— MISMATCH: <details>`. MISMATCH = fix before Phase B.
6. After all stories: run `npx vite build` — must pass with 0 errors
7. Commit on a work branch or locally (no push to production) and deploy the PREVIEW; write its
   URL to `docs/pipeline/m{N}-preview-url.txt`.

## Phase B — Explore

Use the Playwright LIBRARY (`import { chromium } from 'playwright'` in a script under `tests/e2e/exploration/`, run with `node`) to walk through the deployed preview and capture screenshots. The session has no MCP server: `browser_*` tools do not exist here.

### Exploration Rules

1. **Follow the use case plan exactly.** Each step in the plan has a `screenshot` filename — capture that exact filename.
2. **For each step:**
   a. Perform the action described
   b. Check the DOM state matches expectations (locator assertions, text content)
   c. Take a `page.screenshot()` with the exact filename from the plan
   d. Save to: `{project-dir}/tests/e2e/exploration/m{N}/{screenshot-filename}`
3. **For edge cases — real backend first:**
   a. **Default:** trigger the edge case against the real backend by manipulating real data or auth state (e.g., create a record to test "already exists", sign out to test "unauthorized", delete a row to test "not found"). Screenshots for acceptance criteria MUST come from real backend responses.
   b. **Mocks are a last resort**, allowed ONLY for conditions the real backend cannot reproduce on demand: provider outages (3rd-party down), timeouts > 30s, malformed responses the server never returns, rate-limit walls. When you use a mock, label the step in the exploration log as `MOCKED: <reason why real backend cannot produce this>`.
   c. **Banned:** mocking authentication, role, session expiry, or any owned-backend state to bypass a verification. If the user flow goes through your own API, you must test it end-to-end with real JWTs against the real API.
   d. **Demo shortcuts (e.g., "Demo Admin" buttons):** if they exist, use them ONLY for UI-only flows. Any flow that hits `/api/*` must also be verified with a real logged-in user whose role is set in Supabase.
4. **Screenshot naming:** Use EXACTLY the filenames in the use case plan. Do not rename.
5. **Retake if wrong:** If a screenshot doesn't show the expected state, fix the code and retake.

### Exploration Log

Write the exploration log incrementally to `{project-dir}/tests/e2e/exploration/m{N}-exploration-log.md`.

After EACH story (not at the end), append:
```markdown
## US-{X.Y} — {Title}
### Happy Path
- Step {n}: {what happened} → {screenshot filename} ✓/✗
### Edge Case E{n}: {label}
- Step {n}: {what happened} → {screenshot filename} ✓/✗
### Issues Found
- {any bugs discovered and fixed}
```

### Test Snippets

For each user story, write a Playwright test snippet to `{project-dir}/tests/e2e/exploration/m{N}-test-snippets/US-{X.Y}.test.ts`.

Each snippet must:
- Test the happy path steps from the use case plan
- Test each edge case with API interception
- Use meaningful assertions (not just "element visible" — check text content, counts, states)
- Be runnable with `npx playwright test`

## Completion

When done:
1. Run `npx vite build` one final time — must pass
2. Count your screenshots vs the plan's required screenshots — report the numbers
3. List any screenshots you could NOT capture and why
4. Give the preview URL, the commits, the screenshots count, and what you could not do — that is your final message to the chef (the chef writes it into the journal; do NOT write a verdict yourself)

## Rules

- You CANNOT waive spec requirements. If something seems impossible, fix the code to make it possible.
- You CANNOT skip edge cases. Every edge case in the spec must have working code AND screenshots.
- You CANNOT fabricate claims. If a feature doesn't work, say so — don't claim it does.
- You CANNOT batch-write the exploration log. Write incrementally after each story.
- If you find a bug during exploration, fix it immediately and retake affected screenshots.
- Every browser interaction goes through the Playwright library (no MCP in this session).
- NEVER write anything under `tests/e2e/verification/` — that folder belongs to the independent verifier.
- NEVER use `cp`, `mv`, `xcopy`, or any file-copy command to create screenshots from other screenshots. Every file in `tests/e2e/exploration/` MUST come from a distinct `page.screenshot()` call. Reusing an existing PNG under a new name is fabrication. If a story genuinely can't produce a unique screenshot (e.g., two edge cases converge on the same UI state), write that in the exploration log explicitly.
- If you hardcode a user-facing string in JSX (e.g., a French/English label directly in a `<th>` or badge) in a project that has `src/i18n/*.json`, you MUST wrap it in `t(...)` with a new key added to every locale file.
- **No mock-first verification.** Every acceptance criterion must be verifiable against the real backend. If a story path runs only when a `page.route()` intercept fires, the story is not built — it's simulated. Flag it in the exploration log as `NOT VERIFIED AGAINST REAL BACKEND` and fix the code, don't hide behind the mock.
- **No demo-shortcut-only verification of backend-touching flows.** A "Demo Admin" button or similar client-side shortcut verifies the UI mounts, not that the API works. For any flow that calls `/api/*` you MUST also run it with a real signed-in user whose role/state is set in the real auth system and capture a screenshot of the success response.
- **Seed/demo data warning.** If the app reads from seed or fixture data (e.g., rows inserted by a `seed.sql` or a `003_seed_*.sql` migration), flag this in the exploration log. Before declaring a data-reading feature "verified", confirm the happy-path also works when that seed is empty — create at least one real row via the app's own flow and re-capture a screenshot.
```
