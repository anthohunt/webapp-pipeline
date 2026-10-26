---
name: pipeline-revue
description: Étape 3 « Revue » de la pipeline web app (nœud `revue`, en conversation) — le client regarde la vidéo et teste l'app avec l'opérateur ; transformer les mots du client, rapportés par l'opérateur, en verdict (`good` clôt la run) ou en un tour de retours vérifiables (`docs/pipeline/retours/tour-N.json`), une question à la fois, citations mot pour mot, puis relancer la construction sur ces seuls points. PAS un skill de construction : rien ne se code dans cette session.
---

# Pipeline Revue — le verdict du client

Nœud `revue` du graphe `webapp`, la barrière humaine de fin. Le client regarde la vidéo de
démonstration et teste l'app en ligne ; il parle à l'opérateur, et c'est **l'opérateur** qui te
rapporte ce qu'il dit. Ton travail : garder ces mots tels quels, et en faire des points qu'un
agent de construction pourra corriger puis **vérifier** sur l'app, sans avoir à interpréter.

Contrat : `$WEBAPP_PIPELINE_HOME/docs/2026-10-24-webapp-3-etapes-contrat.md` (étape 3). Gate :
`webapp-revue`.

## 0. Où tu es

• **Normal : dans le module `/webapp <projet>`.** Les outils du module `retours` et `revue`
  écrivent `revue.json` et `retours/tour-N.json/.md` au contrat et relancent la construction
  eux-mêmes. Tu n'écris pas ces fichiers à la main.
• **Sans le module** (session ouverte par `flux-local webapp revue`, ou à la main) : tu écris
  les mêmes fichiers toi-même (§5), puis tu lances la commande du serveur.

## 1. Donner les deux liens

Lis-les, ne les recompose pas :
• la vidéo : `video/video-url.txt` (table de montage, avec son `?code=` : c'est la clé du client)
  et la version courante (dernière entrée de `video/versions.json`) ;
• l'app : `docs/pipeline/app-url.txt`.

Une ligne chacun, copiables. Rien d'autre : l'opérateur et le client regardent.

## 2. Recueillir le verdict, mot pour mot

Attends ce que l'opérateur rapporte. La **citation** est son message exact (copié, jamais résumé,
jamais corrigé — fautes comprises).

• Le client dit sans réserve que c'est bon → verdict `good`. Une phrase qui mêle « c'est bien »
  et une demande (« super, mais le bouton est trop petit ») est un verdict `retours`.
• Doute sur le verdict → une seule question : « A — c'est bon, on clôt ; B — il y a des retours
  à corriger ; C — autre chose, précise-moi. »

## 3. Un retour = un point vérifiable — une question à la fois

D'abord, renvoie la liste de ce que tu as entendu, numérotée, une ligne par retour, avec le
mot du client entre guillemets. Puis, **un retour à la fois** :

1. `dit` : le passage exact du message de l'opérateur qui porte ce retour (extrait mot pour mot).
2. `ecran` et `histoire` : cherche-les toi-même dans `design/screens.json`, `stories.json` et
   `parcours-utilisateur.json` (l'écran dont parle le client, l'histoire du geste). `null` si le
   retour est global (« les couleurs sont tristes ») — ne force pas un rattachement faux.
3. `attendu` : un critère qu'un agent peut constater sur l'app, à l'écran — « sur S2, le prix
   du produit est le premier élément, en caractères d'au moins 20 px », pas « plus lisible ».
   Propose-le en A/B/C, avec une option D ouverte (« autre chose, précise-moi ») ; ce que l'opérateur
   choisit ou écrit devient l'`attendu`, avec ses mots quand il en donne.
4. Le retour est clair et l'attendu évident ? Ne pose pas de question pour rien : énonce
   l'attendu en une ligne et passe au suivant ; l'opérateur te corrigera.

Jamais deux questions dans un message. Jamais un retour inventé, ni un retour « en passant »
que le client n'a pas fait. Un retour qui demande un nouvel écran ou une nouvelle fonction
reste un retour : la construction le bâtira.

## 4. Écrire le tour, puis relancer

Dans le module :
1. outil `retours` : la liste `[{dit, attendu, histoire, ecran}]` + `citation` (le message
   de l'opérateur qui transmet les retours) → écrit `docs/pipeline/retours/tour-N.json` et `.md`
   (statut `a-traiter`) ;
2. outil `revue` : `verdict: "retours"` + `citation` → écrit `revue.json` et relance la
   construction toute seule, en mode retours (`webapp-lancer.py`).
Verdict `good` : outil `revue` `verdict: "good"` + `citation` → la run est close.

Dis ensuite en une ligne ce qui se passe : « la construction repart sur N points ; la vidéo V<k+1>
ne refilmera que les séquences touchées » ou « run close ».

## 5. Sans le module — les fichiers au contrat

N = (nombre de tours déjà dans `revue.json`) + 1.

`docs/pipeline/retours/tour-N.json` (seulement pour un verdict `retours`) :
```json
{"tour": N, "date": "<ISO>", "statut": "a-traiter", "citation": "<message de l'opérateur>",
 "retours": [{"id": "R1", "dit": "<mots exacts>", "histoire": "US-x.y", "ecran": "S2",
              "attendu": "<critère vérifiable>"}]}
```
`docs/pipeline/retours/tour-N.md` : la même liste, lisible (`## R1 · US-x.y · écran S2`, puis
`• Dit : « … »` et `• Attendu : …`).

`docs/pipeline/revue.json` — ajoute le tour, n'efface jamais les précédents :
```json
{"tours": [{"tour": N, "verdict": "good"|"retours", "date": "<ISO>",
            "citation": "<mots exacts de l'opérateur>", "version_video": "V<k>"}]}
```

Puis :
• `retours` → `python3 $WEBAPP_PIPELINE_HOME/tools/webapp-lancer.py <workspace>` (une ligne JSON :
  `{"ok": true, "mode": "retours", …}` ; un refus dit pourquoi) ;
• `good` → `python3 $FLUX_HOME/runtime/run-node.py webapp revue --workspace <workspace>`
  (le gate `webapp-revue` constate le verdict).

## Règles

• Citations mot pour mot, toujours : `citation` et `dit` ne se reformulent pas.
• Une question à la fois, chaque question à choix avec une option ouverte.
• Rien ne se code ici : la correction appartient au nœud `construire`.
• Le gate refuse : un tour sans citation, un retour sans `attendu`, un `histoire`/`ecran` qui
  n'existe pas, un tour joué sans vidéo du tour précédent, un tour après un `good`.
