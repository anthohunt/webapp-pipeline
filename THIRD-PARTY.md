# Third-party dependencies

This repository redistributes no third-party library. The components below are installed separately by the user, when
needed.

| Component | Role | License | Required |
|---|---|---|---|
| flux (pipeline engine, separate repository by the same author) | plays the graphs, starts the agents, runs the checks | Apache 2.0 | yes |
| Python 3.10+ (standard library) | tools, checks, module program | PSF | yes |
| jsonschema | graph validation by the flux engine | MIT | yes (through flux) |
| tmux | detached sessions of the stage 2 launcher | ISC | to run agents |
| Claude Code (Anthropic) | the agents; the `mod/` module is a Claude Code mod | Anthropic's terms (not open source) | to run agents |
| PyYAML | video filming (`tools/webapp-tourner.py`) | MIT | no (video) |
| edge-tts | synthetic voice for the video | LGPL 3.0 | no (video) |
| playwright-core, Playwright's Chromium | page capture (`tools/webapp-sonde.mjs`), tests of the built apps | Apache 2.0 | no |
| Filming tool ("tournage" mod) | filming and editing the demo video | not provided | no (video) |

The applications the pipeline builds use React, Vite, Supabase (client), Playwright and Vitest by default (MIT or
Apache 2.0 licenses), installed in each application, never in this repository. Their hosting (Supabase, Vercel) goes
through the user's accounts.

All these licenses are compatible with the Apache 2.0 license of the code in this repository: nothing is copied or
statically linked; edge-tts (LGPL) is only imported, at run time, by an optional tool.
