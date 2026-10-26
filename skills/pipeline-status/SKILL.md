---
name: pipeline-status
description: Check pipeline progress — shows current step, artifacts produced, and what to do next. Use when the user asks about pipeline status or runs /pipeline-status.
---

# Pipeline Status

Show the current state of the pipeline workflow in this project.

## Process

1. **Check for state directory** — look for `docs/pipeline/status.md` in the current project.
   - If it doesn't exist: "No pipeline initialized. Run `/pipeline-step1` to start."
   - If it exists: read it and continue.

2. **Read status.md** — parse current step, sub-step, and timestamp.

3. **Check artifacts** — scan `docs/pipeline/` for which files exist:
   - `config.json` — configuration
   - `architecture-map.html` — Step 1 output
   - `mockup.html` — Step 2 output
   - `stories.json` — validated user stories
   - `roadmap.html` — roadmap
   - `spec.md`, `plan.md`, `tasks.md`, `rules.md` — Project Kit
   - `spec-final.md` — Step 5 reconciled spec
   - `project-memory.md` — rolling summary

4. **Display status** — format as:

```
Pipeline Status
===============
Current step: Step {N} — {name} (sub-step {X})
Last updated: {timestamp}

Artifacts:
  [x] architecture-map.html
  [x] mockup.html
  [ ] roadmap.html
  ...

Next: Run `/pipeline-step{N}` to continue (or `/pipeline-step{N+1}` if ready).
```

5. **Show project memory** — if `project-memory.md` exists, display its contents as a summary of the project so far.
