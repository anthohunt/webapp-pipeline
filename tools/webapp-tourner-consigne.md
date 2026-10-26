Tu écris puis répètes la séquence {SEQ_MAJ} de la vidéo de démonstration de l'application web « {APP} » ({APP_URL}). Tu travailles seul, sans humain : tu ne poses aucune question, tu tranches et tu notes tes choix dans fait.json. Face à une erreur ou une incertitude technique, cherche en ligne avant de deviner. Ta réponse finale tient en deux lignes (résultat d'abord).

Une séquence = un parcours utilisateur joué de bout en bout sur l'app en ligne, filmé automatiquement (navigateur sans écran), commenté par une voix de synthèse (Henri). Le client regarde cette vidéo pour découvrir son app : elle doit être juste, lisible et sobre.

## Le parcours à montrer
```json
{PARCOURS}
```

## Les histoires (user stories) que ce parcours joue
{HISTOIRES}

## Les écrans concernés
{ECRANS}
{RETOURS}
## Ce que tu livres
Le fichier `{FRAG}` (YAML), déjà amorcé. Tu remplis `titre`, `url` et `etapes` ; tu ne touches à aucun autre champ (voix, taille, profil…).
• `titre` : titre de la séquence, 3 à 7 mots, sans point final.
• `url` : l'adresse exacte où la séquence commence. L'app s'ouvre à neuf à chaque prise (profil de navigateur vide, aucune donnée locale).
• `etapes` : la liste des plans, dans l'ordre, ids `{SEQ}-1`, `{SEQ}-2`… Chaque plan :
```yaml
  - id: {SEQ}-1
    ecran: "ce qu'on voit à l'image pendant ce plan (une ligne, pour le scénario)"
    dit: "Ce que dit la voix. Une à trois phrases."
    montre: "ce qui doit être lisible à l'écran quand la voix le dit"
    avant: []      # facultatif : attentes jouées AVANT que la voix parle (écran prêt)
    gestes: []     # gestes calés sur un mot du dit
    ensuite: []    # facultatif : gestes ou attentes après la phrase (courts : ils allongent le plan)
```

## Le texte dit
• Un narrateur à la 3e personne raconte ce que fait la personne du parcours, au présent : « La cliente ouvre l'onglet Rayons. »
• Une idée par phrase, phrases courtes. Une à trois phrases par plan. Quatre à huit plans. La séquence dure 30 à 75 secondes.
• Ton factuel et démonstratif : les noms exacts des boutons et des écrans, tels qu'affichés. Pas de chiffre qui change d'une heure à l'autre (un prix, une heure) : décris plutôt (« le produit le moins cher arrive en tête »).
• Jamais de punchline, de formule marketing, de question, d'exclamation, de superlatif publicitaire. Jamais de deux-points dans le dit (la voix y prend un mauvais rythme) ; pas de guillemets, de parenthèses ni d'abréviations ; des virgules là où un lecteur respire.
• Le premier plan situe la personne et ce qu'elle veut faire. Le dernier plan dit le résultat obtenu, visible à l'écran.
• Chaque phrase parle de ce qui est à l'écran à ce moment-là : on ne commente jamais un écran qui n'est pas encore affiché.

## Les gestes (format du joueur tournage.mjs)
Cibles : `{role: button, nom: "Fruits", exact: true}`, `{texte: "…"}`, `{label: "…"}`, `{testid: "…"}`, `{css: "…"}` (en dernier recours) ; `rang: n` pour le n-ième (-1 = dernier).
Gestes : `clic`, `double`, `survol` (+ `tenir` ms), `tape: {cible, texte, vitesse: 70, vider: true}`, `touche: Enter`, `defile: {cible, dy: 300}`, `choisir: {cible, valeur}` (liste déroulante), `attendre: {role/texte… | ms | absent: cible, delai: 15000}`, `pause: 0.8` (s).
Exemple :
```yaml
    gestes:
      - sur: fruits
        clic: { role: button, nom: Fruits, exact: true }
    ensuite:
      - attendre: { role: heading, nom: "Rayon · Fruits" }
```
• `sur: <mot>` : le geste part quand Henri prononce ce mot (le curseur part 0,45 s avant). Le mot doit figurer tel quel dans le `dit` de SON plan ; choisis le mot qui annonce le geste, jamais un mot outil (le, la, de, et). Les gestes d'un plan suivent l'ordre de leurs mots dans la phrase.
• Les cibles se trouvent sur l'app réelle, relevées avec la sonde ou dans les fichiers `.aria.txt` de la répétition ; jamais au jugé. Préfère `role` + `nom` exact.
• Après un geste qui charge (réseau, calcul), mets une attente sur l'élément qui prouve que l'écran est prêt (dans `ensuite`, ou dans `avant` du plan suivant).
• Mise en scène : amène dans le cadre ce dont la voix parle (`defile`), désigne une valeur sans cliquer (`survol` avec `tenir`). Chaque plan a au moins un geste visible, sauf un plan fixe voulu.
• L'app est en production, chez le client : ne crée que les données que le parcours exige, plausibles (jamais « test » ni « toto ») ; ne supprime rien qui existait avant toi.

## Tes outils (déjà installés)
```bash
cd {DIR}
export PATH={SHIM}:$PATH TOURNAGE_CHROMIUM={CHROME}
# relever une page : arbre d'accessibilité (rôles, noms) + capture à lire
node {SONDE} "<url>" sonde.png [--clic "button:Démarrer"] [--tape "textbox:Nom=velo"]
# voix d'Henri (quelques secondes ; à refaire après toute modification d'un dit)
node {TOURNAGE} voix {SEQ}.yaml
# répétition complète, app neuve : captures par plan, journal, arbre de chaque page
rm -rf {PROFIL_DIR} && node {TOURNAGE} repetition {SEQ}.yaml --headless --sans-voix --releve
```
La répétition écrit `{SEQ}.repetition/` : `NN-<id>.png` (l'image à la fin de chaque plan), `NN-<id>.aria.txt` (l'arbre de la page), `journal.json` (`echec`, et `decalage_ms` de chaque geste par rapport à son mot). Ne modifie aucun fichier hors de `{DIR}`.

## Fini quand
1. Une répétition complète passe : `echec` vaut null et aucun `decalage_ms` ne dépasse 300 (sinon ajoute une attente au plan précédent ou choisis un mot plus tardif).
2. Tu as LU chaque capture de la dernière répétition : ce que dit `montre` y est lisible ; aucun écran blanc, chargement ou message d'erreur.
3. Tu as écrit `{DIR}/fait.json` : `{"ok": true, "tour": {TOUR}, "notes": "<tes choix, 1 à 3 phrases>", "constats": ["<défaut du produit vu en route>"]}`.
Si un défaut de l'app empêche de jouer le parcours et qu'aucun autre chemin ne montre la même chose : `{"ok": false, "tour": {TOUR}, "bloque": "<ce qui ne marche pas, sur quel écran>"}`.
