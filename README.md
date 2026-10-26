# webapp-pipeline

> **In short (English)**: a three-step agent pipeline that turns a client's idea into a deployed web app — design the
> app in conversation with the client (spec, user journeys, user stories, clickable mockup tested by the client),
> build it milestone by milestone with an independent verifier agent, then review it with the client until they say
> "good". It runs on the [flux](#le-moteur-flux) pipeline engine and Claude Code. Docs are in French.

Une pipeline d'agents en trois étapes qui transforme l'idée d'un client en application web en ligne.

| # | Étape | Mode | Contrôle de fin d'étape |
|---|---|---|---|
| 1 | **Concevoir** | en conversation, avec le client | `webapp-concevoir` |
| 2 | **Construire** (+ vidéo, optionnelle) | autonome, sur un serveur, relancée jusqu'au vert | `webapp-construire` |
| 3 | **Revue** du client | en conversation (barrière humaine) | `webapp-revue` |

1. **Concevoir** : pitch, questions d'usage (une à la fois, réponses A/B/C + une option ouverte), cahier des charges,
   parcours utilisateur, user stories dérivées du parcours, maquette cliquable avec son panneau d'histoires, **test de
   la maquette par le client**, puis spécification, feuille de route et pré-vol sans question.
2. **Construire** : un jalon par lancement — un agent bâtisseur construit les écrans du jalon, un **vérificateur
   indépendant** (agent neuf, qui n'a rien construit) rejoue chaque histoire sur l'app déployée et rend PASS ou FAIL,
   puis tests, commit, mise en production. Une fois tous les jalons faits : la vidéo de démonstration, si un outil de
   tournage est branché.
3. **Revue** : le client teste l'app (et regarde la vidéo). « Good » clôt la run ; ses retours, gardés mot pour mot,
   deviennent des points vérifiables et la construction repart sur ces seuls points.

Chaque étape a un **contrôle automatique** (`validators/`) qui juge ses livrables : tant qu'il est rouge, l'étape
suivante ne démarre pas.

## Contenu du dépôt

| Dossier | Ce qu'il contient |
|---|---|
| `workflows/` | les graphes : `webapp.json` (les 3 nœuds) et `webapp-design.json` (le seul nœud « concevoir », régénéré par `tools/sync-webapp-design.py`) |
| `skills/` | les consignes des agents, une par dossier (`<nom>/SKILL.md`) : `pipeline-step1` à `pipeline-step4.5`, `pipeline-revue`, `pipeline-status`, `webapp-start` |
| `validators/` | les contrôles de fin d'étape (`webapp_concevoir.py`, `webapp_construire.py`, `webapp_revue.py` et les moments qu'ils appellent) |
| `tools/` | le lanceur de l'étape 2 (`webapp-lancer.py`), son état (`webapp-etat.py`), la publication de la maquette (`publier-design.sh`), le tournage optionnel (`webapp-tourner.py`, `webapp-sonde.mjs`) |
| `mod/` | un mod de Claude Code : volet de suivi, bande au-dessus de l'invite, décisions du client gardées mot pour mot (`/webapp <projet>`) |
| `docs/` | le design des 3 étapes et le contrat des fichiers entre graphe, outils et module |
| `exemple/` | `demo.sh` : démonstration de bout en bout sans compte |
| `tests/` | tests du lanceur, de l'état et des contrôles |
| `legacy/` | anciennes étapes « durcissement » et « livraison » (`pipeline-step5/6`), hors du graphe |

## Le moteur flux

La pipeline ne tourne pas seule : elle est jouée par **flux**, un moteur de pipelines d'agents (dépôt séparé du même
auteur, licence Apache 2.0). Il lit les graphes, injecte les consignes, lance les agents dans des sessions Claude Code
et passe les contrôles. Ce dépôt ne le recopie pas : clonez-le dans `vendor/flux` (ou ailleurs, et indiquez son
chemin dans `FLUX_HOME`).

## Installer

Prérequis : Linux ou macOS, `git`, Python 3.10+, `pip`. Pour lancer de vrais agents : `tmux` et Claude Code connecté
à un compte.

```bash
git clone <adresse de webapp-pipeline> webapp-pipeline
cd webapp-pipeline
git clone <adresse de flux> vendor/flux            # le moteur (voir son propre README)
python3 -m pip install -r vendor/flux/requirements.txt   # jsonschema
cp .env.example .env                               # puis adapter les chemins et adresses
set -a; . ./.env; set +a
```

Vérifier l'installation :

```bash
python3 "$FLUX_HOME/runtime/verifier-graphes.py" workflows/*.json   # → GRAPHES CONFORMES
FLUX_HOME="$FLUX_HOME" python3 -m unittest discover -s tests         # tests du lanceur et des contrôles
python3 -m unittest discover -s mod/programme/tests                  # tests du programme du module
bash exemple/demo.sh                                                 # démonstration de bout en bout
```

`exemple/demo.sh` crée une run « covoiturage-facile » (projet inventé), écrit le brief du nœud « concevoir » avec
ses consignes, montre le contrôle de l'étape 1 rouge sur une run vide, puis vert pour les contrôles des étapes sur
une run finie d'exemple, lit l'état de la construction et demande au lanceur ce qu'il ferait. **Tout cela tourne sans
compte.** La suite — la conversation de conception et les agents de construction — exige Claude Code connecté.

## Utiliser

1. **Nouvelle run** : dans Claude Code, avec le mod, `/webapp <projet>` ; sans le mod, le skill `/webapp-start`
   (création par `python3 $FLUX_HOME/runtime/new-run.py webapp '<projet>'`).
2. **Concevoir** avec le client dans la même session. La maquette est publiée en HTTP par
   `tools/publier-design.sh` (réglages `DESIGN_PUBLISH_DIR`, `PUBLIC_BASE_URL`) pour que le client l'ouvre sans compte.
3. **Construire** : `python3 tools/webapp-lancer.py <workspace>` lance l'étape 2 en détaché et la relance jusqu'au
   contrôle vert ; `python3 tools/webapp-etat.py <workspace>` dit où elle en est (une ligne JSON).
4. **Revue** : skill `pipeline-revue` (ou le volet du mod) ; des retours relancent la construction sur ces seuls points.

## Réglages

Tout ce qui dépend de la machine passe par des variables d'environnement, listées avec des valeurs d'exemple dans
`.env.example` : emplacement du moteur et des runs, compte des agents (`WEBAPP_MOTEUR`, un moteur de `moteurs.json`
de flux), fichier des jetons Supabase et Vercel (`WEBAPP_STACK_ENV`, **hors dépôt**), publication de la maquette,
vidéo (`WEBAPP_VIDEO=0` par défaut), hôte SSH du serveur des runs.

La pile imposée aux applis construites est React + Vite, Supabase, Vercel : un compte Supabase et un compte Vercel
servent tous les projets. Leurs jetons ne vont jamais dans un dépôt ; chaque appli reçoit ses propres clés dans son
`.env.local`, ignoré par git.

## Vidéo de démonstration (optionnelle)

`tools/webapp-tourner.py` écrit le texte de chaque séquence avec un agent, génère la voix, filme l'app en ligne et
publie une table de montage. Il exige un outil de tournage externe, **non fourni** ici (`TOURNAGE_MOD_HOME`,
`TOURNAGE_SKILL_HOME`). Sans lui, laissez `WEBAPP_VIDEO=0` : les contrôles ne demandent alors aucune vidéo et le
client fait sa revue sur l'app seule.

## Licences

- **Code** (Python, JavaScript, TypeScript, shell, graphes JSON) : [Apache 2.0](LICENSE), voir [NOTICE](NOTICE).
- **Textes, documents et schémas** (consignes `skills/*/SKILL.md`, `docs/`, `legacy/`, README, textes des graphes) :
  [CC BY 4.0](LICENSE-docs). Vous pouvez les réutiliser et les adapter en citant l'auteur, Anthony Hunt.
- Dépendances tierces et leurs licences : [THIRD-PARTY.md](THIRD-PARTY.md).

Auteur : Anthony Hunt.
