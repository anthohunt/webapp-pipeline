# Pipeline web app en 3 étapes — design (24/10/2026)

Design validé le 24/10/2026.

## Problème
La pipeline `webapp` compte 4 étapes (cadrer → construire → durcir → livrer). Le client n'y
intervient qu'une fois, au test du mockup ; il ne voit jamais l'app finie avant la livraison, et
le cycle de construction (5 agents par jalon) plus le durcissement et la documentation finale
coûtent environ 2 jours pour une app de taille moyenne (mesuré sur une run d'essai).

## Solution : une boucle en 3 étapes

### 1. Concevoir — en conversation (opérateur + client)
• Pitch, puis questions d'usage.
• Livrables : **cahier des charges**, **parcours utilisateur**, **user stories**, **mockup
  cliquable** avec panneau d'histoires (format dual-layer actuel).
• Le client teste le mockup ; boucle de correction en direct jusqu'à validation.
• Repris de l'actuel nœud `cadrer` ; le cahier des charges et le parcours utilisateur deviennent
  des livrables explicites, jugés par le gate.

### 2. Construire — autonome (serveur)
• Découpage en jalons = groupes d'écrans du mockup (règle du 20/08 conservée, contrat C7).
• Cycle allégé par jalon : **bâtisseur** puis **vérificateur indépendant** qui rejoue les
  histoires avec captures ; puis tests, commit, mise en ligne. (Remplace bâtisseur → évaluateur
  → descripteur → auditeur → contre-évaluateur.)
• App complète → **vidéo de démonstration** par un outil de tournage externe (optionnel, non fourni) :
  ◦ scénario écrit automatiquement depuis le parcours utilisateur et les user stories, une
    séquence par parcours, séquences « filmées » sur l'app en ligne ; pas de validation du
    scénario (la revue se fait à l'étape 3) ;
  ◦ chaque vidéo livrée figée en version (`montage.py --figer`, V1, V2…) ;
  ◦ table de montage publiée (`$MONTAGE_URL/<app>/`, `--avec-code`).
• Supprimés : le durcissement (4 audits) et la livraison documentaire — la vidéo est le livrable.

### 3. Revue — le client avec l'opérateur
• Le client regarde la vidéo et teste l'app.
• « Good » → fin de la run.
• Sinon, les retours arrivent **en conversation via l'opérateur** ; ils deviennent des histoires à
  corriger ; l'étape 2 repart sur ces seuls points, ne refilme que les séquences touchées et fige
  la version suivante de la vidéo.

## Architecture (flux)
• `workflows/webapp.json` : 3 nœuds — `concevoir` (local, interactif), `construire` (agent,
  relancé par jalon puis tournage), `revue` (local, barrière humaine, boucle vers `construire`).
• Nœuds `durcir` et `livrer` retirés ; `webapp-design` régénéré par `tools/sync-webapp-design.py`.
• Skills : `pipeline-step1` (+ cahier des charges, parcours), `pipeline-step4*` (cycle à 2
  agents + tournage), nouveau protocole de revue ; `pipeline-step5/6` sortent du graphe.

## Critères de succès
• L'étape 1 se joue de bout en bout avec le client (mockup publié, gate vert).
• L'étape 2 produit l'app en ligne + une vidéo V1 publiée sur la table de montage, sans humain.
• Un retour client relance l'étape 2 et produit une V2 qui ne refilme que les séquences touchées.

## Hors périmètre
Durcissement, documentation finale, parcours illustré, commentaires du client directement sur la
table de montage (les retours passent par l'opérateur).
