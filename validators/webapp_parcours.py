"""
Validateur webapp — CAHIER DES CHARGES et PARCOURS UTILISATEUR (moments de « concevoir »).

Les histoires découlent du parcours, et la vidéo de démonstration filme une séquence
par parcours : un parcours qui nomme un écran que le mockup n'a pas, ou une histoire
que personne n'a écrite, casse la construction ET le tournage, deux étapes plus loin.
Ce contrôle juge donc le contenu, pas la seule présence des fichiers.

Contrats :
1. `cahier-des-charges.md` présent, non vide, et traite les six rubriques : but,
   utilisateurs, périmètre V1, hors périmètre, contraintes, sources de données.
2. `parcours-utilisateur.json` est un JSON valide au contrat :
   `{"parcours":[{"id","titre","qui","but","etapes":[{"n","ecran","geste","stories":[…]}]}]}`
   — au moins un parcours, ids uniques, chaque étape numérotée 1, 2, 3… dans l'ordre.
3. Chaque étape nomme un écran qui existe dans `design/screens.json`.
4. Chaque étape cite au moins une histoire, et chaque histoire citée existe
   (`stories.json`, à défaut `design/stories-v1.json`).
5. `parcours-utilisateur.md` présent, non vide, et nomme chaque parcours (id ou titre).
"""
import json, pathlib, re, unicodedata

DOCS = 'docs/pipeline'
RUBRIQUES = (
    ('but', r'\bbut\b|objectif'),
    ('utilisateurs', r'utilisateur'),
    ('périmètre V1', r'(?<!hors )(?<!hors-)(?<!hors)perimetre|\bv1\b'),
    ('hors périmètre', r'hors[\s-]*perimetre|hors[\s-]*scope'),
    ('contraintes', r'contrainte'),
    ('sources de données', r'sources?\s+de\s+donnees|donnees\s+sources?'),
)


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def _plat(s):
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def _json(p):
    try:
        return json.loads(_txt(p)), None
    except json.JSONDecodeError as e:
        return None, str(e)


def ids_ecrans(ws):
    j, _ = _json(ws / DOCS / 'design' / 'screens.json')
    if j is None:
        return None
    ecrans = j if isinstance(j, list) else (j.get('screens') or j.get('ecrans') or [])
    return {str(e.get('id')) for e in ecrans if isinstance(e, dict) and e.get('id')}


def ids_histoires(ws):
    for f in (ws / DOCS / 'stories.json', ws / DOCS / 'design' / 'stories-v1.json'):
        if not f.exists():
            continue
        j, _ = _json(f)
        if j is None:
            continue
        lst = j if isinstance(j, list) else (j.get('stories') or j.get('histoires') or [])
        ids = {str(s.get('id')) for s in lst if isinstance(s, dict) and s.get('id')}
        if ids:
            return ids
    return None


def lire_parcours(ws):
    """(liste des parcours, erreurs de forme). Sert aussi aux autres contrôles."""
    p = ws / DOCS / 'parcours-utilisateur.json'
    if not p.exists() or p.stat().st_size == 0:
        return None, [f"C2: `{DOCS}/parcours-utilisateur.json` absent/vide — sans parcours, ni les "
                      "histoires ni la vidéo n'ont de fil"]
    j, e = _json(p)
    if j is None:
        return None, [f"C2: `parcours-utilisateur.json` JSON invalide : {e}"]
    if not isinstance(j, dict) or not isinstance(j.get('parcours'), list) or not j['parcours']:
        return None, ["C2: `parcours-utilisateur.json` doit porter `{\"parcours\": [ … ]}` avec au "
                      "moins un parcours"]
    errs, vus = [], set()
    for i, pc in enumerate(j['parcours'], 1):
        if not isinstance(pc, dict):
            errs.append(f"C2: parcours n°{i} n'est pas un objet")
            continue
        pid = str(pc.get('id') or f'#{i}')
        for k in ('id', 'titre', 'qui', 'but'):
            if not isinstance(pc.get(k), str) or not pc[k].strip():
                errs.append(f"C2: parcours {pid} : champ `{k}` absent ou vide")
        if pc.get('id') in vus:
            errs.append(f"C2: id de parcours en double : {pid}")
        vus.add(pc.get('id'))
        et = pc.get('etapes')
        if not isinstance(et, list) or not et:
            errs.append(f"C2: parcours {pid} : aucune étape — un parcours est un usage de bout en bout")
            continue
        for k, e in enumerate(et, 1):
            if not isinstance(e, dict):
                errs.append(f"C2: parcours {pid} étape {k} n'est pas un objet")
                continue
            if e.get('n') != k:
                errs.append(f"C2: parcours {pid} : l'étape en position {k} porte `n: {e.get('n')!r}` "
                            f"(attendu {k}) — les étapes se numérotent 1, 2, 3… dans l'ordre")
            for c in ('ecran', 'geste'):
                if not isinstance(e.get(c), str) or not e[c].strip():
                    errs.append(f"C2: parcours {pid} étape {k} : champ `{c}` absent ou vide")
            if not isinstance(e.get('stories'), list):
                errs.append(f"C2: parcours {pid} étape {k} : `stories` doit être une liste")
    return j['parcours'], errs


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    cdc = d / 'cahier-des-charges.md'
    if not cdc.exists() or cdc.stat().st_size == 0:
        errs.append(f"C1: `{DOCS}/cahier-des-charges.md` absent/vide — le périmètre de la V1 n'est "
                    "écrit nulle part")
    else:
        t = _plat(_txt(cdc))
        manq = [nom for nom, rx in RUBRIQUES if not re.search(rx, t)]
        if manq:
            errs.append("C1: `cahier-des-charges.md` ne traite pas : " + ', '.join(manq))

    parcours, e_forme = lire_parcours(ws)
    errs += e_forme
    if parcours:
        ecrans = ids_ecrans(ws)
        histoires = ids_histoires(ws)
        if ecrans is None:
            errs.append("C3: `design/screens.json` illisible — les écrans des parcours ne se "
                        "vérifient pas")
        if histoires is None:
            errs.append("C4: ni `stories.json` ni `design/stories-v1.json` lisibles — les histoires "
                        "des parcours ne se vérifient pas")
        for pc in parcours:
            if not isinstance(pc, dict):
                continue
            pid = pc.get('id')
            for e in pc.get('etapes') or []:
                if not isinstance(e, dict):
                    continue
                n = e.get('n')
                ec = e.get('ecran')
                if ecrans is not None and isinstance(ec, str) and ec.strip() and ec not in ecrans:
                    errs.append(f"C3: parcours {pid} étape {n} : écran `{ec}` absent de "
                                "`design/screens.json` — le mockup ne le dessine pas")
                st = e.get('stories')
                if isinstance(st, list):
                    if not st:
                        errs.append(f"C4: parcours {pid} étape {n} ne cite aucune histoire — une "
                                    "étape sans histoire n'est ni construite ni filmée")
                    elif histoires is not None:
                        inconnues = [s for s in st if str(s) not in histoires]
                        if inconnues:
                            errs.append(f"C4: parcours {pid} étape {n} cite des histoires "
                                        "inexistantes : " + ', '.join(map(str, inconnues)))

    md = d / 'parcours-utilisateur.md'
    if not md.exists() or md.stat().st_size == 0:
        errs.append(f"C5: `{DOCS}/parcours-utilisateur.md` absent/vide — la lecture humaine des "
                    "parcours manque")
    elif parcours:
        t = _plat(_txt(md))
        absents = [str(pc.get('id')) for pc in parcours if isinstance(pc, dict)
                   and not ((pc.get('id') and str(pc['id']).lower() in t)
                            or (pc.get('titre') and _plat(str(pc['titre'])) in t))]
        if absents:
            errs.append("C5: `parcours-utilisateur.md` ne nomme pas les parcours : " + ', '.join(absents))
    return errs
