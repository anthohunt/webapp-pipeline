---
name: webapp-start
description: Ouvre ou reprend une run de la pipeline « web app » (flux `webapp`, 3 étapes : concevoir → construire avec vidéo → revue du client) quand le module `/webapp` n'est pas là. Déclencheurs — « /webapp-start », « nouvelle app », « on construit une web app », « reprends la run webapp », « joue le nœud concevoir ». Point d'entrée normal : le module `/webapp <projet>`. Ce skill est le chemin de secours (session sur une autre machine via flux-local, ou reprise à la main).
---

# webapp-start — entrer dans la pipeline web app

## Le point d'entrée normal est le module `/webapp <projet>`

Une run web app se mène dans une session Claude Code sur le serveur des runs (ou reliée à lui
par SSH) avec la commande du module : **`/webapp <projet>`**. Le module crée ou reprend
la run, ouvre le volet (où on en est, ce qui t'attend, liens maquette / app / vidéo), garde le
pitch mot pour mot, avance les sous-étapes, passe le gate de l'étape 1, lance la construction et
enregistre la revue. Source : `$WEBAPP_PIPELINE_HOME/mod` (README).

**Si `/webapp` existe dans la session, utilise-le et arrête-toi ici.** Ce skill sert quand le
module n'est pas là : session sur une autre machine (`flux-local`), poste qui ne fait que
concevoir (`webapp-design`), ou reprise à la main d'une run.

## La pipeline : trois étapes

| # | Nœud | Mode | Gate |
|---|---|---|---|
| 1 | **Concevoir** | INTERACTIF, en conversation avec le client | `webapp-concevoir` |
| 2 | **Construire** (+ vidéo) | autonome, serveur, relancé par `webapp-lancer` | `webapp-construire` |
| 3 | **Revue** du client | en conversation (barrière humaine) | `webapp-revue` |

• **Concevoir** : pitch → questions d'usage → cahier des charges → parcours utilisateur →
  histoires dérivées du parcours → mockup dual-layer → **test du mockup par le client** →
  spécification et pré-vol (sans question). Protocoles `pipeline-step1/2/3`.
• **Construire** : un jalon par lancement (bâtisseur → vérificateur indépendant → tests, commit,
  production), puis la vidéo de démonstration (une séquence par parcours, V1 figée, table de
  montage publiée). Protocoles `pipeline-step4` et `4.1`→`4.5`.
• **Revue** : le client regarde la vidéo et teste l'app. « Good » clôt la run ; ses retours,
  rapportés par l'opérateur, deviennent un tour de points vérifiables et la construction repart sur
  ces seuls points (vidéo V2, V3… qui ne refilme que les séquences touchées). Protocole
  `pipeline-revue`.

Durcissement et livraison documentaire (`pipeline-step5/6`) ne font pas partie du graphe.

## Deux flux, un même nœud

| Flux | Ce qu'il contient | Pour qui |
|---|---|---|
| `webapp` | les 3 nœuds — du pitch au « good » du client | le projet mené de bout en bout |
| `webapp-design` | le seul nœud `concevoir`, sur ses propres runs | qui ne fait QUE concevoir |

`webapp-design` est régénéré depuis le nœud `concevoir` de `webapp` par
`$WEBAPP_PIPELINE_HOME/tools/sync-webapp-design.py` : toute retouche se fait dans `webapp.json`,
puis on relance ce script. Ses runs vivent sous `~/webapp-design-runs`.

## Déroulé (sans le module)

### 0. Résoudre le FLUX

**Sur un poste partagé qui ne fait que concevoir, le flux est `webapp-design`** : on y conçoit,
on n'y construit pas ; prendre `webapp` y ferait tomber sur la run d'un autre projet. Le nom du
flux se substitue à `webapp` dans toutes les commandes ci-dessous.

### 1. Résoudre la run

```bash
flux-local webapp          # liste les nœuds et leur état, nomme la run active
```

• Nouveau projet → créer la run (slug = le projet, jamais un horodatage seul) :
  ```bash
  ssh $WEBAPP_HOTE "python3 $FLUX_HOME/runtime/new-run.py webapp '<nom du projet>'"
  ```
  (sur le serveur des runs lui-même : la commande sans `ssh`). La run la plus récente devient la run active.
• Run existante que l'opérateur reprend → la garder.

### 2. Rapatrier le workspace et sortir le brief

```bash
flux-local webapp concevoir
```

Copie le workspace sous `~/flux-runs/<run>/`, écrit `.flux/concevoir/brief.md` (objectif,
check-list imposée, livrables) et `.flux/concevoir/sys.md` (protocoles `pipeline-step1/2/3`).
**Lis les deux en entier avant de parler** ; la première ligne du brief demande un `TodoWrite`
reprenant ses items dans l'ordre.

### 3. Jouer l'étape 1

Le premier message de l'opérateur après ce chargement EST le pitch — ne demande pas « tu veux
construire quoi ». Puis les moments de `sys.md`, d'une traite : questions d'usage (A/B/C + une
option ouverte écrite, une à la fois), cahier des charges, parcours, histoires, mockup publié
aussi en HTTP (`$WEBAPP_PIPELINE_HOME/tools/publier-design.sh <workspace>` → `mockup-public-url.txt`), **test par le client**
(on corrige et on republie dans la foulée), puis spécification et pré-vol sans question.

### 4. Renvoyer et passer le gate

```bash
flux-local webapp concevoir --push
```

Le gate `webapp-concevoir` appelle les validateurs de moments et préfixe chaque défaut
(`[cadrage]`, `[parcours]`, `[mockup]`, `[test du client]`, `[spécification]`, `[pré-vol]`).
**Rouge = on corrige et on repousse**, dans la même session. Au vert, `flux-local` affiche la
banderole de fin d'étape (libellé du graphe) : ne la recopie pas à la main.

### 5. Lancer la construction (serveur)

```bash
ssh $WEBAPP_HOTE "python3 $WEBAPP_PIPELINE_HOME/tools/webapp-lancer.py $WEBAPP_RUNS/<run>"
ssh $WEBAPP_HOTE "python3 $WEBAPP_PIPELINE_HOME/tools/webapp-etat.py $WEBAPP_RUNS/<run>"
```

`webapp-lancer` lance `construire` en détaché sur le compte des agents de construction (moteur
`WEBAPP_MOTEUR`, sinon le `defaut` de `moteurs.json`) et le relance jusqu'au gate vert — un lancement = un jalon, puis le tournage ; il refuse
si la construction tourne déjà et repart en mode retours s'il trouve un tour `a-traiter`.
`--dry-run` dit ce qu'il ferait sans rien lancer. `webapp-etat` rend une ligne JSON (phase,
jalons, liens app et vidéo, blocage éventuel).

### 6. La revue

Quand `webapp-etat` dit `phase: fini` avec une vidéo : skill `pipeline-revue` (ou
`flux-local webapp revue`), en conversation avec l'opérateur et son client.

## Ce qu'il ne faut pas faire

• **Lancer un nœud interactif depuis le flux** : personne ne répondrait.
• **Travailler directement dans le workspace du serveur depuis une autre machine** : on rapatrie, on
  travaille, on renvoie.
• **Poser une question après le test du mockup** : la suite se tranche et se justifie par écrit.
• **Lancer `run-node.py webapp construire` à la main** : sans le lanceur, rien ne le relance
  après le premier jalon, et le moteur n'est pas forcément celui des agents de construction.

## Références

• Graphe : `$WEBAPP_PIPELINE_HOME/workflows/webapp.json` (la vérité exécutable)
• Contrat des fichiers : `$WEBAPP_PIPELINE_HOME/docs/2026-10-24-webapp-3-etapes-contrat.md`
• Validateurs : `$WEBAPP_PIPELINE_HOME/validators/webapp_*.py`
• Module : `$WEBAPP_PIPELINE_HOME/mod`
