# Pipeline web app en 3 étapes — contrat entre le graphe, le tournage et le module (24/10/2026)

Design : `docs/2026-10-24-webapp-3-etapes-design.md`. Ce fichier fixe ce que chaque morceau lit et écrit,
pour que le graphe (`workflows/webapp.json` + skills `pipeline-step*`), le tournage automatique
(`tools/webapp-tourner.py`) et le module Claude Code (`$WEBAPP_PIPELINE_HOME/mod`) se branchent sans se
parler. Chemins relatifs au workspace de la run (`$WEBAPP_RUNS/<run>/`).

## Étape 1 — Concevoir (nœud `concevoir`, type `local`, interactif)

Livrables existants conservés (concept, design/, stories, roadmap-approved, kit…) PLUS :

| Fichier | Contenu |
| --- | --- |
| `docs/pipeline/cahier-des-charges.md` | but de l'app, utilisateurs, périmètre V1, hors périmètre, contraintes, sources de données |
| `docs/pipeline/parcours-utilisateur.json` | `{"parcours":[{"id":"P1","titre":"…","qui":"…","but":"…","etapes":[{"n":1,"ecran":"<id screens.json>","geste":"…","stories":["US-1.1"]}]}]}` — un parcours = un usage complet de bout en bout ; chaque étape nomme un écran de `design/screens.json` et les histoires qu'elle joue |
| `docs/pipeline/parcours-utilisateur.md` | la lecture humaine des mêmes parcours |

Le parcours utilisateur s'écrit **avant** les user stories (les histoires découlent du parcours) et **avant** le
mockup. Le panneau d'histoires du mockup peut grouper par parcours.

## Étape 2 — Construire (nœud `construire`, type `agent`, serveur)

Cycle par jalon : **bâtisseur** puis **vérificateur indépendant** (rejoue les histoires du jalon sur l'app
déployée, avec captures) ; puis tests, commit, déploiement. Plus d'évaluateur, de descripteur, d'auditeur ni de
contre-évaluateur. Une fois tous les jalons cochés : **tournage** (`tools/webapp-tourner.py`).

| Fichier | Contenu |
| --- | --- |
| `docs/pipeline/status.md` | jalons cochés (inchangé) |
| `docs/pipeline/avancement.json` | tenu à jour par le nœud à chaque transition : `{"phase":"jalons"\|"tournage"\|"fini"\|"retours","tour":0,"jalon_courant":"M2","jalons":[{"id":"M1","titre":"…","statut":"a-faire"\|"en-cours"\|"fait"}],"maj":"<ISO>"}` |
| `docs/pipeline/app-url.txt` | l'URL de production |
| `video/` | le projet du mod tournage (scénario `.texte.md`, `.yaml`, `clips/`, vidéo assemblée, `.tournage/`) |
| `video/video-url.txt` | le lien de la table de montage en ligne (avec `?code=`) |
| `video/versions.json` | `{"versions":[{"version":"V1","tour":0,"date":"<ISO>","sequences":["s1",…],"refilmees":["s1",…]}]}` |

## Étape 3 — Revue (nœud `revue`, type `local`, barrière humaine)

Le client regarde la vidéo et teste l'app ; ses retours arrivent **en conversation via l'opérateur**.

| Fichier | Contenu |
| --- | --- |
| `docs/pipeline/revue.json` | `{"tours":[{"tour":1,"verdict":"good"\|"retours","date":"<ISO>","citation":"<mots exacts de l'opérateur>"}]}` |
| `docs/pipeline/retours/tour-<N>.json` | `{"tour":N,"date":"<ISO>","statut":"a-traiter"\|"traite","retours":[{"id":"R1","dit":"<mots exacts>","histoire":"US-x.y"\|null,"ecran":"<id>"\|null,"attendu":"<critère vérifiable>"}]}` |
| `docs/pipeline/retours/tour-<N>.md` | la même liste, lisible |

Verdict `retours` → `construire` repart en **mode retours** : il traite le plus ancien `tour-<N>.json` au statut
`a-traiter` (corrige, vérifie chaque `attendu`, redéploie), refilme seulement les séquences dont un parcours
traverse un écran ou une histoire touchés, fige la version suivante (`V<N+1>`), passe le tour à `traite`.
Verdict `good` → la run est close.

## Commandes (serveur, sortie JSON sur stdout)

| Commande | Effet |
| --- | --- |
| `python3 $WEBAPP_PIPELINE_HOME/tools/webapp-lancer.py <ws>` | lance l'étape 2 (construction, ou tour de retours s'il y en a un `a-traiter`) en détaché ; refuse si elle tourne déjà ; `{"ok":true,"tmux":"…","mode":"construction"\|"retours"}` |
| `python3 $WEBAPP_PIPELINE_HOME/tools/webapp-etat.py <ws>` | `{"en_cours":bool,"phase":…,"tour":N,"jalons":[…],"app_url":…,"video":{"url":…,"version":…},"bloque":null\|"<raison>","derniere_passe":{…}}` |
| `python3 $WEBAPP_PIPELINE_HOME/tools/webapp-tourner.py <ws> [--tour N] [--sequences s1,s3]` | tournage complet (tour 0) ou partiel ; écrit `video/` comme ci-dessus |
