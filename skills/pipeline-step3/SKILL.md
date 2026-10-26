---
name: pipeline-step3
description: Pre-implementation setup — verify Project Kit, configure git remote, run pre-flight checks, sign off the roadmap. Autonomous. After Step 2.
---

# Pipeline Step 3 — Pre-Implementation Setup

Verify the Project Kit from Step 2, configure git remote, run pre-flight checks, and sign off
the roadmap before building begins.

## This step is AUTONOMOUS — it checks, it fixes, it does not ask

Everything here is verifiable on the artifacts: a milestone either states its demo in one
sentence or it doesn't, a use-case file either exists or it doesn't. So this node checks and
CORRECTS rather than handing the work back for review. No approval round, no A/B loop.

The design's one human barrier is the mockup test (Step 1) — the place where only an eye can
judge. Everything downstream is contract-checked, until the client's review of the finished app
and its demo video (node `revue`).

## Process

### 1. Gate Check

Read `docs/pipeline/status.md` in the current project directory.

- **File does not exist:** Tell the user: "No pipeline state found. Run `/pipeline-step2` first to produce the Project Kit."
- **File exists and shows Step < 2 complete:** Tell the user: "Step 2 isn't complete yet. Run `/pipeline-step2` first."
- **File exists and shows Step 2 complete (or Step 3 in progress):** Proceed to Sub-step A.
- **File exists and shows Step > 3:** the run is further along; say so in one line and stop rather than overwriting setup state behind the build.

---

### 2. Sub-step A — Kit Verification

Automatically check that these Project Kit files exist:

- `docs/pipeline/spec.md`
- `docs/pipeline/plan.md`
- `docs/pipeline/tasks.md`
- `docs/pipeline/rules.md`
- `tests/e2e/use-cases/` directory (with at least one `m{N}-use-case.md` file from Step 2)

**If ALL found:** proceed silently to Sub-step B — internal bookkeeping is not worth a line of output.

**If ANY missing:** write the missing file yourself, from what the rest of the kit already
says (spec + stories + roadmap carry enough). Only a genuinely empty Step 2 — no stories, no
roadmap — is a blocker worth stopping on, and then you say so plainly and stop.

---

### 3. Sub-step B — Git Remote

Decide version control from what the workspace already shows:

- **A remote is already configured** (`git remote -v` answers) → keep it, record it in
  `docs/pipeline/config.json` under `gitRemoteUrl`, set `"pushOnEpic": true`.
- **No remote, and the deployment target needs one** (Vercel, Netlify, any push-to-deploy
  host named in `stack-decisions.md`) → create the repo (`gh repo create`, private by
  default) and record it the same way.
- **No remote and no push-to-deploy target** → local only, `"pushOnEpic": false`.

Creating a repo is an outward-facing act: do it under the user's account only, private, and
say in one line that it was created. Never push anything beyond the initial commit here.

---

### 4. Sub-step C — Pre-flight Check

Read the **Pre-flight Requirements** section from `docs/pipeline/spec.md` and settle each item
yourself. What you cannot settle — a secret, an account only the user can open — goes into
`docs/pipeline/config.json` as a listed prerequisite, named and blocking at deploy time, never
invented and never committed.

Key items to cover:

- **Deployment target** (Vercel, VPS, local dev, etc.)
- **Database** requirements and connectivity
- **CLI tools** needed (Node version, package managers, etc.)
- **API keys / tokens** — read existing config and shared tokens; a genuinely absent secret is listed as a prerequisite, not requested mid-run
- **External services** (auth providers, storage, CDN, etc.)

**Supabase headless workaround:** If the project uses Supabase via Vercel integration and you're in a headless/SSH context where `vercel integration add supabase` blocks on browser OAuth — skip the integration flow. Instead run `vercel env pull` to pull existing env vars (connection strings, API keys) from the already-linked Vercel project. This works when Supabase is already provisioned on the Vercel project.

**Save deployment info to `docs/pipeline/config.json`** under the `deployment` key as items are confirmed. Include whatever is relevant: `type`, `host`, `port`, `domain`, `database`, etc.

**Deferred requirements:** when a prerequisite cannot be settled here (a secret only the user
holds, an account only they can open):

1. Cross-reference `docs/pipeline/spec.md` for the user stories it affects.
2. Record it in `docs/pipeline/config.json` under `skippedFeatures` — each entry
   `{ "feature": "...", "reason": "...", "affectedStories": [...] }`.
3. Say it in ONE line at the end of the node, with the stories it blocks. That line is the
   whole notification; the build node will refuse to mark those stories done.

---

### 5. Sub-step D — Roadmap & Use Case Review

Display the roadmap from `docs/pipeline/roadmap.html` or from `docs/pipeline/spec.md` **as-is**. Do NOT rebuild or regenerate it.

**Testability gate:** Review every milestone in the roadmap yourself:

- Each milestone MUST produce something the user can see and test
- Pure infrastructure milestones (e.g., "Set up database", "Configure auth") with nothing user-visible MUST be merged into the next user-facing milestone
- If you merge any milestones, explain what was merged and why: "Milestone {X} (infra-only) merged into Milestone {Y} so every milestone is user-testable."

**Use case verification:** Verify that `tests/e2e/use-cases/m{N}-use-case.md` exists for EVERY milestone. These were produced in Step 2. Check that:
- Every user story has a happy path with numbered steps and screenshot filenames
- Every edge case from spec.md is listed with trigger and expected behavior
- Screenshot filenames follow the naming convention: `{US-X.Y}-{NN}-{description}.png`
- A missing use case file is written here, from the spec — the run does not go back to Step 2

These are the test plans Step 4 will execute. Verify them against the spec: a plan that skips an edge case, or names a screen the mockup does not have, is a defect to fix here.

**Mockup coverage gate — run it, do not eyeball it.** Read `roadmap.json`,
`design/screens.json` and `stories.json` and check three things:

1. Every screen appears in exactly one milestone's `ecrans` (a screen in two owners, or in
   none, is a defect — `ecrans_traverses` does not count as ownership).
2. Every story is in exactly one milestone's `stories`, or in `stories_transverses`.
3. Every story of a milestone is actually *played* by a step in its `m{N}-use-case.md`. A
   story named only in a section heading (`US-12.1..12.9`) is not played — the plan must have
   a numbered step producing a screenshot for it.

**Parcours coverage gate — run it too.** Read `parcours-utilisateur.json`, `screens.json` and
`stories.json`:

4. Every step of every parcours names an `ecran` that exists in `screens.json` **and** cites at
   least one story that exists in `stories.json`. A step without a screen cannot be built; a
   step without a story cannot be verified; and either way the video cannot film it.
5. Every story cited by a step carries that step back in its own `parcours` list.
6. Count the screens that NO parcours crosses. They are allowed (settings, legal page…), but
   each one is listed by id in `roadmap-approved.json` → `controles.ecrans_hors_parcours` with
   one line of reason: they will be built and verified, never filmed.

Report the counts. Then act on what you found, without asking:

- **Milestone not demonstrable** → merge it into the next one, record the merge and its reason.
- **Missing use case file** → write it from the spec, do not send the run back to Step 2.
- **Screen in two milestones** → give it to the one that *builds* it; the other lists it in
  `ecrans_traverses`.
- **Story in no milestone** → place it with its screen. Only a story with no screen at all
  goes to `stories_transverses`.
- **Story never played by its plan** → add the numbered step and its screenshot name.
- **Parcours step with an unknown screen or no story** → fix the link (the screen id or the
  story that plays the gesture). Never invent a screen the mockup does not draw: if the
  gesture has no screen, the parcours is wrong — correct the step and record it.
- **Story citing a step that does not cite it back** → make both sides agree.

Record every correction in `roadmap-approved.json` — that file is the sign-off, and the gate
refuses one produced outside this run. It carries `roadmap.json` in full (screens and stories
per milestone included) plus a `controles` block stating that each screen lands in exactly one
milestone and each story is placed or transverse. A sign-off that lists only milestone titles
proves nothing about what each one must satisfy.

---

### 6. Write State

Once the pre-flight is clean, update these files:

#### `docs/pipeline/status.md`

```markdown
# Pipeline Status

- **Current step:** 3
- **Sub-step:** complete
- **Last updated:** {ISO 8601 timestamp}
- **Summary:** Project Kit verified, git remote configured ({remote type}), pre-flight complete, roadmap signed off. {X} milestones ready for build.
```

#### `docs/pipeline/config.json`

Merge into the existing config (do NOT overwrite previous keys like `language`). Ensure these keys are present after this step:

- `gitRemoteUrl` (string or null)
- `pushOnEpic` (boolean)
- `deployment` (object with deployment details)
- `skippedFeatures` (array, empty if none)

#### `docs/pipeline/project-memory.md`

Rewrite the rolling summary (max 2000 characters) to include:

- **Concept:** 1-2 sentence app description (carried from previous steps)
- **Architecture:** section/screen count summary (carried from Step 1)
- **Kit status:** confirmation that spec, plan, tasks, rules are verified
- **Git remote:** type (GitHub / custom / local) and URL if applicable
- **Deployment:** target platform, key infrastructure decisions
- **Skipped features:** list if any, with affected stories
- **Roadmap:** milestone count, any merges made for testability, with their reasons

---

### 7. Announce Completion

End with:

> Step 3 done — pre-flight clean, {X} milestones ready.

This closes node `concevoir`. The build is launched on the build server, never from this session:
`/webapp lancer` in the module, or `python3 $WEBAPP_PIPELINE_HOME/tools/webapp-lancer.py <workspace>`.
