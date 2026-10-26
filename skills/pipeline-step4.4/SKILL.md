---
name: pipeline-step4.4
description: Tests, commit et mise en production après le PASS du vérificateur indépendant (web app en 3 étapes) — consolidation des tests, régression complète, commit, déploiement en production, contrôle sur l'URL, `docs/pipeline/app-url.txt`. Sous-skill de pipeline-step4 ; sert aussi au mode retours (4.3).
---

# Pipeline Step 4.4 — Test + Commit + Deploy

**Called by:** the chef (pipeline-step4) after the independent verifier's `Verdict : PASS` (4.2) — for a milestone or a retours round (4.3).
**Input:** Built and verified code, test snippets, production URL.
**Output:** Committed code, passing tests, production deployment, `docs/pipeline/app-url.txt`.

---

## Chef Instructions

The chef may run this phase directly (it is tests, git and deploy, not app code) or dispatch a single fresh agent for the test consolidation + regression portion. A regression that needs a code fix goes back to a Builder (4.1) and then a fresh verifier (4.2) — the chef never patches app code. Heavy CPU work (build, full suite) runs under `lourd COMMAND…`.

---

## Step 1: Test Consolidation

Consolidate the Builder's test snippets into a proper Playwright spec file.

### Process

1. Read all test snippet files from `{project-dir}/tests/e2e/exploration/m{N}-test-snippets/`
2. Read the use case plan to ensure all stories and edge cases have test coverage
3. Create a consolidated Playwright spec: `{project-dir}/tests/e2e/m{N}-explore.spec.ts`

### Spec File Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('M{N} — {Milestone Title}', () => {

  test.describe('US-{X.Y} — {Story Title}', () => {

    test.describe('Happy Path', () => {
      test('step {n}: {description}', async ({ page }) => {
        // Navigate, interact, assert
      });
    });

    test.describe('Edge Case E1: {label}', () => {
      test('step {n}: {description}', async ({ page }) => {
        // Intercept API, navigate, interact, assert
      });
    });
  });
});
```

### Test Quality Rules

- Every test must have meaningful assertions (check text content, element counts, visibility of specific elements — not just "page loaded")
- **Edge case tests — real backend first.** Default: trigger edge cases by manipulating real data or auth state (create/delete rows, sign in as real roles, cause real validation errors). `page.route()` interception is ALLOWED only when the real backend cannot reproduce the condition on demand (3rd-party outage, timeout > 30s, malformed response). When used, the test must name why in a code comment: `// MOCKED: <real backend cannot produce this>`.
- **Backend-touching flows must be covered by at least one real-backend test.** If a user story calls `/api/*`, the spec MUST contain at least one test that runs without any `page.route()` and asserts the real API response. A suite whose every `/api/*` test is intercepted fails this gate.
- Tests must save screenshots to `tests/e2e/delivery/` with the exact filenames from the use case plan (never into `tests/e2e/verification/`, which belongs to the verifier)
- Tests must be independent (each test navigates from scratch, no shared state)
- Use `test.setTimeout(60000)` for tests with API interception

---

## Step 2: Regression

Run ALL tests — current milestone AND all previous milestones.

```bash
# Unit tests
npx vitest run

# Build check
npx vite build

# E2E — all milestones
npx playwright test
```

### Handle Failures

- **Unit test failure from changed code:** Update the test if behavior intentionally changed, fix the code if regression
- **Build failure:** Fix immediately — must pass before proceeding
- **E2E failure in current milestone:** Fix the test or code, re-run
- **E2E failure in previous milestone:** This is a regression — fix the code, NOT the old test. Re-run ALL tests after fix.
- **Flaky test:** Re-run 3 times. If it passes 2/3, mark as flaky in test file with `test.fixme()` comment explaining why. If it fails 3/3, it's a real failure — fix it.

### Regression Report

Record in `{project-dir}/docs/pipeline/m{N}-journal.md` under "## Test & Regression":
- Unit tests: {passed}/{total}
- Build: PASS/FAIL ({chunk sizes})
- E2E: {passed}/{total} across {N} milestone specs
- Regressions found: {count} — {descriptions}
- Fixes applied: {count} — {descriptions}

---

## Step 3: Commit

After all tests pass:

1. Stage all changed files (source, tests, screenshots, docs):
   ```bash
   git add src/ tests/ docs/pipeline/m{N}-journal.md docs/pipeline/status.md docs/pipeline/project-memory.md
   ```
2. Commit with a descriptive message:
   ```
   feat(m{N}): {Milestone Title} — {brief description of what was built}
   ```
3. Do NOT push yet — push happens after deploy verification

---

## Step 4: Deploy

### Read deployment config

Read `{project-dir}/docs/pipeline/config.json` for:
- `productionUrl` — the Vercel deployment URL
- `pushOnEpic` — whether to push to remote
- `gitRemoteUrl` — the remote URL

### Deploy to Vercel

1. Push to the remote (if `pushOnEpic` is true):
   ```bash
   git push origin master
   ```
2. Wait for Vercel to deploy (check with `npx vercel ls` or monitor the Vercel dashboard URL)
3. Verify the deployment — REAL BACKEND SMOKE TEST (Playwright library — the session has no MCP server):
   - Open the production URL in Playwright
   - Sign in with a real account (from `docs/pipeline/config.json` → `testAccounts`), NOT a "Demo X" shortcut
   - Navigate through the new milestone's features and trigger at least one end-to-end flow per user story that calls `/api/*`
   - **Record every response (`page.on('response')`) and assert every `/api/*` call returns 2xx.** If any call returns 4xx/5xx, STOP — this is a real bug; back to a Builder, re-verify, re-deploy.
   - For any admin/role-gated flow: sign in as the real admin account and verify the first admin API call returns data (not 401/403). If it fails, the frontend/backend role check is mismatched — fix before shipping.
   - Take 2-3 verification screenshots showing the deployed app works
   - Save to `{project-dir}/tests/e2e/delivery/m{N}-deploy-verify-{nn}.png`

### If deploy fails

- Check Vercel build logs: `npx vercel logs`
- Common issues: missing env vars, build errors not caught locally, SPA routing (need `vercel.json` rewrites)
- Fix, re-commit, re-push, re-verify

---

## Step 5: Record

Update `{project-dir}/docs/pipeline/m{N}-journal.md` under "## Deploy":
- Commit hash
- Production URL
- Deploy verification: PASS/FAIL
- Screenshot evidence filenames

Write the production URL (one line, `https://…`) to `{project-dir}/docs/pipeline/app-url.txt` — the review and the video read it there. Check it answers: `curl -sI <url>` → 2xx/3xx.

In retours mode, the same record goes to `docs/pipeline/retours/tour-{N}-journal.md` under "## Deploy".

---

## Completion

After successful deploy + verification, the chef closes the milestone (pipeline-step4 §4 « Clore le jalon ») or moves on to the refilm (4.3 §4). Nothing is presented to anyone here: the client sees the app and its video at the review.
