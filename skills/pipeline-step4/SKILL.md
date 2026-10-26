---
name: pipeline-step4
description: Étape 2 « Construire » de la pipeline web app (nœud `construire`, serveur, autonome) — le chef lit l'avancement, choisit le mode (jalon, tournage ou retours), fait tourner le cycle bâtisseur → vérificateur indépendant → tests/commit/déploiement, tient `avancement.json`, puis tourne la vidéo. Un lancement = un jalon, ou le tournage, ou un tour de retours.
---

# Pipeline Step 4 — Construire (le chef)

Nœud `construire` du graphe `webapp` (3 étapes : concevoir → construire → revue). Il tourne
**seul sur le serveur** : personne ne répond à une question pendant qu'il tourne. Tu décides, tu
écris pourquoi dans le journal, tu continues. `tools/webapp-lancer.py` le lance, et le **relance**
tant que son contrôle (`webapp-construire`) n'est pas vert.

**Un lancement traite UNE unité de travail**, puis s'arrête (rapport de passe + sentinelle,
comme le brief le dit) :
• un jalon de la feuille de route (cycle complet, jusqu'à la mise en production) ;
• ou le tournage de la vidéo, une fois tous les jalons faits ;
• ou un tour de retours du client.

Contrat des fichiers : `$WEBAPP_PIPELINE_HOME/docs/2026-10-24-webapp-3-etapes-contrat.md`.

---

## 0. Stack Credentials — Shared Infrastructure, Not a Per-Project Prerequisite

The standard stack (React + Vite / Supabase / Vercel) ships with **credentials that already
exist**. Never conclude "no keys available" before looking in both places, in this order:

**1. `.env.local` at the project root** — the run's own Supabase project and Vercel project,
already provisioned. This is the normal case in a shared container, where several sessions
run side by side and account-wide tokens must never land:

```
SUPABASE_PROJECT_REF · SUPABASE_URL · VITE_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY · SUPABASE_DB_PASSWORD      # this project only
VERCEL_TOKEN · VERCEL_PROJECT_ID · VERCEL_ORG_ID      # scoped to this project only
```

```bash
set -a; . .env.local; set +a
```

These keys reach **this project and nothing else** — that is deliberate, not a limitation.
You cannot create another Supabase or Vercel project with them, and you do not need to:
yours already exists. `.env.local` is git-ignored; never commit it, never echo its values
into a report, a screenshot or a transcript.

**2. `$WEBAPP_STACK_ENV` (fichier hors dépôt, voir `.env.example`)** — account-level tokens
(`SUPABASE_ACCESS_TOKEN`, `VERCEL_TOKEN`), readable only on the build server. They exist to
*provision* a run's projects. If `.env.local` is present, you do not need them; if this file
is unreachable (you are in a container), that is expected — do not treat it as a blocker.

**Supabase free plan = 2 active projects per organisation.** Before creating the run's project,
count them (`GET /v1/projects`, status `ACTIVE_HEALTHY`). If two are already active, do not
pause anyone's project yourself (they may be a client's live app): write
`avancement.json.bloque` = « Supabase : déjà 2 projets actifs (<noms>), en mettre un en pause
puis relancer », rapport, sentinelle. The `/webapp` pane shows that sentence with a Relancer
button.

**Any other service** the spec calls for (transactional e-mail, payments, analytics…) is
*not* covered by this file. If a milestone genuinely cannot be built without one, build
everything that does not depend on it, state the missing key in one line in
`docs/pipeline/status.md`, and keep going — do not stop the whole node, and never mock the
service to fake a PASS.

---


## 1. Lire l'état, choisir le mode

L'état vit dans les fichiers, jamais dans la mémoire d'un agent : tu es une instance neuve à
chaque lancement. Lis, dans cet ordre, et prends le **premier** cas vrai :

| # | Constat | Mode | Sous-skill |
|---|---------|------|-----------|
| 1 | un `docs/pipeline/retours/tour-<N>.json` au statut `a-traiter` | **retours** sur le plus petit N | `pipeline-step4.3` |
| 2 | un jalon de `roadmap-approved.json` non coché dans `status.md` | **jalon** : le premier non coché | `4.1` → `4.2` → `4.4` |
| 3 | tous les jalons cochés, `video/versions.json` sans version au tour 0 | **tournage** | `pipeline-step4.5` |
| 4 | tout est fait | **rien** : passe `avancement.json` en `fini` si ce n'est pas déjà le cas, rapport, sentinelle | — |

**Sans outil de tournage** (`echo $WEBAPP_VIDEO` rend `0`) : le cas 3 n'existe pas. Tous les jalons
cochés = cas 4 ; le contrôle de fin d'étape ne demande alors ni `video/` ni version de vidéo, et un
tour de retours se clôt sans refilmer.

Un jalon au statut `en-cours` dans `avancement.json` est un jalon qu'un lancement précédent n'a
pas fini : reprends-le où son journal s'arrête (dernier cycle écrit), ne recommence pas de zéro.

## 2. `docs/pipeline/avancement.json` — tu le tiens à CHAQUE transition

C'est ce que lisent `webapp-etat.py` et le module `/webapp` pour montrer à l'opérateur où en est la
construction. Format clos (le contrôle refuse tout autre) :

```json
{"phase": "jalons", "tour": 0, "jalon_courant": "M2",
 "jalons": [{"id": "M1", "titre": "Les prix autour de moi", "statut": "fait"},
            {"id": "M2", "titre": "Le coût d'un trajet", "statut": "en-cours"}],
 "maj": "2026-10-24T09:30:00Z"}
```

• `phase` : `jalons` pendant la construction, `tournage` pendant la vidéo, `retours` pendant un
  tour de retours, `fini` quand l'unité de travail laisse tout livré (tous jalons faits, vidéo
  publiée, aucun tour en attente).
• `tour` : le numéro du dernier tour de retours ouvert (0 avant toute revue). En mode retours,
  c'est le N du tour que tu traites.
• `jalons` : TOUS les jalons de `roadmap-approved.json`, dans l'ordre, `id` = `M<n>`, statut
  `a-faire` | `en-cours` | `fait`. Un jalon n'est `fait` que coché dans `status.md`.
• `bloque` (optionnel) : une phrase, quand tu t'arrêtes sur un blocage que le lancement suivant
  ne lèvera pas seul (3 cycles refusés, clé absente qui empêche tout le jalon, tournage en
  échec deux fois). Le lanceur ne relance pas une run bloquée : la phrase est ce que l'opérateur
  lira. Efface-la (`null`) dès que tu repars.
• `maj` : l'heure ISO de l'écriture.

Transitions à écrire : au démarrage (jalon → `en-cours`, `jalon_courant`), à la fin du jalon
(`fait`, `jalon_courant` = le suivant ou `null`), à l'entrée et à la sortie du tournage et d'un
tour de retours. Écris-le d'un bloc (fichier temporaire puis `mv`), jamais à moitié.

## 3. Le chef ne code pas

Tu ne touches jamais au code de l'app. Tu :
• prépares le jalon (journal, plan de cas d'usage, serveur de dev) ;
• dispatches des **sous-agents frais** avec l'outil Task (Agent) — un bâtisseur, puis un
  vérificateur qui n'a rien construit ; chaque nouveau cycle = de nouveaux agents ;
• routes l'information (les écarts du vérificateur vont au bâtisseur suivant, mot pour mot) ;
• tiens `status.md`, `avancement.json`, `project-memory.md`, le journal, les commits.

La session n'a pas de serveur MCP : les agents pilotent le navigateur avec la **bibliothèque
Playwright** (`npx playwright` / `import { chromium } from 'playwright'`), jamais `browser_*`.
Tout travail lourd en CPU (build, suite Playwright complète) est préfixé par `$WEBAPP_LIMITEUR` s'il est défini (limiteur de CPU de la machine, ex. `nice -n 10`).

Dans le prompt de CHAQUE sous-agent, ajoute ces règles (à propager s'il en lance d'autres) :
« Face à toute erreur ou incertitude, cherche en ligne d'abord (WebSearch/WebFetch) avant de
deviner. Personne ne répond aux questions : tranche, et écris pourquoi. Rends un résumé court,
résultat d'abord. »

## 4. Mode jalon — le cycle

Le jalon N = le premier non coché. Ses écrans, ses histoires, sa démo sont dans
`roadmap-approved.json` (`milestones[]` : `ecrans`, `stories`, `demo`, `use_case`).

### Préparer
1. `avancement.json` : jalon N → `en-cours`, `phase: jalons`.
2. Plan de cas d'usage `tests/e2e/use-cases/m{N}-use-case.md` : s'il manque, écris-le — il suit,
   dans l'ordre, les étapes de `parcours-utilisateur.json` dont l'écran appartient au jalon, puis
   les histoires du jalon qu'aucun parcours ne porte.
3. Journal `docs/pipeline/m{N}-journal.md` : crée-le (ou reprends-le) avec un en-tête
   `# Jalon N — <titre>` et une chronologie horodatée.
4. Serveur de dev si besoin : `npx vite --port 5199`.

### Cycle K (K = 1, 2, 3)

```
bâtisseur (4.1) → vérificateur indépendant (4.2)
    FAIL → cycle K+1 : nouveau bâtisseur avec la liste des écarts, puis NOUVEAU vérificateur
    PASS → tests, commit, mise en production (4.4) → jalon fait
```

• Charge le sous-skill (outil Skill) **avant** de dispatcher l'agent qu'il décrit.
• Le journal porte, pour chaque cycle, `## Bâtisseur — cycle K` (résumé du bâtisseur) puis
  `## Vérificateur — cycle K` suivi **immédiatement** de la ligne `Verdict : PASS` ou
  `Verdict : FAIL` — c'est le vérificateur qui l'écrit, pas toi. Le contrôle lit le DERNIER
  verdict du vérificateur de chaque jalon coché.
• Au bout de 3 cycles refusés : n'insiste pas. Le jalon reste `en-cours`, tu écris la liste des
  écarts restants dans le journal et dans `status.md` (une ligne), `avancement.json.bloque` =
  « m{N} : 3 cycles refusés — <écart principal> », rapport, sentinelle.

### Clore le jalon (après le PASS et la mise en production de 4.4)
1. `status.md` : `- [x] Milestone N — <titre> (journal : docs/pipeline/m{N}-journal.md)`.
2. `avancement.json` : jalon N → `fait`, `jalon_courant` = le suivant (ou `null`), `phase`
   reste `jalons` (le tournage est un autre lancement).
3. `project-memory.md` réécrit (≤ 2000 caractères) : ce qui est construit, décisions, URL.
4. Rapport de passe, sentinelle. Le lanceur relance pour le jalon suivant.

## 5. Mode tournage — `pipeline-step4.5`
## 6. Mode retours — `pipeline-step4.3`

## 7. Résilience des API externes

Quand l'app appelle des services tiers : sérialiser les requêtes vers les API à quota, utiliser
les miroirs quand il y en a, valider le format avant de parser, réduire la portée d'une requête
trop grosse. Décisions dans `docs/pipeline/m{N}-decisions.md`.

## 8. Hors de ce nœud

Deux agents par cycle, pas davantage : le vérificateur indépendant est le seul juge du jalon.
Ni audit de durcissement ni documentation finale : la vidéo et l'app en ligne sont le livrable,
la revue du client (nœud `revue`) juge.
