---
name: pipeline-step2
description: Import the interactive mockup bundle, produce system architecture, user stories, roadmap, Project Kit, and E2E tests. After Step 1.
---

# Pipeline Step 2 — Specifications & Roadmap

Step 2 consumes the interactive mockup bundle from Step 1 and produces everything needed for build: system architecture diagram, validated user stories, roadmap, Project Kit (spec/plan/tasks/rules), and E2E test scaffolding.

The visual layer (design system, mockup, prototype) is already done at Step 1 — Step 2 does NOT redo that.

## This step is AUTONOMOUS — it asks nothing

Design is over. Step 2 decides on its own and writes down WHY: no A/B/C questions, no
"does this match?", no "looks good?" loops. The stack itself is not even a decision — it is a
STANDARD (React+Vite / Supabase / Vercel, below); what `stack-decisions.md` records is how
that standard applies to this project, plus any deviation and the usage fact forcing it.

The user does not come back inside this step. The one human barrier of the whole pipeline is
the mockup test, already behind us.

## Gate Check

1. Read `docs/pipeline/status.md` — confirm Step 1 is marked complete.
2. Verify `docs/pipeline/design/` exists and contains:
   - `screens.json` (screens + interactive elements — REQUIRED, it drives UI coverage)
   - `design-system.md` (palette, typography, components)
   - `mockup-url.txt` (the published mockup artifact)
   - `validation.md` (what the user validated, after testing it live)
   - `stories-v1.json` (the stories derived from the parcours, one per gesture)
3. Verify `docs/pipeline/cahier-des-charges.md` and `docs/pipeline/parcours-utilisateur.json`
   exist: the parcours are the spine of everything below — stories, milestones' use cases, and
   the demo video at the build step (one sequence per parcours).
4. If missing: "Step 1 isn't complete or the design bundle is missing. Run `/pipeline-step1` first." and stop.

---

## Sub-step 0 — Design Bundle Import

### Read the bundle

Read every file under `docs/pipeline/design/`. Extract:

- **Sections** (from `screens.json` and the mockup)
- **Screens** per section, each with purpose/description
- **Navigation** between screens
- **Components** used (from design system README)
- **Design system summary**: palette, typography, spacing — for reference in spec.md
- **Any explicit user stories or requirements** Claude Design recorded in chat

If the bundle contains only `mockup-url.txt` (the local `mockup.html` copy is missing):
1. `WebFetch` the URL's README first.
2. If the artifact is unreachable, ask the user to save a local copy of the published page as `docs/pipeline/design/mockup.html`, then re-run this sub-step.

### Write parsed structure

Save to `docs/pipeline/design/parsed.json`:

```json
{
  "concept": "...",
  "sections": [
    { "name": "...", "screens": [ { "name": "...", "purpose": "..." } ] }
  ],
  "navigation": [ { "from": "...", "to": "...", "trigger": "..." } ],
  "components": ["Button", "Card", ...],
  "design_system": { "palette": {...}, "fonts": {...}, "spacing": {...} },
  "explicit_stories": [ "..." ]
}
```

### Sanity-check the parse yourself

The mockup is the source of truth: every screen in `screens.json` must appear in
`parsed.json`, with its section and its interactive elements. A screen that parses to
nothing is a parsing bug — fix it against the mockup, do not ask about it.

---

## Sub-step 1 — System Architecture Diagram

The old Step 1's `architecture-map.html` (screen-navigation diagram) is replaced by the Claude Design prototype itself — skip it.

Generate **only** the system architecture (backend + infrastructure) here.

### La pile est STANDARD — on l'applique, on ne la rechoisit pas

Toute application web construite par cette pipeline part de la même pile :

| Couche | Standard | Pourquoi c'est figé |
|---|---|---|
| Front | **React + Vite** (TypeScript) | un seul écosystème à maîtriser d'un projet à l'autre |
| Données / Auth | **Supabase** (Postgres + Auth + Storage + RLS) | comptes, données et fichiers en un service, API REST générée |
| Hébergement | **Vercel** | déploiement au push, CDN, aucune machine à administrer |
| Tests | **Vitest** + **Playwright** | critères d'acceptation vérifiables en unitaire et en bout en bout |

**Ne pose aucune question dessus et n'ouvre pas de comparatif.** Le standard existe pour que
l'effort aille dans le produit, pas dans le choix d'outils — et pour que l'infra partagée
(comptes, clés, conventions) serve tous les projets.

`docs/pipeline/stack-decisions.md` documente donc **deux choses seulement** :

1. **Comment le standard s'applique à CE projet** — le schéma de données, les tables et leurs
   politiques RLS, les buckets, ce qui est déployé où. Une ligne par élément, ancrée dans un
   fait d'usage du concept.
2. **Les ÉCARTS au standard, s'il y en a** — chacun avec le fait d'usage qui l'impose. Un écart
   n'est légitime que si le standard rend le produit impossible ou absurde (temps réel massif,
   contrainte de souveraineté des données, cible hors navigateur). « Je préfère » n'est pas un
   motif ; l'écart se signale à l'opérateur en une ligne au lieu de se décider seul.

Lis quand même `docs/pipeline/questions-techniques.md` : les questions différées au cadrage
que le standard ne tranche pas (stratégie hors-ligne, préchargement, volumétrie, sources de
données externes) se répondent ici, dans le même fichier.

### Les accès sont une infra PARTAGÉE, pas un pré-requis par projet

Le standard étant fixe, les comptes le sont aussi : un compte Supabase et un compte Vercel
servent tous les projets. Les accès vivent dans `$WEBAPP_STACK_ENV` (fichier hors dépôt, voir `.env.example`)
sur le serveur (hors dépôt, lisible par le seul utilisateur du moteur) :

```
SUPABASE_ACCESS_TOKEN=…      # jeton de gestion : crée le projet et applique les migrations
VERCEL_TOKEN=…               # jeton de déploiement
```

Le nœud de construction lit ce fichier, **crée le projet Supabase dédié** à la run, écrit ses
clés propres (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`) dans le `.env.local` du projet, et
lie le dépôt à Vercel. Rien de tout cela ne se demande à l'opérateur au moment du build.

Si le fichier `$WEBAPP_STACK_ENV` manque ou qu'un jeton est refusé : **s'arrêter et le dire en une ligne**
— jamais simuler le service, jamais inventer une clé, jamais committer un secret.

### Generate diagram

Invoke the `architecture-diagram` skill with the stack info. Output: `docs/pipeline/system-architecture.html` (dark-themed, shows components + relationships).

No approval round here: the diagram ships with the rest of the specification, and the
roadmap approval node is where the user weighs in.

---

## Sub-step 2 — User Stories Draft

### Start from the tested stories

`docs/pipeline/design/stories-v1.json` already holds the main stories — written on the
mockup and tested by the user at Step 3. **Load them as-is; they are decisions, not drafts.**
The gate refuses a `stories.json` that lost any of them.

Then, for each screen, add what the first pass deliberately left out: 2-5 stories covering
secondary gestures, plus anything `validation.md` records as a correction.

Format: `As a {user}, I can {action} so that {outcome}.`

Group by module/section. Output to `docs/pipeline/stories-draft.md` (pipeline neutral style: DM Sans, `#faf9f6`).

### Save the stories — and keep their link to the parcours

```json
[
  { "id": "US-1.1", "story": "As a user, I can...", "module": "section-name", "validated": true,
    "screen": "S1", "parcours": ["P1.1"] }
]
```

Write to `docs/pipeline/stories.json`.

**The stories come FROM the parcours (Step 1, D.2), and the link must survive this step.**
`parcours` lists the parcours steps the story plays, as `P<parcours>.<step n>`; `screen` is the
screen it lives on. Rules, checked again at Step 3:

- A story of `stories-v1.json` keeps its id and its `parcours` entries. Never rename or drop an
  id that a step of `parcours-utilisateur.json` cites — the video and the review find gestures
  through those ids.
- A story added here (edge case, completeness pair, A11Y) attaches to the step of the story it
  derives from (same `parcours` entry), or carries `"parcours": []` when it is a secondary
  gesture no parcours walks through — it is built and verified, but not filmed.
- If you split a cited story in two, update the step's `stories` list in
  `parcours-utilisateur.json` (and its `.md`) so it cites both. A step must keep citing at least
  one existing story.

---

## Sub-step 3 — Stories Expansion

Apply expansion rules in order:

1. **Edge cases** — 3 per main story (errors, empty states, boundary conditions)
2. **Completeness pairs** — Add/Delete, Open/Close, Show/Hide, Enable/Disable for every relevant action
3. **UI coverage (checked by the gate)** — Every entry of `interactive_elements` in
   `docs/pipeline/design/screens.json` must be named by at least one user story. Write the
   element name in the story so the mapping is machine-checkable, and record it in
   `docs/pipeline/ui-coverage.json`:
   `{ "S1": { "bouton Nouvelle sortie": ["US-1.1"], "filtre 4 semaines": ["US-2.3"] } }`
   An element with no story is a control nobody builds and nobody tests.
4. **A11Y stories** — Add US-A11Y-001 (keyboard nav), US-A11Y-002 (focus management), US-A11Y-003 (escape key), US-A11Y-004 (ARIA labels)
5. **Split/merge** — 1 story = 1 testable unit. Target 3-10 stories per milestone.
6. **Dependency order** — Foundational stories first within each milestone.
7. **Acceptance criteria** — 2-5 per story, specific and testable, in GIVEN/WHEN/THEN format.

Update `docs/pipeline/stories.json` with the expanded set.

---

## Sub-step 4 — Roadmap

### The roadmap is READ from the mockup, not invented beside it

The user validated the mockup **screen by screen** — that is the only thing they signed off.
A milestone is therefore **a group of screens from that mockup**, and its stories are simply
the stories of those screens. You are grouping screens, not inventing a work breakdown.

- **Every screen belongs to exactly one milestone.** A screen a milestone merely passes
  through (reached at the end of a flow, but built later) goes in `ecrans_traverses`, never
  in two owners. An ambiguous screen is the single most common defect here.
- **Every story follows its screen.** A story's `screen` field decides its milestone — you
  never place stories by hand.
- **A story with no screen is transverse** (accessibility, performance, i18n): it is checked
  on *every* milestone and audited at hardening, never parked in one milestone.
- Group screens that share a user flow, following the order the mockup itself proposes.
- No pure infra milestones — merge setup into the first user-facing milestone.
- Aim for 3-6 milestones; a project with many screens groups more per milestone rather than
  producing a dozen.

### Generate `docs/pipeline/roadmap.json` FIRST

The HTML is a rendering of this file, not the source. Write it before the page:

```json
{
  "source_de_verite": "docs/pipeline/design/mockup.html",
  "milestones": [
    {"n": 1, "titre": "…", "demontrable": true,
     "use_case": "tests/e2e/use-cases/m1-use-case.md",
     "ecrans": [{"id": "S1", "nom": "Entrée"}],
     "ecrans_traverses": [{"id": "S2", "nom": "Tableau de bord"}],
     "stories": ["US-1.1", "US-1.2"], "nb_stories": 2}
  ],
  "stories_transverses": {"motif": "…", "ids": ["US-A11Y-001"]}
}
```

**Check it before writing the page** — three counts that must hold, or the roadmap is wrong:
every screen of `screens.json` appears exactly once across `ecrans`; every story of
`stories.json` is in exactly one `stories` list or in `stories_transverses`; the sum of
`nb_stories` plus the transverse ones equals the total. State the three numbers in your
output.

### Generate

Create `docs/pipeline/roadmap.html` using pipeline neutral style (DM Sans, Space Grotesk, `#faf9f6`, earthy colors, rounded corners):

- **Header**: project name, concept summary, milestone count, story count
- **Per milestone**: name, **the mockup screens it owns** (id + name, and any screen it only
  passes through), demo outcome, full user stories, dependencies
- **Footer**: the transverse stories and why they belong to no single milestone
- **Progress indicators**: visual status markers

The screen list is what lets the user recognise their own mockup in the roadmap. A roadmap
page that does not name screens sends them back to guessing.

### Self-check

Every milestone must produce something the user can open and judge. A milestone whose demo
outcome you cannot state in one sentence is not a milestone — merge it into the next one.

---

## Sub-step 5 — Project Kit Generation

Read all prior output and produce the Project Kit. Can dispatch to a subagent.

### Output Files

All files go in `docs/pipeline/`:

**`spec.md`** — What & Why
- Product vision
- Sections with specs + references to the mockup screens
- Design system summary from `design-system.md` (palette, fonts, components — for engineer reference)
- User stories organized by type: Main, Edge, Pair, A11Y
- Each story has GIVEN/WHEN/THEN acceptance criteria
- Pre-flight requirements (deployment, DB, env vars, CLIs)
- Link to `docs/pipeline/design/` for design reference

**`plan.md`** — How (technical architecture)
- Tech stack: the standard — React+Vite (TS), Supabase (Postgres/Auth/Storage/RLS), Vercel, Vitest + Playwright
- Data models and API contracts
- Component architecture (derived from the mockup's components list)
- File structure

**`tasks.md`** — Ordered work units
- Each task: ID, user story reference, file paths, dependencies, "done when" condition
- Grouped into phases: Setup first, then per-milestone

**CRITICAL: No simulated/mock/stub services in tasks.** If the spec references an external data source, the task MUST implement the real integration — not a hardcoded JSON file or setTimeout. Sample data files are acceptable ONLY as fallback for offline development. Every service task must specify the actual endpoint/source and include error handling (network failure, rate limiting, empty responses, malformed data).

**`rules.md`** — Boundaries for the build phase
- **Always do**: testing, commit format, accessibility checks, use the mockup's design system
- **Ask first**: architecture changes, new dependencies, scope additions, design-system deviations
- **Never do**: skip tests, force push, deploy without green tests, re-invent the design system

---

## Sub-step 6 — Use Case Plans + Test Scaffolding

### Use Case Plans

**`tests/e2e/use-cases/m{N}-use-case.md`** — one file per milestone.

**Source of truth = the mockup.** It shows what each screen looks like and how interactions work. The use case plan scripts how to walk through those screens and verify them in the real app during Step 4.

**Walk the parcours first.** The journey of `m{N}-use-case.md` follows, in order, the parcours
steps (`parcours-utilisateur.json`) whose screen belongs to this milestone: each such step is a
numbered step of the plan, citing its parcours step (`P1.3`) and the stories it plays. Stories
of the milestone that no parcours step carries come after, as their own steps.

For each user story in the milestone, write:
- **Happy path**: numbered steps, one action per step, expected result (reference the prototype screen by name), screenshot filename for Step 4 to capture
- **Edge cases**: from spec.md edge cases, each with MULTIPLE steps: trigger action (screenshot), result state (screenshot), recovery action if applicable (screenshot). Minimum 2 screenshots per edge case.
- **Screenshot naming**: `{US-X.Y}-{NN}-{description}.png` for happy path, `{US-X.Y}-E{N}-{NN}-{description}.png` for edge cases
- **Prototype reference**: name the prototype screen each step corresponds to, so Step 4 can verify the real app matches the Claude Design intent

**No SKIPs allowed.** Every edge case is testable via `page.route()`:
- Network errors → `page.route(url, r => r.abort())`
- Empty data → input that produces zero results
- Timeouts → `page.route(url, r => r.fulfill({ status: 504 }))`
- Rate limits → `page.route(url, r => r.fulfill({ status: 429 }))`
- Malformed data → `page.route(url, r => r.fulfill({ body: '{malformed}' }))`
- Resume after nav → actually navigate away and back during loading

If you think an edge case can't be tested, you haven't thought hard enough about `page.route()`.

### Test Files (project root)

**`tests/features/FT-NNN-slug.test.js`** — metadata only: id, title, testMode, userStory, acceptance criteria. Documentation, not executable.

**`tests/e2e/tests/ft-nnn.js`** — Playwright scripts:
```javascript
module.exports = async function(page) {
  const results = [];
  // Setup: clean previous state
  // For each AC: interact via Playwright, verify outcome
  // results.push({ id: 'AC-1', criterion: '...', status: 'pass'|'fail', detail: '...', duration: ms });
  // Teardown: clean up test data
  return results;
};
```

**`tests/features/registry.json`**:
```json
{
  "features": [
    { "id": "FT-001", "title": "...", "file": "FT-001-slug.test.js", "testMode": "browser", "status": "draft" }
  ]
}
```

CRITICAL: **Explore-first test design.** Navigate the deployed app with Playwright BEFORE writing test scripts. Open the app URL, try each screen, click buttons, fill forms, verify selectors and timings empirically. NEVER write tests blind from specs alone. (The Claude Design prototype is a REFERENCE for intent, not the source of real selectors — the deployed app is.)

Generate tests for ALL user stories — main, edge, pair, A11Y. Target 1 test file per screen, grouping related stories. Every acceptance criterion must be covered.

---

## State Updates

After Project Kit generation:

1. **Update `docs/pipeline/status.md`**: mark Step 2 complete with timestamp.
2. **Rewrite `docs/pipeline/project-memory.md`** (max 2000 chars):
   - Concept summary
   - Current status
   - Sections with story counts
   - Milestone list
   - Kit status (which files generated)
   - Design bundle reference (`docs/pipeline/design/`)
   - Key decisions made during Step 2 (stack choices, story adjustments)

---

## Completion

> **Step 2 done.**
> - System architecture: `docs/pipeline/system-architecture.html`
> - Stories: `docs/pipeline/stories.json` ({N} total)
> - UI coverage: `docs/pipeline/ui-coverage.json` (every interactive element mapped)
> - Roadmap: `docs/pipeline/roadmap.html` ({M} milestones)
> - Project Kit: `spec.md`, `plan.md`, `tasks.md`, `rules.md`
> - Tests: `tests/e2e/use-cases/`, `tests/features/`, `tests/e2e/tests/`
>
> Run `/pipeline-step3` to verify the kit, configure git remote, and approve the roadmap.

---

## Rules

- **No questions at all.** This node is autonomous: decide, justify in `stack-decisions.md`, move on. The roadmap approval node carries the user's say.
- **The mockup is canonical**: never contradict the validated screens. When in doubt, re-read `docs/pipeline/design/`.
- **No mockup re-creation**: Step 2 does NOT generate `mockup.html` or `architecture-map.html`. The prototype in Claude Design replaces both.
- **Pipeline neutral style**: Only for pipeline artifacts (roadmap, stories-draft). The app's design system (from handoff) is NOT used in pipeline artifacts.
- **Subagent dispatch**: can dispatch Project Kit generation and test scaffolding to subagents.
