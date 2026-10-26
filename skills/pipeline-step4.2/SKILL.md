---
name: pipeline-step4.2
description: Le vérificateur indépendant (web app en 3 étapes) — agent FRAIS qui n'a rien construit, rejoue chaque histoire du jalon et chaque étape de parcours qui traverse ses écrans sur l'app DÉPLOYÉE, capture chaque étape dans `tests/e2e/verification/m{N}/`, et écrit lui-même son verdict PASS ou FAIL dans le journal. Remplace évaluateur, descripteur, auditeur et contre-évaluateur. Sous-skill de pipeline-step4 ; sert aussi au mode retours (4.3).
---

# Pipeline Step 4.2 — Le vérificateur indépendant

**Appelé par :** le chef (pipeline-step4), après chaque bâtisseur (4.1) — ou par le mode retours (4.3).
**Entrée :** l'URL déployée (la préversion du bâtisseur, `docs/pipeline/m{N}-preview-url.txt`),
les histoires du jalon, les parcours, le plan de cas d'usage, la maquette.
**Sortie :** des captures dans `tests/e2e/verification/m{N}/cycle{K}/`, un rapport, et le
verdict écrit dans le journal du jalon.

Pourquoi un seul agent : il prouve sur l'app réelle, à l'écran, ce que le bâtisseur affirme.
Il n'a rien construit et ne lit pas le transcript du bâtisseur : il ne peut pas être convaincu
par son récit, seulement par ce qu'il voit.

---

## Instructions du chef

Un vérificateur **neuf** par cycle (jamais celui du cycle précédent, jamais le bâtisseur) :

```
Task({ description: "m{N} vérificateur cycle {K}", subagent_type: "general-purpose",
       prompt: "..." })   // le gabarit ci-dessous, chaque {champ} rempli
```

Ne lui donne PAS le résumé du bâtisseur, seulement l'URL et les fichiers. À son retour :
lis la ligne `Verdict :` qu'il a écrite dans le journal (pas son message), et
• `PASS` → `pipeline-step4.4` (tests, commit, production) ;
• `FAIL` → cycle suivant : nouveau bâtisseur (4.1) avec sa liste d'écarts **mot pour mot**,
  puis nouveau vérificateur. Trois cycles au plus (cf. pipeline-step4 §4).

---

## Gabarit du prompt du vérificateur

```
Tu es le vérificateur indépendant du jalon {N}, cycle {K}. Tu n'as rien construit. Tu tournes
seul sur un serveur : personne ne répond aux questions — tranche, et écris pourquoi. Face à toute
erreur ou incertitude, cherche en ligne d'abord (WebSearch/WebFetch) avant de deviner. Rends un
résumé court, résultat d'abord. Travail lourd (suite Playwright) préfixé par `$WEBAPP_LIMITEUR` s'il est défini (limiteur de CPU de la machine).

## Ce que tu vérifies
- App déployée : {URL} — c'est la SEULE cible. Jamais localhost.
- Histoires du jalon (roadmap-approved.json) : {liste des ids}, texte et critères d'acceptation
  dans {projet}/docs/pipeline/stories.json et spec.md.
- Étapes de parcours qui traversent les écrans du jalon : {liste « P1.3 — écran S2 — geste »},
  depuis {projet}/docs/pipeline/parcours-utilisateur.json.
- Plan : {projet}/tests/e2e/use-cases/m{N}-use-case.md.
- Maquette (l'aspect et le comportement attendus) : {projet}/docs/pipeline/design/screens.json
  et {projet}/docs/pipeline/design/mockup-url.txt.
- Comptes de test : {projet}/docs/pipeline/config.json → testAccounts (s'il y en a).
- Fonctions non construites faute de clé : config.json → skippedFeatures (affectedStories) —
  ces histoires sont « NON CONSTRUITE (clé absente) », ni PASS ni FAIL, et ne te font pas refuser.

## Comment
1. Avec la bibliothèque Playwright (`import { chromium } from 'playwright'`, script sous
   {projet}/tests/e2e/verification/m{N}/cycle{K}/), jamais d'outil MCP (il n'y en a pas ici).
   Viewport du plan (téléphone 390×844 si l'app est mobile).
2. Rejoue d'abord les étapes de parcours, dans l'ordre, comme un utilisateur qui fait son usage
   de bout en bout ; puis chaque histoire du jalon, chemin nominal ET cas limites du plan.
3. Une capture par étape : {projet}/tests/e2e/verification/m{N}/cycle{K}/<US-x.y|P1.3>-<nn>-<quoi>.png,
   chacune issue d'un `page.screenshot()` distinct. Regarde chaque capture (outil Read) avant
   de conclure : un écran blanc, une erreur, un texte tronqué se voient sur l'image, pas dans
   le code.
4. Vrai backend : aucune interception `page.route()` sauf pour une panne qu'on ne peut pas
   provoquer (fournisseur tiers en panne, délai > 30 s) — alors écris `SIMULÉ : <pourquoi>`.
   Jamais de raccourci de démo pour un flux qui appelle une API : un vrai compte.
5. Compare à la maquette : un écran qui n'a pas les éléments, l'ordre ou les libellés de la
   maquette validée est un écart, même s'il « marche ».
6. Tu ne modifies RIEN : ni le code, ni les tests, ni les données au-delà de ce qu'un
   utilisateur ferait. Tu n'écris que sous tests/e2e/verification/ et dans le journal.

## Ce que tu rends
A. {projet}/tests/e2e/verification/m{N}/cycle{K}/rapport.md : une ligne par histoire et par
   étape de parcours — `PASS` | `FAIL` | `NON CONSTRUITE (clé absente)` — avec la capture qui
   le prouve ; pour chaque FAIL : ce qui était attendu (critère ou maquette), ce que tu as vu,
   la capture.
B. Ajoute au journal {projet}/docs/pipeline/m{N}-journal.md, en fin de fichier, EXACTEMENT :

   ## Vérificateur — cycle {K}
   Verdict : PASS        (ou : Verdict : FAIL)
   Rejoué sur : {URL} — <n> histoires, <m> étapes de parcours, <c> captures
   Écarts :
   1. <histoire ou étape> — attendu <…> — vu <…> — capture <chemin>
   (« aucun » si PASS)

   La ligne `Verdict :` suit IMMÉDIATEMENT le titre : le contrôle de la pipeline la lit là.
   PASS seulement si TOUTES les histoires construites et toutes les étapes de parcours passent.
   Un doute = FAIL avec l'écart décrit : le bâtisseur suivant le lèvera ou le contestera.
C. Ton message final au chef : le verdict, les comptes, les écarts numérotés.
```

## Mode retours (appelé par 4.3)

Même agent, même règles, avec en plus la liste du tour : pour chaque retour `R<i>`, son `dit`
(mots du client) et son `attendu`. Il vérifie chaque `attendu` sur la **préversion** que le
bâtisseur a déployée (`docs/pipeline/retours/tour-{N}-preview-url.txt`), puis
rejoue les histoires et étapes de parcours des écrans touchés (non-régression). Captures dans
`tests/e2e/verification/retours/tour-{N}/cycle{K}/`, verdict dans
`docs/pipeline/retours/tour-{N}-journal.md`, même format (`## Vérificateur — cycle K` puis
`Verdict :`), une ligne par retour `R<i> — attendu tenu | non tenu — capture`.
