"""
Validateur webapp — SPÉCIFIER.

Gate de sortie du nœud « specifier » : le kit de projet est-il un CONTRAT
vérifiable, ou une belle intention ? Deux contrats mordent particulièrement :
chaque jalon doit avoir son plan de cas d'usage (sinon le build n'a rien à
prouver), et `tasks.md` ne doit contenir aucun service simulé (sinon on livre
une maquette qui se fait passer pour une application).

Contrats :
1. Les livrables du kit sont présents et non vides.
2. stories.json est un JSON valide, non vide, chaque histoire portant un id, un
   titre et des critères d'acceptation en ÉTANT DONNÉ / QUAND / ALORS.
3. spec.md, plan.md, tasks.md, rules.md font chacun au moins 800 caractères.
4. tests/features/registry.json est valide et chaque fichier de test référencé existe.
5. Chaque jalon de la feuille de route a son `tests/e2e/use-cases/m{N}-use-case.md`.
6. `tasks.md` ne prescrit AUCUN service simulé (mock, stub, données en dur à la
   place d'une intégration réelle).
7. La feuille de route porte au moins un jalon.
C11. La pile technique est TRANCHÉE et JUSTIFIÉE : `stack-decisions.md` répond aux questions
   différées au cadrage, chacune avec le fait d'usage qui la commande. Ce nœud est autonome —
   une décision non écrite est une décision que personne ne pourra contester à l'approbation.
8bis. Les histoires v1 du canvas ont toutes survécu : la spécification COMPLÈTE, elle ne
   repart pas de zéro. Une histoire testée puis disparue est une décision annulée en
   silence.
8. COUVERTURE UI : chaque élément interactif déclaré dans `design/screens.json` est
   couvert par au moins une user story, via `ui-coverage.json`. C'est le contrat
   historique du mockup à deux couches, rendu machine-vérifiable : un contrôle
   dessiné que personne ne raconte est un contrôle que personne ne construit.
"""
import json, pathlib, re

DOCS = 'docs/pipeline'
KIT = ('spec.md', 'plan.md', 'tasks.md', 'rules.md')

# formulations qui trahissent un faux service (FR + EN), hors mention explicite de repli
SIMULE = re.compile(
    r'\b(mock(ed|s)?|stub(bed|s)?|fake\s+(api|service|data)|donn[ée]es?\s+simul[ée]es?|'
    r'service\s+simul[ée]|simulate[d]?\s+(api|service|response)|hardcod(e|ed|ing)\s+'
    r'(json|data|response)|setTimeout\s*\(\s*\)\s*(pour|to)\s+simul)', re.I)


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def _milestones(ws):
    """Numéros de jalons trouvés dans la feuille de route (html) ou la spec."""
    nums = set()
    for f in (ws / DOCS / 'roadmap.html', ws / DOCS / 'spec.md'):
        if f.exists():
            for m in re.finditer(r'(?:milestone|jalon)\s*#?\s*(\d+)', _txt(f), re.I):
                nums.add(int(m.group(1)))
    return sorted(nums)


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    attendus = ('system-architecture.html', 'stories.json', 'roadmap.html') + KIT
    for f in attendus:
        p = d / f
        if not p.exists() or p.stat().st_size == 0:
            errs.append(f"C1: `{DOCS}/{f}` absent/vide — le kit de projet est incomplet")

    st = d / 'stories.json'
    if st.exists() and st.stat().st_size:
        try:
            j = json.loads(_txt(st))
            stories = j if isinstance(j, list) else (j.get('stories') or j.get('user_stories') or [])
            if not stories:
                errs.append("C2: `stories.json` ne contient aucune histoire utilisateur")
            sans_ac = []
            for s in stories:
                if not isinstance(s, dict):
                    continue
                blob = json.dumps(s, ensure_ascii=False)
                if not re.search(r'(GIVEN|[EÉ]TANT DONN[EÉ])', blob, re.I) or \
                   not re.search(r'(WHEN|QUAND)', blob, re.I) or \
                   not re.search(r'(THEN|ALORS)', blob, re.I):
                    sans_ac.append(str(s.get('id') or s.get('title') or '?'))
            if sans_ac:
                errs.append(f"C2: {len(sans_ac)} histoire(s) sans critères d'acceptation "
                            "ÉTANT DONNÉ/QUAND/ALORS (" + ', '.join(sans_ac[:5]) +
                            ") — non testable = ne compte pas")
        except json.JSONDecodeError as e:
            errs.append(f"C2: `stories.json` JSON invalide: {e}")

    for f in KIT:
        p = d / f
        if p.exists():
            n = len(_txt(p))
            if n < 800:
                errs.append(f"C3: `{DOCS}/{f}` fait {n} car (< 800) — un kit de projet squelettique "
                            "ne cadre rien au moment du build")

    reg = ws / 'tests' / 'features' / 'registry.json'
    if not reg.exists():
        errs.append("C4: `tests/features/registry.json` absent — aucun échafaudage de tests")
    else:
        try:
            j = json.loads(_txt(reg))
            feats = j.get('features') or []
            if not feats:
                errs.append("C4: `registry.json` ne déclare aucune fonctionnalité testée")
            absents = [f.get('file') for f in feats
                       if f.get('file') and not (ws / 'tests' / 'features' / f['file']).exists()]
            if absents:
                errs.append("C4: fichiers de test déclarés mais absents : " +
                            ', '.join(str(a) for a in absents[:5]))
        except json.JSONDecodeError as e:
            errs.append(f"C4: `registry.json` JSON invalide: {e}")

    jalons = _milestones(ws)
    if not jalons:
        errs.append("C7: aucun jalon détecté dans `roadmap.html`/`spec.md` — la feuille de route "
                    "ne découpe rien")
    manquants = [n for n in jalons
                 if not (ws / 'tests' / 'e2e' / 'use-cases' / f'm{n}-use-case.md').exists()]
    if manquants:
        errs.append("C5: jalon(s) sans plan de cas d'usage : " +
                    ', '.join(f'm{n}' for n in manquants) +
                    " — le build n'aurait rien à prouver sur ces jalons")

    # C8 — couverture UI : le canvas ne doit rien laisser sans histoire
    scj = ws / 'docs' / 'pipeline' / 'design' / 'screens.json'
    cov = d / 'ui-coverage.json'
    if scj.exists():
        try:
            sj = json.loads(_txt(scj))
            ecrans = sj if isinstance(sj, list) else (sj.get('screens') or sj.get('ecrans') or [])
        except json.JSONDecodeError:
            ecrans = []
        attendus = {}
        for e in ecrans:
            if isinstance(e, dict):
                attendus[str(e.get('id') or e.get('name'))] = list(
                    e.get('interactive_elements') or e.get('elements_interactifs') or [])
        if attendus and (not cov.exists() or cov.stat().st_size == 0):
            errs.append("C8: `ui-coverage.json` absent — la couverture UI n'est pas établie : "
                        "on ne sait pas quels éléments du canvas ont une histoire")
        elif attendus:
            try:
                cj = json.loads(_txt(cov))
                trous = []
                for sid, elems in attendus.items():
                    couvert = cj.get(sid) or {}
                    for el in elems:
                        if not (couvert.get(el) or []):
                            trous.append(f'{sid}/{el}')
                if trous:
                    errs.append(f"C8: {len(trous)} élément(s) du canvas sans user story (" +
                                ', '.join(trous[:6]) + ") — un contrôle dessiné sans histoire ne "
                                "sera ni construit ni testé")
            except json.JSONDecodeError as e:
                errs.append(f"C8: `ui-coverage.json` JSON invalide: {e}")

    # C11 — la pile est un STANDARD : on verifie qu'il est applique, et que tout ecart
    # porte le fait d'usage qui l'impose. Un projet qui redecide sa pile sans motif fait
    # diverger l'infra partagee (comptes, cles, conventions) que le standard existe pour tenir.
    STANDARD = (('React', r'react'), ('Vite', r'vite'),
                ('Supabase', r'supabase'), ('Vercel', r'vercel'))
    HORS_STANDARD = re.compile(
        r'\b(angular|svelte|nuxt|remix|firebase|mongodb|dynamodb|netlify|heroku|render\.com|'
        r'fly\.io|cloudflare pages|aws amplify)\b', re.I)

    sd = d / 'stack-decisions.md'
    if not sd.exists() or sd.stat().st_size == 0:
        errs.append("C11: `docs/pipeline/stack-decisions.md` absent — le standard doit être "
                    "appliqué par écrit : schéma de données, RLS, ce qui est déployé où")
    else:
        t = _txt(sd)
        if len(t) < 300:
            errs.append(f"C11: `stack-decisions.md` fait {len(t)} car — l'application du standard "
                        "à ce projet ne se relit pas")
        absents = [nom for nom, rx in STANDARD if not re.search(rx, t, re.I)]
        if absents:
            errs.append("C11: `stack-decisions.md` ne dit pas comment le standard s'applique pour "
                        + ', '.join(absents) + " — la pile est figée (React+Vite, Supabase, Vercel), "
                        "c'est son APPLICATION à ce projet qui s'écrit ici")
        for m in set(x.group().lower() for x in HORS_STANDARD.finditer(t)):
            ligne = next((l for l in t.splitlines() if m in l.lower()), '')
            if not re.search(r"(écart|ecart|au lieu|impose|contrainte|sinon impossible)", ligne, re.I):
                errs.append(f"C11: `stack-decisions.md` introduit '{m}' hors standard sans le "
                            "déclarer comme un ÉCART motivé par un fait d'usage")

    # C10 — aucune histoire v1 perdue en route
    v1 = ws / 'docs' / 'pipeline' / 'design' / 'stories-v1.json'
    st2 = d / 'stories.json'
    if v1.exists() and st2.exists():
        try:
            a = json.loads(_txt(v1))
            a = a if isinstance(a, list) else (a.get('stories') or a.get('histoires') or [])
            final = _txt(st2).lower()
            perdues = []
            for x in a:
                if not isinstance(x, dict):
                    continue
                sid = str(x.get('id') or '').strip().lower()
                titre = str(x.get('titre') or x.get('title') or '').strip().lower()
                if sid and sid in final:
                    continue
                mots = [m for m in re.split(r"[^\w']+", titre) if len(m) > 4]
                if mots and sum(1 for m in mots if m in final) >= max(1, len(mots) // 2):
                    continue
                perdues.append(x.get('id') or titre or '?')
            if perdues:
                errs.append(f"C10: {len(perdues)} histoire(s) du canvas absente(s) de `stories.json` (" +
                            ', '.join(str(x) for x in perdues[:5]) + ") — la spécification complète les "
                            "histoires testées, elle ne les remplace pas")
        except json.JSONDecodeError:
            pass

    tk = d / 'tasks.md'
    if tk.exists():
        t = _txt(tk)
        faux = []
        for i, l in enumerate(t.splitlines(), 1):
            if SIMULE.search(l) and not re.search(
                    r'(fallback|repli|hors ligne|offline|aucun|jamais|interdit|sans\s)',
                    l, re.I):
                faux.append(f'l.{i}')
        if faux:
            errs.append("C6: `tasks.md` prescrit des services simulés (" + ', '.join(faux[:6]) +
                        ") — une tâche d'intégration doit nommer la vraie source et gérer ses "
                        "erreurs ; les données d'exemple ne sont tolérées qu'en repli hors ligne")

    return errs
