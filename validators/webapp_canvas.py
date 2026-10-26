"""
Validateur webapp — DESSINER (mockup interactif à deux couches).

Gate de sortie du nœud « dessiner » : le mockup publié est-il un vrai prototype
cliquable avec un panneau de stories qui navigue et surligne — ou une image ?
Ce nœud est autonome (aucune question à l'opérateur) : la direction visuelle et les
tokens sont une décision de l'agent, jugée sur ce qu'elle produit, pas sur son
origine.

Contrats :
1. `mockup.html`, `mockup-url.txt`, `tokens.json`, `design-system-spec.json`,
   `screens.json`, `stories-v1.json` présents et non vides.
2. `screens.json` valide, ≥1 écran, chacun avec id, artboard/vue et ≥1 élément
   interactif (`interactive_elements`).
3. Chaque élément interactif est raconté par au moins une histoire v1
   (`stories-v1.json`, via `target` ou le texte du titre).
4. `mockup.html` porte les DEUX couches : un panneau de stories (texte
   « story »/« histoire ») ET une trace de navigation par script (au moins un
   gestionnaire d'événement / `data-el`) — un fichier purement statique n'a pas
   de prototype cliquable.
5. `tokens.json` déclare ≥4 couleurs par rôle (ground/surface/ink/accent),
   une échelle typographique et une échelle d'espacement.
6. `design-system-spec.json` porte `paths.tokens` et `framework`.
6bis. `mockup-public-url.txt` porte une adresse HTTP : un artifact appartient au
   compte qui l'a publié et reste privé, alors que le test du mockup est la seule
   barrière humaine de l'étape. Elle ne peut pas dépendre d'un identifiant.
7. Le bundle a été produit pendant cette run (plus récent que WORKSPACE.txt).
"""
import json, pathlib, re

D = 'docs/pipeline/design'


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / D

    attendus = ('mockup.html', 'mockup-url.txt', 'mockup-public-url.txt', 'tokens.json',
                'design-system-spec.json', 'screens.json', 'stories-v1.json')
    for f in attendus:
        p = d / f
        if not p.exists() or p.stat().st_size == 0:
            errs.append(f"C1: `{D}/{f}` absent/vide — le bundle du mockup est incomplet")

    ecrans = []
    sc = d / 'screens.json'
    if sc.exists() and sc.stat().st_size:
        try:
            j = json.loads(_txt(sc))
            ecrans = j if isinstance(j, list) else (j.get('screens') or j.get('ecrans') or [])
            if not ecrans:
                errs.append("C2: `screens.json` ne déclare aucun écran")
            for e in ecrans:
                if not isinstance(e, dict):
                    errs.append("C2: entrée d'écran mal formée dans `screens.json`")
                    continue
                nom = e.get('name') or e.get('nom') or e.get('id') or '?'
                if not e.get('id'):
                    errs.append(f"C2: écran « {nom} » sans id")
                inter = e.get('interactive_elements') or e.get('elements_interactifs') or []
                if not inter:
                    errs.append(f"C2: écran « {nom} » sans élément interactif déclaré")
        except json.JSONDecodeError as e:
            errs.append(f"C2: `screens.json` JSON invalide: {e}")

    st = d / 'stories-v1.json'
    stories = []
    if st.exists() and st.stat().st_size:
        try:
            j = json.loads(_txt(st))
            stories = j if isinstance(j, list) else (j.get('stories') or j.get('histoires') or [])
            if not stories:
                errs.append("C1: `stories-v1.json` ne contient aucune histoire")
        except json.JSONDecodeError as e:
            errs.append(f"C1: `stories-v1.json` JSON invalide: {e}")

    blob = json.dumps(stories, ensure_ascii=False).lower()
    orphelins = []
    for e in ecrans:
        if not isinstance(e, dict):
            continue
        for el in (e.get('interactive_elements') or e.get('elements_interactifs') or []):
            mots = [m for m in re.split(r"[^\w']+", str(el).lower()) if len(m) > 3]
            if mots and not any(m in blob for m in mots):
                orphelins.append(f"{e.get('id')}/{el}")
    if orphelins:
        errs.append(f"C3: {len(orphelins)} élément(s) dessiné(s) qu'aucune histoire ne raconte (" +
                    ', '.join(orphelins[:6]) + ") — le panneau de stories n'aurait rien pour naviguer "
                    "jusqu'à eux")

    mk = d / 'mockup.html'
    if mk.exists():
        t = _txt(mk)
        if not re.search(r'stor(y|ies)|histoire', t, re.I):
            errs.append("C4: `mockup.html` ne porte aucune trace d'un panneau de stories — le nœud "
                        "produit un mockup à DEUX couches, pas un prototype seul")
        if not re.search(r'data-el|addEventListener|onclick', t, re.I):
            errs.append("C4: `mockup.html` n'a aucun gestionnaire d'événement ni `data-el` détecté — "
                        "un mockup qu'on ne peut pas cliquer n'est pas un prototype")

    tk = d / 'tokens.json'
    if tk.exists() and tk.stat().st_size:
        try:
            t = json.loads(_txt(tk))
            couleurs = t.get('colors') or t.get('couleurs') or {}
            roles = {k.lower() for k in couleurs} if isinstance(couleurs, dict) else set()
            if len(couleurs) < 4:
                errs.append(f"C5: `tokens.json` ne déclare que {len(couleurs)} couleur(s) — il en faut "
                            "au moins 4, par rôle")
            manquants = [a.split('|')[0] for a in ('ground|background|fond', 'surface|card',
                        'ink|text|texte', 'accent|primary') if not any(re.search(a, r) for r in roles)]
            if manquants:
                errs.append("C5: `tokens.json` sans rôle " + ', '.join(manquants))
            if not (t.get('typography') or t.get('type') or t.get('typographie')):
                errs.append("C5: `tokens.json` sans échelle typographique")
            if not (t.get('spacing') or t.get('espacements') or t.get('space')):
                errs.append("C5: `tokens.json` sans échelle d'espacement")
        except json.JSONDecodeError as e:
            errs.append(f"C5: `tokens.json` JSON invalide: {e}")

    spec = d / 'design-system-spec.json'
    if spec.exists() and spec.stat().st_size:
        try:
            sp = json.loads(_txt(spec))
            if not (sp.get('paths') or {}).get('tokens'):
                errs.append("C6: `design-system-spec.json` sans `paths.tokens`")
            if not sp.get('framework'):
                errs.append("C6: `design-system-spec.json` sans `framework`")
        except json.JSONDecodeError as e:
            errs.append(f"C6: `design-system-spec.json` JSON invalide: {e}")

    wsf = ws / 'WORKSPACE.txt'
    if wsf.exists():
        vieux = [f for f in attendus if (d / f).exists() and (d / f).stat().st_mtime < wsf.stat().st_mtime]
        if vieux:
            errs.append("C7: " + ', '.join(f'`{v}`' for v in vieux) + " plus ancien(s) que "
                        "`WORKSPACE.txt` — bundle hérité d'un projet précédent")

    pub = d / 'mockup-public-url.txt'
    if pub.exists() and pub.stat().st_size:
        if not re.search(r'https?://\S+', _txt(pub)):
            errs.append("C6bis: `mockup-public-url.txt` ne contient pas d'adresse HTTP — le mockup "
                        "n'est atteignable que par le compte qui l'a publié, donc pas par la "
                        "personne qui doit le tester")

    return errs
