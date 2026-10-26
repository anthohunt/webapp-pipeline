# Dépendances tierces

Ce dépôt ne redistribue aucune bibliothèque tierce. Les composants ci-dessous sont installés à part, par
l'utilisateur, quand il en a besoin.

| Composant | Rôle | Licence | Obligatoire |
|---|---|---|---|
| flux (moteur de pipelines, dépôt séparé du même auteur) | joue les graphes, lance les agents, passe les contrôles | Apache 2.0 | oui |
| Python 3.10+ (bibliothèque standard) | outils, contrôles, programme du module | PSF | oui |
| jsonschema | vérification des graphes par le moteur flux | MIT | oui (via flux) |
| tmux | sessions détachées du lanceur de l'étape 2 | ISC | pour lancer des agents |
| Claude Code (Anthropic) | les agents ; le module `mod/` est un mod de Claude Code | conditions d'Anthropic (non libre) | pour lancer des agents |
| PyYAML | tournage de la vidéo (`tools/webapp-tourner.py`) | MIT | non (vidéo) |
| edge-tts | voix de synthèse de la vidéo | LGPL 3.0 | non (vidéo) |
| playwright-core, Chromium de Playwright | relevé des pages (`tools/webapp-sonde.mjs`), tests des applis construites | Apache 2.0 | non |
| Outil de tournage (mod « tournage ») | filmer et monter la vidéo de démonstration | non fourni | non (vidéo) |

Les applications que la pipeline construit utilisent par défaut React, Vite, Supabase (client), Playwright et
Vitest (licences MIT ou Apache 2.0), installés dans chaque application, jamais dans ce dépôt. Leur hébergement
(Supabase, Vercel) passe par les comptes de l'utilisateur.

Toutes ces licences sont compatibles avec la licence Apache 2.0 du code de ce dépôt : rien n'est recopié ni lié
statiquement ; edge-tts (LGPL) n'est qu'importé, à l'exécution, par un outil facultatif.
