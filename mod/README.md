# Web app — module Claude Code

Conduit une run de la pipeline web app en 3 étapes, du pitch au « good » du client (design :
`docs/2026-10-24-webapp-3-etapes-design.md` ; fichiers et commandes : `docs/2026-10-24-webapp-3-etapes-contrat.md`,
à la racine du dépôt).

1. **Concevoir**, en conversation (avec le client à côté) : pitch, questions d'usage, cahier des charges, parcours
   utilisateur, user stories, maquette cliquable, test de la maquette par le client, puis la spécification seule.
2. **Construire**, sur le serveur : un groupe d'écrans à la fois (un constructeur, un vérificateur indépendant),
   puis, si un outil de tournage est branché (optionnel), la vidéo de démonstration publiée sur la table de montage.
3. **Revue** : le client regarde la vidéo et teste l'app. « Good » clôt la run ; ses retours relancent la
   construction sur ces seuls points, et la vidéo passe à la version suivante.

## Utiliser

Installer le mod dans Claude Code depuis le dossier `mod/` (les mods de Claude Code sont en accès anticipé : leur API
peut changer). Deux réglages : `programme` (chemin de `mod/programme/webapp.py` sur le serveur des runs) et `hote`
(`utilisateur@machine`, quand la session ne tourne pas sur ce serveur).

Dans une session Claude Code : `/webapp <projet>`. Le volet s'ouvre à droite, la
bande au-dessus de l'invite dit où on en est et ce qui t'attend. Le message suivant est le pitch. `/webapp` seul
rouvre le volet ; `/webapp off` détache la session.

Le volet : ce qui t'attend en tête (avec le bouton « Lancer la construction » / « Relancer », ou « C'est bon » /
« Il a des retours » pendant la revue), les liens maquette, app et vidéo (copiables pour le client), puis les 3 étapes
et leurs sous-étapes ; pendant la construction, les jalons un par un.

## Comment c'est fait

- `programme/webapp.py` : l'état de la run, dans ses fichiers (`<run>/state/module-webapp.json`, journal
  `module-webapp.jsonl`, `docs/pipeline/revue.json`, `docs/pipeline/retours/tour-N.json`). Il parle au moteur flux :
  création de la run (`runtime/new-run.py`), brief et gate du nœud 1 (`runtime/run-node.py`), lancement et suivi de
  l'étape 2 (`tools/webapp-lancer.py`, `tools/webapp-etat.py`). Une commande par geste, JSON sur l'entrée standard.
  Tests : `python3 -m unittest discover -s programme/tests` (faux moteur flux dans un dossier temporaire).
- `programme/parcours.json` : les étapes, sous-étapes, sorties et consignes de l'agent. Rien de propre à une run.
- `hooks/` : le mod (volet, bande, consignes et outils de la seule session rattachée ; le programme est joint
  en local sur le serveur des runs, par SSH ailleurs). Tests : `claude plugin test .` (vues fabriquées par le vrai programme :
  `python3 tests/fabriquer-fixtures.py`). Les types de l'API des mods (`.claude-plugin/types/`) sont générés par
  Claude Code et ne sont pas fournis ici.
