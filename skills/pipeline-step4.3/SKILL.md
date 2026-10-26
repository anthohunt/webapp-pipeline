---
name: pipeline-step4.3
description: Le mode retours de l'étape « Construire » (web app en 3 étapes) — traite le plus ancien `docs/pipeline/retours/tour-<N>.json` au statut `a-traiter` : corriger chaque retour, vérifier chaque `attendu` par un vérificateur frais, remettre en production, refilmer seulement les séquences touchées, figer la version V<N+1>, passer le tour à `traite`. Sous-skill de pipeline-step4.
---

# Pipeline Step 4.3 — Mode retours

**Appelé par :** le chef (pipeline-step4 §1, cas 1) quand un tour de retours attend.
**Entrée :** `docs/pipeline/retours/tour-<N>.json` (écrit à la revue, nœud `revue`, à partir des
mots du client rapportés par l'opérateur) :

```json
{"tour": 1, "date": "…", "statut": "a-traiter", "citation": "<mots de l'opérateur>",
 "retours": [{"id": "R1", "dit": "<mots exacts>", "histoire": "US-2.1", "ecran": "S3",
              "attendu": "<critère vérifiable>"}]}
```

**Sortie :** l'app corrigée en production, la vidéo V<N+1> qui ne refilme que les séquences
touchées, `tour-<N>.json` au statut `traite`, `avancement.json` en `fini` au tour N.

Un tour de retours = un lancement. Un seul tour à la fois, le plus petit N encore `a-traiter`.

---

## 1. Ouvrir le tour

1. `avancement.json` : `phase: "retours"`, `tour: N`, `bloque: null`, `maj`.
2. Journal du tour : `docs/pipeline/retours/tour-<N>-journal.md` (`# Tour N — retours du client`,
   la citation de l'opérateur, la liste des retours).
3. Lis chaque retour : `dit` est la parole du client, `attendu` est ce qui sera vérifié. Tu ne
   réinterprètes pas : si `attendu` et `dit` semblent diverger, c'est `attendu` qui se vérifie,
   et tu notes la divergence dans le journal (la revue suivante la tranchera).

## 2. Cycle K (K = 1, 2, 3) — le même qu'un jalon

```
bâtisseur (4.1, variante retours) → vérificateur frais (4.2, mode retours)
    FAIL → cycle K+1 avec les écarts mot pour mot
    PASS → tests, commit, production (4.4)
```

• **Bâtisseur** : gabarit 4.1, avec à la place des histoires du jalon la liste des retours
  (`id`, `dit`, `histoire`, `ecran`, `attendu`). Il corrige, rejoue les écrans touchés, déploie
  une préversion et écrit son URL dans `docs/pipeline/retours/tour-<N>-preview-url.txt`. Il
  rend aussi la **liste des écrans réellement modifiés** (ids de `screens.json`) : un retour
  sans écran (« les couleurs sont tristes ») en touche souvent plusieurs.
• **Vérificateur** : gabarit 4.2, section « Mode retours » ; verdict dans le journal du tour.
• Un retour qui change le périmètre (nouvel écran, nouvelle fonction absente de la maquette)
  se construit quand même s'il tient dans l'app — c'est le client qui l'a demandé ; écris dans
  le journal ce qu'il ajoute. Une histoire nouvelle s'ajoute à `stories.json` (id neuf,
  `parcours` renseigné si un parcours la traverse).
• Trois cycles refusés : `avancement.json.bloque` = « tour N : <retour non tenu> », le tour reste
  `a-traiter`, rapport, sentinelle.

## 3. Remettre en production — `pipeline-step4.4`

Régression complète, commit (`fix(retours-N): …`), production, contrôle HTTP, `app-url.txt`.

## 4. Refilmer les séquences touchées

**Sans outil de tournage** (`WEBAPP_VIDEO=0`) : saute cette section ; le tour se clôt sans version de vidéo.

La séquence `s<k>` filme le parcours de rang k de `parcours-utilisateur.json` (P1 → s1, P2 → s2…).
Une séquence est touchée si son parcours a une étape dont l'`ecran` est dans les écrans
touchés, ou dont les `stories` croisent les histoires touchées. Écrans touchés = les `ecran` des
retours + les écrans réellement modifiés rendus par le bâtisseur. Histoires touchées = les
`histoire` des retours.

```bash
python3 $WEBAPP_PIPELINE_HOME/tools/webapp-tourner.py <workspace> --tour N --sequences s1,s3
```

• Lance-le comme au tournage initial (`pipeline-step4.5` §2 : détaché, attendu au premier plan sans rendre la main,
  lire la dernière ligne JSON).
• Aucune séquence touchée (correction invisible à l'écran, rare) : passe quand même toutes les
  séquences du parcours le plus proche du retour — chaque tour doit avoir sa version de vidéo,
  le client revoit une vidéo à chaque revue.
• Le script fige `V<N+1>` et met à jour `video/versions.json` et `video/video-url.txt`.
  Vérifie-le : `versions.json` porte une version au tour N, `refilmees` = ce que tu as demandé.

## 5. Clore le tour

1. `tour-<N>.json` : `statut: "traite"`, ajoute `traite_le` (ISO) et `version` (« V<N+1> ») —
   ne touche à aucun autre champ, surtout pas `dit` ni `citation`.
2. `tour-<N>.md` : ajoute en fin `Traité le … — version V<N+1>, séquences refilmées : …`.
3. `avancement.json` : `phase: "fini"`, `tour: N`, `jalon_courant: null`, `maj`.
4. `project-memory.md` : une ligne sur ce que le tour a changé.
5. Rapport de passe, sentinelle. La revue suivante se joue en conversation (nœud `revue`).
