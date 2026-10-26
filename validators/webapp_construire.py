"""
Validateur webapp — CONSTRUIRE (étape 2 : jalons, vidéo, tours de retours).

Gate de sortie du nœud « construire ». Le nœud est relancé tant que ce contrôle
est rouge : chaque lancement traite un jalon, puis le tournage, puis un tour de
retours s'il y en a un. Il n'est vert que quand TOUT est livré — l'app en ligne,
la vidéo publiée, et aucun tour de retours en attente.

Un jalon coché doit avoir été construit sous le cycle, pas coché à la main : son
journal porte le PASS du vérificateur indépendant, et le vérificateur a laissé
ses captures.

Contrats :
1. `status.md` présent et non vide.
2. TOUS les jalons de `roadmap-approved.json` sont cochés dans `status.md`.
3. Chaque jalon coché a son `m{N}-journal.md`, non vide, dont le DERNIER verdict du
   vérificateur est PASS.
4. Les journaux ont été écrits pendant cette run (plus récents que WORKSPACE.txt).
5. Chaque jalon coché a laissé des captures du vérificateur dans
   `tests/e2e/verification/m{N}/`.
6. `avancement.json` est au contrat (phase, tour, jalons, maj) ; en fin de nœud la
   phase est `fini` et chaque jalon de la feuille de route y est `fait`.
7. `app-url.txt` porte l'URL de production (http/https).
8. `video/video-url.txt` porte le lien de la table de montage, avec son `?code=`.
9. `video/versions.json` est au contrat ; versions V1, V2… consécutives, V1 au tour 0.
10. Chaque tour de retours (`retours/tour-<N>.json`) est `traite` et a sa version de
    vidéo (une entrée de `versions.json` au tour N) ; l'avancement porte le dernier tour.
11. `project-memory.md`, s'il existe, ne dépasse pas 2000 caractères.

Sans outil de tournage (réglage WEBAPP_VIDEO=0), la vidéo n'est pas demandée : les contrats 8 et 9
et l'exigence de vidéo du contrat 10 sont levés.
"""
import json, os, pathlib, re

DOCS = 'docs/pipeline'
PHASES = ('jalons', 'tournage', 'fini', 'retours')
STATUTS_JALON = ('a-faire', 'en-cours', 'fait')


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


def coches(status_txt):
    return sorted({int(m.group(1)) for m in
                   re.finditer(r'\[x\][^\n]*?(?:milestone|jalon)\s*#?\s*(\d+)', status_txt, re.I)} |
                  {int(m.group(1)) for m in
                   re.finditer(r'(?:milestone|jalon)\s*#?\s*(\d+)[^\n]*?\[x\]', status_txt, re.I)})


def jalons_approuves(ws):
    """[(n, titre)] de la feuille de route approuvée."""
    j, _ = _json(ws / DOCS / 'roadmap-approved.json')
    if not isinstance(j, dict):
        return []
    out = []
    for m in (j.get('milestones') or j.get('jalons') or []):
        v = (m.get('n') or m.get('id') or m.get('numero')) if isinstance(m, dict) else m
        mm = re.search(r'\d+', str(v or ''))
        if mm:
            out.append((int(mm.group()), (m.get('titre') or m.get('title') or '') if isinstance(m, dict) else ''))
    return sorted(set(out))


def tours_retours(ws):
    """[(N, chemin, json|None, erreur|None)] triés par N."""
    d = ws / DOCS / 'retours'
    out = []
    for f in sorted(d.glob('tour-*.json')) if d.is_dir() else []:
        m = re.fullmatch(r'tour-(\d+)\.json', f.name)
        if not m:
            continue
        j, e = _json(f)
        out.append((int(m.group(1)), f, j, e))
    return sorted(out, key=lambda x: x[0])


def lire_versions(ws):
    j, e = _json(ws / 'video' / 'versions.json')
    return j, e


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    stt = d / 'status.md'
    if not stt.exists() or stt.stat().st_size == 0:
        errs.append(f"C1: `{DOCS}/status.md` absent/vide — l'état du build est introuvable")
        coch = []
    else:
        coch = coches(_txt(stt))

    attendus = jalons_approuves(ws)
    if not attendus:
        errs.append("C2: `roadmap-approved.json` ne nomme aucun jalon lisible — rien à construire")
    restants = [n for n, _ in attendus if n not in coch]
    if restants:
        errs.append("C2: jalon(s) approuvé(s) non construit(s) : " +
                    ', '.join(f'm{n}' for n in restants) +
                    " — le nœud se relance jusqu'à épuisement de la feuille de route")

    ref = (ws / 'WORKSPACE.txt').stat().st_mtime if (ws / 'WORKSPACE.txt').exists() else 0
    for n in coch:
        j = d / f'm{n}-journal.md'
        if not j.exists() or j.stat().st_size == 0:
            errs.append(f"C3: jalon m{n} coché mais `{DOCS}/m{n}-journal.md` absent/vide — un jalon "
                        "sans journal est auto-déclaré")
            continue
        verdicts = re.findall(r'v[ée]rificat(?:eur|rice)\w*[\s\S]{0,300}?\b(PASS|FAIL)\b', _txt(j), re.I)
        if not verdicts:
            errs.append(f"C3: journal m{n} sans PASS du vérificateur — les histoires du jalon n'ont "
                        "pas été rejouées par un agent qui ne les a pas construites")
        elif verdicts[-1].upper() != 'PASS':
            errs.append(f"C3: journal m{n} : le dernier verdict du vérificateur est FAIL — le jalon "
                        "est coché sur un refus")
        if ref and j.stat().st_mtime < ref:
            errs.append(f"C4: journal m{n} plus ancien que `WORKSPACE.txt` — il vient d'une run "
                        "précédente")
        cap = ws / 'tests' / 'e2e' / 'verification' / f'm{n}'
        if not cap.is_dir() or not any(cap.rglob('*.png')):
            errs.append(f"C5: aucune capture dans `tests/e2e/verification/m{n}/` — rien ne prouve que "
                        "le vérificateur a rejoué le jalon sur l'app déployée")

    # C6 — avancement
    av_p = d / 'avancement.json'
    av = None
    if not av_p.exists() or av_p.stat().st_size == 0:
        errs.append(f"C6: `{DOCS}/avancement.json` absent/vide — l'avancement n'est pas tenu")
    else:
        av, e = _json(av_p)
        if not isinstance(av, dict):
            errs.append(f"C6: `avancement.json` illisible ({e or 'pas un objet'})")
            av = None
    if av is not None:
        if av.get('phase') not in PHASES:
            errs.append(f"C6: `avancement.json` phase `{av.get('phase')}` hors de {list(PHASES)}")
        elif av.get('phase') != 'fini':
            errs.append(f"C6: `avancement.json` en phase `{av.get('phase')}` — le nœud n'est fini "
                        "qu'en phase `fini`")
        if not isinstance(av.get('tour'), int) or av.get('tour') < 0:
            errs.append("C6: `avancement.json` : `tour` doit être un entier ≥ 0")
        if not isinstance(av.get('maj'), str) or not re.match(r'\d{4}-\d{2}-\d{2}T', av.get('maj') or ''):
            errs.append("C6: `avancement.json` : `maj` doit être une date ISO")
        jl = av.get('jalons')
        if not isinstance(jl, list):
            errs.append("C6: `avancement.json` : `jalons` doit être une liste")
            jl = []
        vus = {}
        for x in jl:
            if not isinstance(x, dict) or not x.get('id') or x.get('statut') not in STATUTS_JALON:
                errs.append(f"C6: `avancement.json` : jalon mal formé {x!r} (id, titre, statut parmi "
                            f"{list(STATUTS_JALON)})")
                continue
            mm = re.search(r'\d+', str(x['id']))
            if mm:
                vus[int(mm.group())] = x['statut']
        for n, _ in attendus:
            if vus.get(n) != 'fait':
                errs.append(f"C6: `avancement.json` : jalon M{n} au statut `{vus.get(n, 'absent')}` "
                            "— attendu `fait`")

    # C7 — URL de production
    au = d / 'app-url.txt'
    url = _txt(au).strip().splitlines()[0].strip() if au.exists() and _txt(au).strip() else ''
    if not re.match(r'https?://\S+$', url):
        errs.append(f"C7: `{DOCS}/app-url.txt` ne porte pas d'URL http(s) — l'app en ligne est "
                    "introuvable pour la revue")

    if os.environ.get('WEBAPP_VIDEO', '1').strip() == '0':
        return _sans_video(ws, errs, av)

    # C8 — table de montage
    vu = ws / 'video' / 'video-url.txt'
    vurl = _txt(vu).strip().splitlines()[0].strip() if vu.exists() and _txt(vu).strip() else ''
    if not re.match(r'https?://\S+$', vurl):
        errs.append("C8: `video/video-url.txt` ne porte pas d'URL http(s) — la vidéo n'est pas "
                    "publiée")
    elif 'code=' not in vurl:
        errs.append("C8: `video/video-url.txt` sans `?code=` — le client ne pourra pas ouvrir la "
                    "table de montage")

    # C9 — versions de la vidéo
    vers, e = lire_versions(ws)
    tours_video = set()
    if vers is None:
        errs.append(f"C9: `video/versions.json` absent ou illisible ({e or 'absent'})")
    elif not isinstance(vers, dict) or not isinstance(vers.get('versions'), list) or not vers['versions']:
        errs.append("C9: `video/versions.json` doit porter `{\"versions\": [ … ]}` non vide")
    else:
        for i, v in enumerate(vers['versions'], 1):
            if not isinstance(v, dict):
                errs.append(f"C9: version n°{i} n'est pas un objet")
                continue
            if v.get('version') != f'V{i}':
                errs.append(f"C9: la version n°{i} s'appelle `{v.get('version')}` (attendu V{i}) — "
                            "chaque version livrée est figée à la suite de la précédente")
            if not isinstance(v.get('tour'), int):
                errs.append(f"C9: version V{i} : `tour` doit être un entier")
            else:
                tours_video.add(v['tour'])
            if i == 1 and v.get('tour') != 0:
                errs.append("C9: V1 doit être la vidéo du tour 0 (la construction initiale)")
            if not isinstance(v.get('date'), str) or not v.get('date'):
                errs.append(f"C9: version V{i} sans `date`")
            for k in ('sequences', 'refilmees'):
                if not isinstance(v.get(k), list) or not v.get(k):
                    errs.append(f"C9: version V{i} : `{k}` doit être une liste non vide")
            if isinstance(v.get('sequences'), list) and isinstance(v.get('refilmees'), list):
                hors = [s for s in v['refilmees'] if s not in v['sequences']]
                if hors:
                    errs.append(f"C9: version V{i} refilme des séquences qu'elle ne contient pas : "
                                + ', '.join(map(str, hors)))

    # C10 — tours de retours
    dernier = 0
    for n, f, j, e in tours_retours(ws):
        if j is None:
            errs.append(f"C10: `retours/{f.name}` illisible ({e})")
            continue
        dernier = max(dernier, n)
        if j.get('statut') != 'traite':
            errs.append(f"C10: tour {n} au statut `{j.get('statut')}` — ses retours sont à traiter "
                        "(mode retours)")
        elif vers is not None and n not in tours_video:
            errs.append(f"C10: tour {n} marqué `traite` sans version de vidéo au tour {n} dans "
                        "`video/versions.json` — les séquences touchées n'ont pas été refilmées")
    if av is not None and isinstance(av.get('tour'), int) and av['tour'] != dernier:
        errs.append(f"C10: `avancement.json` porte le tour {av['tour']}, le dernier tour de retours "
                    f"est {dernier}")

    pm = d / 'project-memory.md'
    if pm.exists() and len(_txt(pm)) > 2000:
        errs.append(f"C11: `project-memory.md` fait {len(_txt(pm))} car (> 2000)")

    return errs


def _sans_video(ws, errs, av):
    """C10 et C11 sans la vidéo (WEBAPP_VIDEO=0) : chaque tour de retours est traité, l'avancement porte le dernier."""
    dernier = 0
    for n, f, j, e in tours_retours(ws):
        if j is None:
            errs.append(f"C10: `retours/{f.name}` illisible ({e})")
            continue
        dernier = max(dernier, n)
        if j.get('statut') != 'traite':
            errs.append(f"C10: tour {n} au statut `{j.get('statut')}` — ses retours sont à traiter "
                        "(mode retours)")
    if av is not None and isinstance(av.get('tour'), int) and av['tour'] != dernier:
        errs.append(f"C10: `avancement.json` porte le tour {av['tour']}, le dernier tour de retours "
                    f"est {dernier}")
    pm = ws / DOCS / 'project-memory.md'
    if pm.exists() and len(_txt(pm)) > 2000:
        errs.append(f"C11: `project-memory.md` fait {len(_txt(pm))} car (> 2000)")
    return errs
