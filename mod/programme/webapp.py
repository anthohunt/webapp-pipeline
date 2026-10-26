#!/usr/bin/env python3
"""Programme du module « webapp » : l'état d'une run de la pipeline web app en 3 étapes.

Design (docs/2026-10-24-webapp-3-etapes-design.md) et contrat des fichiers (docs/2026-10-24-webapp-3-etapes-contrat.md)
à la racine du dépôt. Le mod (hooks/) dessine ; ce programme tient l'état, dans les fichiers de la run sur le serveur,
et parle au moteur flux (gate de l'étape 1, lancement et suivi de l'étape 2).

Une commande par geste : `webapp.py <commande>`, paramètres en JSON sur l'entrée standard, réponse en JSON sur la
dernière ligne de la sortie : {"ok": true, "resultat": …} ou {"ok": false, "refus": "…"}.

Bibliothèque standard seule. Tests : python3 -m unittest discover -s programme/tests
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

ICI = pathlib.Path(__file__).resolve().parent
DEPOT = ICI.parent.parent    # racine du dépôt webapp-pipeline
GRAPHES = pathlib.Path(os.environ.get('WEBAPP_GRAPHES') or DEPOT / 'workflows')


def _racine_runs():
    """Les runs : WEBAPP_RUNS, sinon le `workspace_root` du graphe (comme le moteur), sinon ~/webapp-runs."""
    if os.environ.get('WEBAPP_RUNS'):
        return pathlib.Path(os.environ['WEBAPP_RUNS'])
    try:
        r = json.loads((GRAPHES / 'webapp.json').read_text(encoding='utf-8')).get('workspace_root')
    except Exception:
        r = None
    return pathlib.Path(os.path.expandvars(os.path.expanduser(r or '~/webapp-runs')))


RUNS = _racine_runs()
# Le moteur flux (dépendance) : FLUX_HOME, sinon le clone conseillé par le README (vendor/flux).
FLUX = pathlib.Path(os.environ.get('FLUX_HOME') or os.environ.get('WEBAPP_FLUX') or DEPOT / 'vendor' / 'flux')
# Les outils et le graphe de la pipeline vivent dans ce dépôt ; les tests les remplacent par des faux.
OUTILS = pathlib.Path(os.environ.get('WEBAPP_OUTILS') or DEPOT / 'tools')
# Le dossier d'état du moteur (FLUX_STATE_DIR, comme socle.dossier_state()).
ETAT_FLUX = pathlib.Path(os.environ.get('FLUX_STATE_DIR') or FLUX / 'state')
WORKFLOW = 'webapp'
ETAT_MODULE = 'state/module-webapp.json'
JOURNAL = 'state/module-webapp.jsonl'
LIRE_MAX = 200_000


class Refus(Exception):
    pass


# ───────────────────────────────────────── fichiers

def maintenant():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def charger_json(chemin, defaut=None):
    try:
        return json.loads(pathlib.Path(chemin).read_text(encoding='utf-8'))
    except Exception:
        return defaut


def ecrire_atomique(chemin, texte):
    chemin = pathlib.Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_name(chemin.name + '.tmp')
    tmp.write_text(texte, encoding='utf-8')
    os.replace(tmp, chemin)


def ecrire_json(chemin, valeur):
    ecrire_atomique(chemin, json.dumps(valeur, ensure_ascii=False, indent=2) + '\n')


def journaliser(ws, type_, donnees=None):
    p = pathlib.Path(ws) / JOURNAL
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'a': maintenant(), 'type': type_, **(donnees or {})}, ensure_ascii=False) + '\n')


def parcours():
    return json.loads((ICI / 'parcours.json').read_text(encoding='utf-8'))


def toutes_sous_etapes(p=None):
    p = p or parcours()
    return [s for e in p['etapes'] for s in e['sous_etapes']]


def sous_etape(sid):
    for s in toutes_sous_etapes():
        if s['id'] == sid:
            return s
    raise Refus(f'sous-étape inconnue : {sid}')


# ───────────────────────────────────────── runs

def slug(texte):
    s = re.sub(r'[^a-z0-9-]+', '-', str(texte or '').lower()).strip('-')
    return s[:40]


def lire_entete(ws):
    """WORKSPACE.txt : « clé: valeur » par ligne (écrit par flux/runtime/new-run.py)."""
    vals = {}
    try:
        for l in (pathlib.Path(ws) / 'WORKSPACE.txt').read_text(encoding='utf-8').splitlines():
            if ':' in l:
                k, v = l.split(':', 1)
                vals[k.strip()] = v.strip()
    except Exception:
        pass
    return vals


def runs_du_projet(projet):
    if not RUNS.is_dir():
        return []
    trouves = []
    for d in RUNS.iterdir():
        if not d.is_dir() or d.name.startswith('_'):
            continue
        ent = lire_entete(d)
        if ent.get('workflow', WORKFLOW) == WORKFLOW and slug(ent.get('projet')) == projet:
            trouves.append((ent.get('ouvert', ''), d))
    return [d for _, d in sorted(trouves)]


def workspace(run):
    if not run or '/' in run or run.startswith('.'):
        raise Refus(f'run invalide : {run!r}')
    ws = RUNS / run
    if not (ws / 'WORKSPACE.txt').exists():
        raise Refus(f'run introuvable : {run}')
    return ws


def creer_run(projet):
    r = subprocess.run([sys.executable, str(FLUX / 'runtime' / 'new-run.py'), WORKFLOW, projet],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise Refus(f'création de la run refusée par le moteur : {(r.stderr or r.stdout).strip()[-400:]}')
    runs = runs_du_projet(projet)
    if not runs:
        raise Refus('la run a été créée mais reste introuvable (WORKSPACE.txt sans « projet: »)')
    return runs[-1]


def noeud(n):
    """L'identifiant du nœud n du graphe (concevoir, construire, revue) : lu dans le graphe, jamais supposé."""
    g = charger_json(GRAPHES / f'{WORKFLOW}.json', {}) or {}
    for nd in g.get('nodes') or []:
        if nd.get('n') == n:
            return nd['id']
    return {1: 'concevoir', 2: 'construire', 3: 'revue'}[n]


def etat_noeud_flux(ws, nid):
    return charger_json(ETAT_FLUX / WORKFLOW / pathlib.Path(ws).name / f'{nid}.json', {}) or {}


# ───────────────────────────────────────── état du module

def etat_module(ws):
    e = charger_json(pathlib.Path(ws) / ETAT_MODULE)
    if e:
        return e
    p = parcours()
    e = {
        'projet': lire_entete(ws).get('projet'),
        'cree': maintenant(),
        'sous_etapes': {s['id']: {'etat': 'a_faire'} for s in toutes_sous_etapes(p)},
        'decisions': [],
        'sessions': [],
        'lance_le': None,
        'close': False,
    }
    e['sous_etapes']['E1.1'] = {'etat': 'en_cours', 'depuis': maintenant()}
    return e


def sauver(ws, e):
    ecrire_json(pathlib.Path(ws) / ETAT_MODULE, e)


def lire_texte(ws, rel):
    try:
        return (pathlib.Path(ws) / rel).read_text(encoding='utf-8').strip() or None
    except Exception:
        return None


def construction(ws):
    """Le suivi de l'étape 2 (tools/webapp-etat.py, contrat). Jamais d'exception."""
    outil = OUTILS / 'webapp-etat.py'
    if not outil.exists():
        return {'indisponible': 'tools/webapp-etat.py absent'}
    try:
        r = subprocess.run([sys.executable, str(outil), str(ws)], capture_output=True, text=True, timeout=25)
        ligne = (r.stdout or '').strip().splitlines()[-1] if (r.stdout or '').strip() else ''
        return json.loads(ligne) if ligne else {'indisponible': (r.stderr or '').strip()[-300:] or 'réponse vide'}
    except Exception as exc:
        return {'indisponible': str(exc)[:300]}


def revue_json(ws):
    return charger_json(pathlib.Path(ws) / 'docs/pipeline/revue.json', {'tours': []}) or {'tours': []}


def tour_attendu(ws):
    """Le tour de construction en cours : 0 au départ, N après le N-ième verdict « retours »."""
    return sum(1 for t in revue_json(ws).get('tours', []) if t.get('verdict') == 'retours')


def construction_finie(c, tour):
    if not c or c.get('indisponible') or c.get('en_cours'):
        return False
    return c.get('phase') == 'fini' and int(c.get('tour') or 0) >= tour and bool((c.get('video') or {}).get('url'))


def vue(ws, e=None, c=None):
    ws = pathlib.Path(ws)
    e = e or etat_module(ws)
    p = parcours()
    tour = tour_attendu(ws)
    lance = bool(e.get('lance_le'))
    if c is None:
        c = construction(ws) if lance else None
    finie = construction_finie(c, tour)
    tours = revue_json(ws).get('tours', [])
    decisions = e.get('decisions', [])

    def etat_derive(sid):
        se = e['sous_etapes'].get(sid, {'etat': 'a_faire'})
        if not sid.startswith('E1') and not sid.startswith('E3'):
            # étape 2 : constatée dans le suivi du moteur
            if not lance:
                return {'etat': 'a_faire'}
            phase = (c or {}).get('phase')
            bloque = (c or {}).get('bloque')
            retours = tour > 0 and not finie
            if sid == 'E2.1':
                if retours and (phase == 'retours' or (c or {}).get('en_cours') and phase == 'fini'):
                    return {'etat': 'bloquee' if bloque else 'en_cours'}
                if finie or phase in ('tournage', 'fini'):
                    return {'etat': 'validee'}
                return {'etat': 'bloquee' if bloque else 'en_cours'}
            if finie:
                return {'etat': 'validee'}
            if phase == 'tournage':
                return {'etat': 'bloquee' if bloque else 'en_cours'}
            return {'etat': 'a_faire'}
        if sid == 'E3.1':
            if e.get('close'):
                return {'etat': 'validee', 'citation': (tours[-1] if tours else {}).get('citation')}
            return {'etat': 'en_cours' if finie else 'a_faire'}
        return se

    etapes = []
    for et in p['etapes']:
        sous = []
        for s in et['sous_etapes']:
            d = etat_derive(s['id'])
            sous.append({
                'id': s['id'], 'titre': s['titre'], 'qui': s['qui'], 'etat': d.get('etat', 'a_faire'),
                'depuis': d.get('depuis'), 'valide_le': d.get('valide_le'), 'citation': d.get('citation'),
                'sorties': [{'chemin': x, 'existe': (ws / x).exists()} for x in s.get('sortie', [])],
                'decisions': [x for x in decisions if x.get('sous_etape') == s['id']],
            })
        faite = all(x['etat'] == 'validee' for x in sous)
        etapes.append({'n': et['n'], 'titre': et['titre'], 'resume': et['resume'], 'sous_etapes': sous,
                       'etat': 'faite' if faite else 'ouverte'})
    for et in etapes:
        if et['etat'] == 'ouverte' and not any(x['etat'] != 'a_faire' for x in et['sous_etapes']):
            et['etat'] = 'fermee'
    courante = next((et['n'] for et in etapes if et['etat'] != 'faite'), 3)
    if tour and not finie and not e.get('close'):
        courante = 2

    liens = {
        'maquette': lire_texte(ws, 'docs/pipeline/design/mockup-public-url.txt'),
        'app': lire_texte(ws, 'docs/pipeline/app-url.txt') or (c or {}).get('app_url'),
        'video': lire_texte(ws, 'video/video-url.txt') or ((c or {}).get('video') or {}).get('url'),
    }
    v = {
        'run': ws.name, 'projet': e.get('projet'), 'workspace': str(ws), 'etape_courante': courante,
        'etapes': etapes, 'liens': liens, 'construction': c, 'tour': tour, 'tours': tours,
        'close': bool(e.get('close')), 'lance_le': e.get('lance_le'),
        'version_video': ((c or {}).get('video') or {}).get('version'),
    }
    v['regles'] = p['regles_communes']
    v['attend'] = ce_qui_attend(v)
    en = next((s for et in etapes for s in et['sous_etapes'] if s['etat'] in ('en_cours', 'a_valider', 'bloquee')), None)
    v['sous_etape_courante'] = en['id'] if en else None
    v['consigne'] = sous_etape(en['id'])['consigne'] if en else None
    n1 = noeud(1)
    d1 = ETAT_FLUX / WORKFLOW / ws.name / n1
    v['brief'] = {'noeud': n1, 'sys': str(d1 / 'sys.md'), 'brief': str(d1 / 'brief.md')}
    return v


def ce_qui_attend(v):
    if v['close']:
        return None
    toutes = [s for et in v['etapes'] for s in et['sous_etapes']]
    for s in toutes:
        if s['id'].startswith('E1'):
            if s['etat'] == 'a_valider':
                return {'quoi': f'valider {s["titre"].lower()}', 'sous_etape': s['id']}
            if s['etat'] == 'en_cours':
                if s['id'] == 'E1.1':
                    return {'quoi': 'le pitch de l’app (le tien ou celui du client)', 'sous_etape': s['id']}
                if s['id'] == 'E1.2':
                    return {'quoi': 'répondre aux questions d’usage', 'sous_etape': s['id']}
                if s['id'] == 'E1.7':
                    return {'quoi': 'faire tester la maquette au client', 'sous_etape': s['id']}
                return None
            if s['etat'] == 'a_faire':
                return None
    if not v['lance_le']:
        return {'quoi': 'lancer la construction', 'action': 'lancer'}
    c = v['construction'] or {}
    if c.get('bloque') and not c.get('en_cours'):
        return {'quoi': f'construction bloquée : {c["bloque"]}', 'action': 'lancer'}
    e31 = next(s for s in toutes if s['id'] == 'E3.1')
    if e31['etat'] == 'en_cours':
        return {'quoi': 'montrer la vidéo et l’app au client', 'sous_etape': 'E3.1'}
    return None


# ───────────────────────────────────────── commandes

def cmd_liste(a):
    out = []
    if RUNS.is_dir():
        for d in sorted(RUNS.iterdir()):
            ent = lire_entete(d)
            if d.is_dir() and not d.name.startswith('_') and ent.get('workflow', WORKFLOW) == WORKFLOW:
                out.append({'run': d.name, 'projet': ent.get('projet'), 'ouvert': ent.get('ouvert'),
                            'module': (d / ETAT_MODULE).exists()})
    return {'runs': out}


def cmd_ouvrir(a):
    projet = slug(a.get('projet'))
    if not projet:
        raise Refus('nom de projet invalide')
    runs = runs_du_projet(projet)
    neuf = not runs
    ws = creer_run(projet) if neuf else runs[-1]
    e = etat_module(ws)
    if not (ws / ETAT_MODULE).exists():
        neuf = True
    sess = a.get('session')
    if sess and sess not in e['sessions']:
        e['sessions'].append(sess)
    sauver(ws, e)
    journaliser(ws, 'ouverture', {'session': sess, 'neuf': neuf})
    preparer_brief(ws)
    v = vue(ws, e)
    v['neuf'] = neuf
    return v


def preparer_brief(ws):
    """Le brief du nœud 1 (objectif, check-list, consignes du graphe) écrit par le moteur, que l'agent lit."""
    try:
        subprocess.run([sys.executable, str(FLUX / 'runtime' / 'run-node.py'), WORKFLOW, noeud(1),
                        '--workspace', str(ws), '--brief-only'], capture_output=True, text=True, timeout=60)
    except Exception:
        pass


def cmd_etat(a):
    return vue(workspace(a.get('run')))


def exiger_citation(a):
    c = str(a.get('citation') or '').strip()
    if not c:
        raise Refus("citation obligatoire : les mots de l'utilisateur, mot pour mot")
    return c


def cmd_avancer(a):
    ws = workspace(a.get('run'))
    sid = a.get('sous_etape')
    s = sous_etape(sid)
    if not sid.startswith('E1.') or s['qui'] == 'programme':
        raise Refus(f'{sid} ne s’avance pas à la main : ' + ('outil `cloturer`' if sid == 'E1.8' else 'le programme la constate'))
    cible = a.get('etat')
    if cible not in ('en_cours', 'a_valider', 'validee'):
        raise Refus('etat attendu : en_cours, a_valider ou validee')
    e = etat_module(ws)
    if e.get('close'):
        raise Refus('la run est close')
    ordre = [x['id'] for x in toutes_sous_etapes() if x['id'].startswith('E1.')]
    i = ordre.index(sid)
    if i and e['sous_etapes'][ordre[i - 1]]['etat'] != 'validee':
        raise Refus(f'{ordre[i - 1]} n’est pas encore validée')
    manquants = [x for x in s.get('sortie', []) if not (ws / x).exists()]
    if cible in ('a_valider', 'validee') and manquants:
        raise Refus('sorties manquantes : ' + ', '.join(manquants))
    se = {'etat': cible, 'depuis': maintenant()}
    if cible == 'validee':
        se['citation'] = exiger_citation(a)
        se['valide_le'] = maintenant()
        if i + 1 < len(ordre) and e['sous_etapes'][ordre[i + 1]]['etat'] == 'a_faire':
            e['sous_etapes'][ordre[i + 1]] = {'etat': 'en_cours', 'depuis': maintenant()}
    e['sous_etapes'][sid] = se
    sauver(ws, e)
    journaliser(ws, 'avancer', {'sous_etape': sid, 'etat': cible, 'citation': se.get('citation')})
    return {'sous_etape': sid, 'etat': cible}


def cmd_decision(a):
    ws = workspace(a.get('run'))
    sid = a.get('sous_etape')
    sous_etape(sid)
    d = {'a': maintenant(), 'sous_etape': sid, 'resume': str(a.get('resume') or '').strip(),
         'citation': exiger_citation(a), 'option': a.get('option')}
    if not d['resume']:
        raise Refus('resume obligatoire')
    e = etat_module(ws)
    e['decisions'].append(d)
    sauver(ws, e)
    journaliser(ws, 'decision', d)
    return {'decision': d}


def cmd_rouvrir(a):
    ws = workspace(a.get('run'))
    sid = a.get('sous_etape')
    if not str(sid).startswith('E1.'):
        raise Refus('seules les sous-étapes de l’étape 1 se rouvrent ; pour l’app livrée, passe par la revue')
    sous_etape(sid)
    raison = str(a.get('raison') or '').strip()
    if not raison:
        raise Refus('raison obligatoire')
    e = etat_module(ws)
    if e.get('lance_le'):
        raise Refus('la construction est lancée : les changements passent par la revue (retours)')
    ordre = [x['id'] for x in toutes_sous_etapes() if x['id'].startswith('E1.')]
    for x in ordre[ordre.index(sid) + 1:]:
        if e['sous_etapes'][x]['etat'] != 'validee':
            e['sous_etapes'][x] = {'etat': 'a_faire'}
    e['sous_etapes'][sid] = {'etat': 'en_cours', 'depuis': maintenant(), 'rouvert': raison}
    sauver(ws, e)
    journaliser(ws, 'rouvrir', {'sous_etape': sid, 'raison': raison})
    return {'sous_etape': sid, 'etat': 'en_cours'}


def cmd_cloturer(a):
    """Fin de l'étape 1 : le gate du nœud 1, par le moteur. Vert → E1.8 validée."""
    ws = workspace(a.get('run'))
    e = etat_module(ws)
    if e['sous_etapes']['E1.7']['etat'] != 'validee':
        raise Refus('le test de la maquette (E1.7) n’est pas validé')
    n1 = noeud(1)
    r = subprocess.run([sys.executable, str(FLUX / 'runtime' / 'run-node.py'), WORKFLOW, n1, '--workspace', str(ws)],
                       capture_output=True, text=True, timeout=300)
    st = etat_noeud_flux(ws, n1)
    vert = r.returncode == 0 and st.get('statut') == 'vert'
    journaliser(ws, 'cloturer', {'vert': vert, 'rc': r.returncode, 'erreurs': st.get('erreurs')})
    if not vert:
        erreurs = st.get('erreurs') or []
        manques = st.get('livrables_manquants') or []
        detail = '; '.join([str(x) for x in erreurs][:12] + [f'manquant : {m}' for m in manques][:12])
        raise Refus('contrôle de l’étape 1 rouge — ' + (detail or (r.stderr or '').strip()[-600:]))
    e['sous_etapes']['E1.8'] = {'etat': 'validee', 'valide_le': maintenant(), 'citation': 'gate vert'}
    sauver(ws, e)
    return {'gate': 'vert'}


def cmd_lancer(a):
    ws = workspace(a.get('run'))
    e = etat_module(ws)
    if e.get('close'):
        raise Refus('la run est close')
    if e['sous_etapes']['E1.8']['etat'] != 'validee':
        raise Refus('l’étape 1 n’est pas close (outil `cloturer`)')
    outil = OUTILS / 'webapp-lancer.py'
    if not outil.exists():
        raise Refus('tools/webapp-lancer.py absent')
    argv = [sys.executable, str(outil), str(ws)] + (['--dry-run'] if a.get('dry_run') else [])
    r = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    ligne = (r.stdout or '').strip().splitlines()[-1] if (r.stdout or '').strip() else ''
    try:
        rep = json.loads(ligne)
    except Exception:
        raise Refus(f'lancement illisible (code {r.returncode}) : {(r.stderr or ligne).strip()[-400:]}')
    if not rep.get('ok'):
        raise Refus(f'lancement refusé : {rep.get("refus") or rep.get("message") or rep}')
    if not a.get('dry_run'):
        e['lance_le'] = e.get('lance_le') or maintenant()
        e.setdefault('lancements', []).append({'a': maintenant(), 'mode': rep.get('mode'), 'tmux': rep.get('tmux')})
        sauver(ws, e)
        journaliser(ws, 'lancer', rep)
    return rep


def cmd_retours(a):
    ws = workspace(a.get('run'))
    v = vue(ws)
    if next(s for s in v['etapes'][2]['sous_etapes'] if s['id'] == 'E3.1')['etat'] != 'en_cours':
        raise Refus('pas de revue en cours : la construction de ce tour n’est pas finie')
    liste = a.get('retours') or []
    if not isinstance(liste, list) or not liste:
        raise Refus('retours : une liste non vide')
    n = v['tour'] + 1
    propres = []
    for i, r in enumerate(liste, 1):
        dit = str((r or {}).get('dit') or '').strip()
        attendu = str((r or {}).get('attendu') or '').strip()
        if not dit or not attendu:
            raise Refus(f'retour {i} : « dit » (mots exacts) et « attendu » (critère vérifiable) obligatoires')
        propres.append({'id': f'R{i}', 'dit': dit, 'histoire': r.get('histoire') or None,
                        'ecran': r.get('ecran') or None, 'attendu': attendu})
    doc = {'tour': n, 'date': maintenant(), 'statut': 'a-traiter', 'citation': exiger_citation(a), 'retours': propres}
    base = ws / 'docs/pipeline/retours'
    ecrire_json(base / f'tour-{n}.json', doc)
    md = [f'# Retours du client — tour {n}', '', f'Reçus le {doc["date"]}, transmis par l’opérateur : « {doc["citation"]} »', '']
    for r in propres:
        md += [f'## {r["id"]}' + (f' · {r["histoire"]}' if r['histoire'] else '') + (f' · écran {r["ecran"]}' if r['ecran'] else ''),
               f'• Dit : « {r["dit"]} »', f'• Attendu : {r["attendu"]}', '']
    ecrire_atomique(base / f'tour-{n}.md', '\n'.join(md))
    journaliser(ws, 'retours', {'tour': n, 'nombre': len(propres)})
    return {'tour': n, 'fichier': f'docs/pipeline/retours/tour-{n}.json', 'retours': propres}


def cmd_revue(a):
    ws = workspace(a.get('run'))
    verdict = a.get('verdict')
    if verdict not in ('good', 'retours'):
        raise Refus('verdict : good ou retours')
    citation = exiger_citation(a)
    v = vue(ws)
    if next(s for s in v['etapes'][2]['sous_etapes'] if s['id'] == 'E3.1')['etat'] != 'en_cours':
        raise Refus('pas de revue en cours : la construction de ce tour n’est pas finie')
    n = v['tour'] + 1
    if verdict == 'retours' and not (ws / f'docs/pipeline/retours/tour-{n}.json').exists():
        raise Refus(f'enregistre d’abord les retours du tour {n} (outil `retours`)')
    rj = revue_json(ws)
    rj.setdefault('tours', []).append({'tour': n, 'verdict': verdict, 'date': maintenant(), 'citation': citation,
                                       'version_video': v.get('version_video')})
    ecrire_json(ws / 'docs/pipeline/revue.json', rj)
    journaliser(ws, 'revue', {'tour': n, 'verdict': verdict, 'citation': citation})
    e = etat_module(ws)
    if verdict == 'good':
        e['close'] = True
        e['close_le'] = maintenant()
        sauver(ws, e)
        try:
            subprocess.run([sys.executable, str(FLUX / 'runtime' / 'run-node.py'), WORKFLOW, noeud(3),
                            '--workspace', str(ws)], capture_output=True, text=True, timeout=120)
        except Exception:
            pass
        return {'tour': n, 'verdict': 'good', 'close': True}
    rep = cmd_lancer({'run': ws.name})
    return {'tour': n, 'verdict': 'retours', 'relance': rep}


def cmd_lire(a):
    ws = workspace(a.get('run'))
    rel = str(a.get('chemin') or '')
    p = (ws / rel).resolve()
    if not str(p).startswith(str(ws.resolve()) + os.sep):
        raise Refus('chemin hors de la run')
    if not p.is_file():
        raise Refus(f'fichier absent : {rel}')
    return {'chemin': rel, 'contenu': p.read_text(encoding='utf-8', errors='replace')[:LIRE_MAX]}


def cmd_evenement(a):
    ws = workspace(a.get('run'))
    journaliser(ws, str(a.get('type') or 'evenement'), a.get('donnees') or {})
    return {}


def cmd_pitch(a):
    """E1.1 : le premier message de l'utilisateur après l'ouverture est le pitch ; il se garde mot pour mot."""
    ws = workspace(a.get('run'))
    e = etat_module(ws)
    if e['sous_etapes']['E1.1']['etat'] != 'en_cours':
        return {'deja': True}
    texte = exiger_citation(a)
    ecrire_atomique(ws / 'docs/pipeline/pitch.md', f'# Le pitch\n\nReçu le {maintenant()}, mot pour mot :\n\n> ' +
                    texte.replace('\n', '\n> ') + '\n')
    e['sous_etapes']['E1.1'] = {'etat': 'validee', 'valide_le': maintenant(), 'citation': texte}
    e['sous_etapes']['E1.2'] = {'etat': 'en_cours', 'depuis': maintenant()}
    sauver(ws, e)
    journaliser(ws, 'pitch', {'citation': texte})
    return {'sous_etape': 'E1.1', 'etat': 'validee'}


COMMANDES = {
    'liste': cmd_liste, 'ouvrir': cmd_ouvrir, 'etat': cmd_etat, 'avancer': cmd_avancer, 'decision': cmd_decision,
    'rouvrir': cmd_rouvrir, 'cloturer': cmd_cloturer, 'lancer': cmd_lancer, 'retours': cmd_retours,
    'revue': cmd_revue, 'lire': cmd_lire, 'evenement': cmd_evenement, 'pitch': cmd_pitch,
}


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDES:
        print(json.dumps({'ok': False, 'refus': 'commande inconnue ; attendu : ' + ', '.join(COMMANDES)}))
        return 2
    try:
        brut = sys.stdin.read() if not sys.stdin.isatty() else ''
        args = json.loads(brut) if brut.strip() else {}
        res = COMMANDES[argv[1]](args)
        print(json.dumps({'ok': True, 'resultat': res}, ensure_ascii=False))
        return 0
    except Refus as r:
        print(json.dumps({'ok': False, 'refus': str(r)}, ensure_ascii=False))
        return 1
    except Exception as exc:
        print(json.dumps({'ok': False, 'refus': f'erreur du programme : {type(exc).__name__}: {exc}'}, ensure_ascii=False))
        return 3


if __name__ == '__main__':
    sys.exit(main(sys.argv))
