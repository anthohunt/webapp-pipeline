---
name: pipeline-step1
description: Étape 1 « Concevoir » de la pipeline web app — pitch, questions d'usage, cahier des charges, parcours utilisateur, histoires dérivées du parcours, mockup dual-layer testé par le client, design bundle. Run this first.
---

# Pipeline Step 1 — Concept & Design (via Claude Design)

Guide the user through concept definition and visual design using **Claude Design inside Claude Code** (the `design` skill + `/design-sync`). Terminal Claude Code handles concept capture, seed-prompt construction and the design bundle; the canvas of artboards handles the visual layer (design system, screens, refinement by direct manipulation).

Output: `cahier-des-charges.md`, `parcours-utilisateur.json/.md` and a design bundle at
`docs/pipeline/design/`, consumed by `/pipeline-step2`.

The order is fixed, because each piece is derived from the one before:
**concept → cahier des charges → parcours utilisateur → stories → mockup → test du client.**
The stories come OUT of the parcours (one per gesture of a parcours step), and the mockup
draws the screens the parcours name. Writing stories or screens before the parcours means
inventing them — and the demo video of step 2 films one sequence per parcours, so a gesture
no parcours carries is never filmed.

**The client is in the room.** The operator plays this step with the client: the questions are
about the client's usage, and the mockup test is the client's.

## This step is INTERACTIVE — it is never launched, it is played

Step 1 is a conversation: closed questions, one at a time, arbitrated on a skeleton that
gets republished after every answer. Nothing here can run headless — there would be nobody
to answer. So the orchestrator (flux) never starts this step: it hands over the brief and
then waits to check the deliverables. The step happens in an already-open Claude Code
session, and only the gate is automatic.

## Prerequisites

- Claude **Pro, Max, Team, or Enterprise** plan (Free tier has no access)
- The `design` skill available in this build of Claude Code (otherwise: browser fallback)

## Gate Check

Read `docs/pipeline/status.md`:
- Missing → fresh project, proceed to Sub-step A
- Step 1 → resume/restart
- Step > 1 → warn: "Project is already at Step {N}. Re-running overwrites state. A) Restart B) Cancel"

---

## Sub-step A — Concept Capture (terminal)

The user's first message IS their pitch. Do NOT ask "what do you want to build?".

**If the user mentions building on an existing codebase**, read existing code for context and skip to Sub-step B.

Reformulate in one message:

> Got it. So the idea is: {1-2 sentence reformulation}.
> **A)** Yes, that's it
> **B)** No, let me clarify

- Vague pitch: up to 2 closed A/B/C follow-ups, then reformulate anyway
- Too detailed: acknowledge, focus on core ("Noted — details in Step 2")
- Loop until A

---

## Sub-step B — Understand the Core Loop (terminal, A/B/C + write-in)

BEFORE scoping sections/screens, understand app behavior.

Ask 2-4 questions — **one per message, always A/B/C plus a fourth write-in option
SPELLED OUT among the choices** — about:
- Core user flow (what does the user DO?)
- Triggers (user actions → app reactions)
- Data (what gets created, tracked, displayed?)

**Never ask a bare open question.** A blank question makes the user do the design work;
proposing 3 plausible answers makes him ARBITRATE, which is faster and sharper. Propose
what you would build, in order of preference — the write-in exists for what you missed.

```
Une partie, ça marche comment ?
**A)** Manche de 10 extraits, score à la fin (recommandé)
**B)** Sans fin, tu t'arrêtes quand tu veux
**C)** Contre-la-montre : le plus d'extraits en 2 minutes
**D)** Autre — dis-moi
```

NO UI questions yet. NO user stories. Just behavior.

---

## Sub-step C — Scope Questions (terminal, closed A/B/C/D)

Once the loop is clear, derive scope. Rules:

- One question per message. NEVER batch.
- 3-5 options max, always spell out the write-in option, always suggest first.
- 4-8 questions total.

Questions to cover:
1. **Main sections** of the app (propose based on Sub-step B)
2. **Key screens** per section
3. **Navigation flow** between sections
4. **Core user actions** per screen (high-level)
5. **Language**: A) English B) French C) Other

### Proactive 3D / Three.js suggestion

If the concept mentions any of: `map of X`, `visualize X`, `explore Y`, entities with relationships (researchers, papers, products, users, companies), clusters/communities, spatial/geographic/conceptual "spaces", dashboards with aggregated entities — **proactively propose** a 3D option:

> For the {screen} screen, we could use flat 2D (simple) or a 3D Three.js visualization (orbit controls, clustered view, significant upgrade). Want me to include 3D in the Claude Design seed prompt?

Record the decision — it goes into the seed prompt.

---

## Sub-step C2 — Cahier des charges (terminal, validated)

Once the scope is clear, write `docs/pipeline/cahier-des-charges.md`. Six sections, each a
short list — the gate checks they are all there:

- **But** — what the app is for, in one or two sentences, from the client's words
- **Utilisateurs** — who uses it, in what situation
- **Périmètre V1** — what the first version does (the gestures, not the features list)
- **Hors périmètre** — what it explicitly does not do (at least three refusals)
- **Contraintes** — device, place of use, language, legal, volume
- **Sources de données** — every external source, each **checked online** (it exists, it
  answers, its terms allow the use). A source nobody checked is a promise, not a source.

Present it in short points, then ask for validation in A/B/C/D (A) oui / B) je corrige /
C) il manque quelque chose / D) autre chose, précise-moi). Never move on without an explicit
yes.

## Sub-step C3 — Parcours utilisateur (terminal, validated, BEFORE stories and mockup)

A **parcours** is one complete usage, end to end, told as a sequence of steps: « je prépare
ma liste de courses et je la partage avec ma colocataire ». Two to five parcours cover a V1; each
one becomes a sequence of the demo video at step 2.

Write `docs/pipeline/parcours-utilisateur.json`, exactly in this shape (closed definition —
the gate refuses any other):

```json
{"parcours": [
  {"id": "P1", "titre": "…", "qui": "…", "but": "…",
   "etapes": [
     {"n": 1, "ecran": "S1", "geste": "j'ouvre l'appli et je vois les prix autour de moi",
      "stories": ["US-1.1"]}
   ]}
]}
```

- `id` unique (`P1`, `P2`…), `titre`, `qui`, `but` non empty.
- `etapes` numbered 1, 2, 3… in order; each names its `ecran` (an id that `screens.json`
  will carry — screens are NAMED here and DRAWN at Sub-step D) and its `geste`.
- `stories` starts empty here and is filled at D.2, when the stories are derived: every
  step must end up citing at least one story, and every cited story must exist.

Write `docs/pipeline/parcours-utilisateur.md` alongside: the same parcours for a human
reader — one sentence per parcours, then its numbered steps. Present each parcours that way,
then ask for validation (A/B/C/D).

---

## What Step 1 does NOT decide

Step 1 frames **usage and scope**: what the app does, for whom, what it refuses to do,
what the screens are. It never decides **how it is built** — framework, hosting, PWA vs
native, database, offline strategy, audio pipeline. Those belong to Step 2, which asks
them with the architecture in hand.

The test before asking a question: *would the answer change what the user SEES or CAN DO,
or only how we build it?* Only the first kind belongs here. "Do you want it installable as
an app, or in the browser?" is a build question wearing a usage costume — ask instead
where and how he plays, and let Step 2 derive the support from that.

When a technical question surfaces during framing, **do not ask it** — append it to
`docs/pipeline/questions-techniques.md`, one line each, with the usage fact that raised
it. Step 2 opens that file before its stack questions, so nothing is lost and nothing is
decided too early.

---

## Live Skeleton — the framing artifact (Sub-steps B and C)

As soon as the first answers land, publish a **skeleton**: a deliberately bare wireframe
of the screens known so far (monospace, hairline borders, grey blocks, no design system),
as an Artifact. Republish **the same file path** after every answer so the URL never
changes — the user watches his app take shape as he arbitrates.

**Any question about something VISIBLE is asked visually.** Render each option A/B/C
inside the affected zone of the skeleton, right under the question, so the user compares
drawings instead of imagining them. Text-only questions stay text-only (data source,
persistence, language).

Two rules keep this from turning into design work:

- **The skeleton is a decision support, thrown away after Step 1.** It never becomes the
  design: the canvas of Sub-step D owns the visual layer, and the skeleton is not part of
  the design bundle. Keep it ugly on purpose — fast to redraw, impossible to mistake for
  a mockup.
- **A visual question covers the whole zone it touches, not one field.** If the screen
  shows four statistics, the options must show the four — proposing a treatment for one
  of them and leaving the rest blank forces the user to arbitrate on a fragment.

Record the skeleton URL in `docs/pipeline/skeleton-url.txt` — Step 2 reads it to see what
was arbitrated and how.

---

## Sub-step D — Interactive Mockup (dual-layer, one Artifact)

Build ONE published Artifact with two layers side by side:

- **App prototype** (left/main): the real screens, clickable, styled with the PROJECT's own
  design system (see below) — this IS the product prototype, not a diagram of it.
- **Stories panel** (right sidebar): every user story from `stories-v1.json`, in PIPELINE
  NEUTRAL style (DM Sans, `#faf9f6` background, earthy accents) — never the app's theme.
  Clicking a story navigates the prototype to its screen and highlights the exact element(s)
  the story is about (a `data-el` attribute matching the story's target, pulsed/outlined for
  ~1.5s). Each story item shows a title AND a one-line detail — never a bare title.

Permanent rule: every screen in the prototype layer is CLICKABLE, never a static picture —
buttons respond, selections highlight, real state changes, not drawn-on states.

### 1. Design system first, in tokens

- **Existing codebase or brand assets** → run `/design-sync` (pull) so the prototype inherits
  the real palette, typography and components.
- **Greenfield** → decide the direction YOURSELF, from the concept and its usage context, and
  say why in one sentence. This step does not ask — framing already happened at Step 1's
  concept sub-steps.

  Fix it as `docs/pipeline/design/tokens.json` (colors by ROLE — ground, surface, ink,
  accent, semantic — type scale, spacing scale, radii) and `design-system-spec.json` (the
  manifest: paths + framework). Roles, never raw hexes in markup.

### 2. Derive the first user stories FROM THE PARCOURS, one per gesture

Before building the prototype, write `docs/pipeline/design/stories-v1.json`: walk each
parcours step by step, and turn each gesture into a story ("as a driver, I pick my fuel to
see only the prices that concern me"), each carrying a `screen` id (the step's `ecran`) and a
`target` — the `data-el` key of the element it is about. Then write the story ids back into
the step's `stories` in `parcours-utilisateur.json`: **every step cites its stories**.

Every interactive element the screens need must have at least one story; a control nobody
tells a story about is a control nobody builds or tests. A story that no parcours carries is
allowed (a secondary gesture), but say why in one line — it will not be filmed.

Present the stories grouped by parcours, one line each, and ask for validation.

### 3. Build the mockup — a real editorial pass, not a redrawn skeleton

Load `artifact-design`'s EDITORIAL process before writing the prototype layer (the
skeleton was deliberately bare; this is the opposite move). Ground the visual direction in
the app's own subject — its materials, vernacular, what the app is ABOUT — not a generic
theme. Commit to one distinctive motif drawn from that subject, one accent spent in one
place, real typographic personality (a characterful display face, not the safe default),
and at least one deliberate motion moment. Never carry over the skeleton's plain
cards/pills/tables verbatim — redraw them in the chosen direction. The stories panel stays
pipeline-neutral regardless (DM Sans, off-white, earthy) — the editorial pass is for the
app layer only.

One HTML file: a screen switcher (tabs, or driven by the story panel) over the app layer, the
stories sidebar on the right, and JS that (a) shows the right screen on story click, (b) adds
a highlight class to the story's `data-el` target for ~1.5s, (c) keeps the two layers'
styling from ever mixing.

Publish it as a normal Artifact (`artifact-design` skill governs the build; this is NOT the
`design` canvas skill — no `.dc.html`, no seed-canvas — a hand-built page gives full control
over cross-screen navigation and the story-driven highlight, which isolated artboards cannot
do). Give the user the link, then go through it WITH him: he clicks stories and screens, calls
out what is wrong, you fix and republish at the same path — live, no end-of-round list.

Hard-won technical rules:
- Selectors in the highlight map must match real `data-el` values in the HTML — verify every
  one after building; a mismatch is a silent failure.
- Keep the DOM light per screen; heavy SVG diagrams make the tab unresponsive.
- Give every story a title AND a one-line detail — a bare title reads as unfinished.

The stories panel may group stories by parcours (one collapsible group per parcours, in
step order) — it lets the client replay a whole usage by clicking down the list.

**The test is the client's.** The operator relays what the client says; you fix and republish at
the same link, one remark at a time. When the client is done: `validation.md` records what
was validated and what changed (remarks word for word), dated, posterior to `screens.json`
AND `stories-v1.json`. Every screen a parcours names must exist in `screens.json` by then —
the gate checks it.

### Fallback — the `design` skill

If the operator explicitly wants a multi-artboard canvas instead (e.g. to hand off to visual
design tools downstream), the `design` skill remains available — but it is not the default
here: it cannot show a story panel driving cross-screen highlights.

## Sub-step E — Design Bundle

`docs/pipeline/cahier-des-charges.md`, `parcours-utilisateur.json` and `parcours-utilisateur.md`
stay at `docs/pipeline/` (they are not design, they are what the design serves). Freeze what
the mockup decided into `docs/pipeline/design/`:

1. **`mockup-url.txt`** — the published Artifact URL (one line).
2. **`mockup.html`** — local copy of the published file, so the prototype survives without
   network.
3. **`tokens.json` + `design-system-spec.json` + `design-system.md`** — the project's own
   design system (Sub-step D.1).
4. **`screens.json`** — the machine-readable screen map, each with its `interactive_elements`
   (the `data-el` keys). Step 2's UI-coverage rule checks every one is named by a story.
5. **`stories-v1.json`** — the first user stories, one per gesture, each with `screen` and
   `target`.
6. **`validation.md`** — what the operator changed and validated, dated, posterior to both
   `screens.json` and `stories-v1.json`.

## Sub-step F — Write State

### `docs/pipeline/status.md`

```markdown
# Pipeline Status

- **Current step:** 1
- **Sub-step:** complete
- **Last updated:** {ISO 8601}
- **Summary:** Concept validated, design canvas bundled. {N} sections, ~{M} screens.
```

### `docs/pipeline/skeleton-url.txt`

The artifact URL of the live skeleton (one line).

### `docs/pipeline/config.json`

```json
{
  "language": "{en|fr|...}",
  "design_source": "claude-design-cli",
  "design_bundle": "docs/pipeline/design/",
  "three_d_screens": ["{screen}", ...]
}
```

### `docs/pipeline/project-memory.md` (≤2000 chars)

- **Concept**: 1-2 sentence description
- **Sections**: list with screen counts (from `design/screens.json`, else from Sub-step C)
- **Navigation flow**: how sections connect
- **3D screens**: if any
- **Key decisions**: rejected ideas, scope boundaries, style/framework choices made with the user

---

## Sub-step G — Graphify (optional, non-blocking)

```bash
python -c "import graphify" 2>/dev/null || pip install graphify -q 2>/dev/null || echo "graphify install skipped"
python -m graphify install 2>/dev/null || true
python -m graphify hook install 2>/dev/null || true
```

Skip if `graphify-out/graph.json` already exists. Failures are logged, not blocking.

---

## Completion

End with:

> **Step 1 done.**
> - Design bundle: `docs/pipeline/design/`
> - State: `docs/pipeline/status.md`, `config.json`, `project-memory.md`
> - {Graphify git hook installed. OR Graphify not installed — non-blocking.}
>
> Run `/pipeline-step2` to generate system architecture, Project Kit, roadmap, and E2E tests.

---

## Rules

- **One question per message. A/B/C/D format, ALWAYS — including the behaviour questions of Sub-step B.** The last option is a write-in and it is WRITTEN OUT as an option of its own (« Autre chose — précise-moi »): when the question goes through a choice widget, enumerate it like the others instead of leaning on the widget's implicit "Other" field, which the user does not read as an invitation. Always suggest first, ordered by what you would pick.
- **Jamais de phrase hybride affirmation+question** (« Je génère X avec Y ? »). Soit une question fermée AVANT d'agir, sans dire qu'on est déjà en train de le faire ; soit un fait accompli énoncé APRÈS coup, sans point d'interrogation. Les deux dans la même phrase brouillent qui décide.
- **Never batch questions. Never ask a bare open question** — if you can imagine three answers, propose them.
- **Never ask a build question.** Framework, support, hosting, storage: it goes to `questions-techniques.md`, not to the user.
- **Never re-create the visual layer in terminal.** No Playwright extraction, no HTML mockup generation, no ELK.js architecture-map. Claude Design owns it.
- **Never redraw the canvas once handed over.** The user refines it himself on the artifact; terminal Claude Code waits for his verdict.
- **Publish the mockup over HTTP as well as an artifact.** Run
  `$WEBAPP_PIPELINE_HOME/tools/publier-design.sh <workspace>` (works from any machine that can write to `DESIGN_PUBLISH_DIR`) and write the address it
  prints into `docs/pipeline/design/mockup-public-url.txt`. An artifact belongs to the
  account that published it and stays private; the person who tests the mockup may not
  have that account, and their test is the step's only human gate — it cannot depend on
  a login. The gate checks that file.
- **Parcours before stories, stories before mockup.** A story is a gesture of a parcours step; a screen is where a parcours step happens. Drawing first and narrating after produces screens nobody uses and gestures nobody films.
- **Terminal does:** concept capture, live skeleton, cahier des charges, parcours, seed-prompt construction, canvas invocation, design bundle, state files.
- **The canvas does:** design system, artboards, refinement by direct manipulation.

---

## Legacy Flow (fallback)

If Claude Design is unavailable (404, admin-disabled, rollout pending) and the user wants to proceed anyway, the previous Playwright-based flow (design-profile extraction, 5-preset templates, pipeline neutral architecture-map.html, dual-layer mockup.html) lives in git history at commit preceding this rewrite. Restore locally if needed.

Preferred behavior: **wait for Claude Design access** rather than fall back. The legacy flow is deprecated.
