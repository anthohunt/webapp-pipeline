"""
Validateur webapp — REVUE (étape 3 : le client regarde la vidéo et teste l'app).

Le verdict du client est la seule entrée humaine de l'étape, et il revient par
l'opérateur : il se garde donc mot pour mot, et chaque retour devient un point qu'un
agent peut vérifier sur l'app. Un retour sans `attendu` vérifiable ne peut pas
être corrigé — seulement interprété.

Contrats :
1. `revue.json` est au contrat : `{"tours":[{"tour","verdict","date","citation"}]}`,
   tours numérotés 1, 2, 3… dans l'ordre, verdict `good` ou `retours`, citation non vide.
2. Le tour N a été joué sur une vidéo qui existe : `video/versions.json` porte une
   version au tour N-1 (V1 pour la revue 1, la version du tour de retours ensuite).
3. Seul le dernier tour peut être `good`, et après un `good` il n'y a plus de tour.
4. Chaque tour à verdict `retours` a son `retours/tour-<N>.json` et son `.md`, au
   contrat : `tour` = N, statut `a-traiter` ou `traite`, au moins un retour, chacun
   avec `id` unique, `dit` (mots exacts) et `attendu` (critère vérifiable) non vides,
   `histoire` et `ecran` à null ou existants (`stories.json`, `design/screens.json`).
5. Un tour `good` n'a pas de fichier de retours.

Sans outil de tournage (réglage WEBAPP_VIDEO=0), le contrat 2 est levé : le client teste l'app seule.
"""
import os, json, pathlib, re

DOCS = 'docs/pipeline'
VERDICTS = ('good', 'retours')


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def _json(p):
    try:
        return json.loads(_txt(p)), None
    except json.JSONDecodeError as e:
        return None, str(e)


def _ids(p, cles):
    j, _ = _json(p)
    if j is None:
        return None
    lst = j if isinstance(j, list) else next((j.get(k) for k in cles if j.get(k)), [])
    return {str(x.get('id')) for x in lst if isinstance(x, dict) and x.get('id')}


def lire_revue(ws):
    j, e = _json(ws / DOCS / 'revue.json')
    if not isinstance(j, dict) or not isinstance(j.get('tours'), list):
        return None
    return j['tours']


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS
    rp = d / 'revue.json'
    if not rp.exists() or rp.stat().st_size == 0:
        return [f"C1: `{DOCS}/revue.json` absent/vide — aucun verdict du client n'est enregistré"]
    j, e = _json(rp)
    if j is None:
        return [f"C1: `revue.json` JSON invalide : {e}"]
    tours = j.get('tours') if isinstance(j, dict) else None
    if not isinstance(tours, list) or not tours:
        return ["C1: `revue.json` doit porter `{\"tours\": [ … ]}` avec au moins un tour"]

    vj, _ = _json(ws / 'video' / 'versions.json')
    tours_video = ({v.get('tour') for v in vj['versions'] if isinstance(v, dict)}
                   if isinstance(vj, dict) and isinstance(vj.get('versions'), list) else set())
    histoires = _ids(d / 'stories.json', ('stories', 'histoires'))
    ecrans = _ids(d / 'design' / 'screens.json', ('screens', 'ecrans'))

    for i, t in enumerate(tours, 1):
        if not isinstance(t, dict):
            errs.append(f"C1: tour n°{i} n'est pas un objet")
            continue
        if t.get('tour') != i:
            errs.append(f"C1: le tour en position {i} porte `tour: {t.get('tour')!r}` (attendu {i})")
        if t.get('verdict') not in VERDICTS:
            errs.append(f"C1: tour {i} : verdict `{t.get('verdict')}` hors de {list(VERDICTS)}")
        if not isinstance(t.get('date'), str) or not re.match(r'\d{4}-\d{2}-\d{2}', t.get('date') or ''):
            errs.append(f"C1: tour {i} : `date` ISO absente")
        if not isinstance(t.get('citation'), str) or not t['citation'].strip():
            errs.append(f"C1: tour {i} : `citation` vide — le verdict se garde avec les mots exacts")
        if (i - 1) not in tours_video and os.environ.get('WEBAPP_VIDEO', '1').strip() != '0':
            errs.append(f"C2: tour {i} sans vidéo à revoir — `video/versions.json` n'a pas de version "
                        f"au tour {i - 1}")
        if t.get('verdict') == 'good' and i != len(tours):
            errs.append(f"C3: tour {i} est `good` mais d'autres tours suivent — un `good` clôt la run")

        rj = d / 'retours' / f'tour-{i}.json'
        rm = d / 'retours' / f'tour-{i}.md'
        if t.get('verdict') == 'good':
            if rj.exists():
                errs.append(f"C5: tour {i} `good` avec un `retours/tour-{i}.json` — l'un des deux ment")
            continue
        if t.get('verdict') != 'retours':
            continue
        if not rj.exists():
            errs.append(f"C4: tour {i} à retours sans `retours/tour-{i}.json` — la construction n'a "
                        "rien à traiter")
            continue
        if not rm.exists() or rm.stat().st_size == 0:
            errs.append(f"C4: `retours/tour-{i}.md` absent/vide — la liste lisible manque")
        r, e = _json(rj)
        if not isinstance(r, dict):
            errs.append(f"C4: `retours/tour-{i}.json` illisible ({e or 'pas un objet'})")
            continue
        if r.get('tour') != i:
            errs.append(f"C4: `retours/tour-{i}.json` porte `tour: {r.get('tour')!r}`")
        if r.get('statut') not in ('a-traiter', 'traite'):
            errs.append(f"C4: `retours/tour-{i}.json` statut `{r.get('statut')}` hors de "
                        "['a-traiter', 'traite']")
        lst = r.get('retours')
        if not isinstance(lst, list) or not lst:
            errs.append(f"C4: `retours/tour-{i}.json` ne porte aucun retour")
            continue
        vus = set()
        for x in lst:
            if not isinstance(x, dict):
                errs.append(f"C4: tour {i} : un retour n'est pas un objet")
                continue
            rid = x.get('id') or '?'
            if rid in vus:
                errs.append(f"C4: tour {i} : id de retour en double {rid}")
            vus.add(rid)
            for k in ('id', 'dit', 'attendu'):
                if not isinstance(x.get(k), str) or not x[k].strip():
                    errs.append(f"C4: tour {i} retour {rid} : `{k}` vide")
            h, ec = x.get('histoire'), x.get('ecran')
            if h is not None and (not isinstance(h, str) or (histoires is not None and h not in histoires)):
                errs.append(f"C4: tour {i} retour {rid} : histoire `{h}` absente de `stories.json`")
            if ec is not None and (not isinstance(ec, str) or (ecrans is not None and ec not in ecrans)):
                errs.append(f"C4: tour {i} retour {rid} : écran `{ec}` absent de `design/screens.json`")
    return errs
