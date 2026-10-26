#!/usr/bin/env python3
"""Où en est l'étape 2 (« construire ») d'une run de la pipeline web app — une ligne JSON sur stdout.

    python3 webapp-etat.py <ws>

Contrat : docs/2026-10-24-webapp-3-etapes-contrat.md (commandes). Le module /webapp
(mod/programme/webapp.py) lit en_cours, phase, tour, jalons[{id,titre,statut}],
app_url, video{url,version}, bloque ; le reste (derniere_passe, lanceur, revue, retours_a_traiter,
source) est du détail pour qui veut comprendre.

LECTURE PURE : rien ne s'écrit, nulle part. En particulier, ni validate.py (son hook réécrit
run-report-bundle/ du workspace) ni socle.dossier_run (il crée le dossier d'état) ne sont appelés.

Sources, dans l'ordre :
• docs/pipeline/avancement.json, tenu par le nœud (skill pipeline-step4) ;
• à défaut (run d'avant les 3 étapes) : roadmap-approved.json + les jalons cochés de status.md ;
• state/lanceur.json (tools/webapp-lancer.py) et l'état du nœud construire dans flux/state/.
"""
import json, os, pathlib, re, subprocess, sys

ICI = pathlib.Path(__file__).resolve().parent
DEPOT = ICI.parent    # racine du dépôt webapp-pipeline
# Le moteur flux est une dépendance : FLUX_HOME, sinon le clone conseillé par le README (vendor/flux).
FLUX = pathlib.Path(os.environ.get('FLUX_HOME') or DEPOT / 'vendor' / 'flux')
sys.path.insert(0, str(FLUX / 'runtime'))
import socle  # noqa: E402

WF = 'webapp'
NOEUD = 'construire'
DOCS = 'docs/pipeline'


def lire_json(p, defaut=None):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:
        return defaut


def lire_ligne(p):
    try:
        for l in pathlib.Path(p).read_text(encoding='utf-8', errors='replace').splitlines():
            if l.strip():
                return l.strip()
    except Exception:
        pass
    return None


def tmux_vivant(sess):
    if not sess:
        return False
    try:
        return subprocess.call(['tmux', 'has-session', '-t', str(sess)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except Exception:
        return False


def dossier_etat(ws):
    """Le dossier d'état du moteur pour cette run, SANS le créer (socle.dossier_run fait mkdir)."""
    nom = pathlib.Path(ws).name
    if socle.run_confinee(ws):
        return socle.racine_runs_mesure() / 'state' / WF / nom
    return socle.dossier_state() / WF / nom


def coches(txt):
    return sorted({int(m.group(1)) for m in
                   re.finditer(r'\[x\][^\n]*?(?:milestone|jalon)\s*#?\s*(\d+)', txt, re.I)} |
                  {int(m.group(1)) for m in
                   re.finditer(r'(?:milestone|jalon)\s*#?\s*(\d+)[^\n]*?\[x\]', txt, re.I)})


def jalons_feuille(ws):
    j = lire_json(pathlib.Path(ws) / DOCS / 'roadmap-approved.json', {}) or {}
    out = []
    for m in (j.get('milestones') or j.get('jalons') or []):
        v = (m.get('n') or m.get('id') or m.get('numero')) if isinstance(m, dict) else m
        mm = re.search(r'\d+', str(v or ''))
        if mm:
            out.append((int(mm.group()), (m.get('titre') or m.get('title') or '') if isinstance(m, dict) else ''))
    return sorted(set(out))


def tours_retours(ws):
    d = pathlib.Path(ws) / DOCS / 'retours'
    out = []
    for f in (sorted(d.glob('tour-*.json')) if d.is_dir() else []):
        m = re.fullmatch(r'tour-(\d+)\.json', f.name)
        if m:
            out.append((int(m.group(1)), lire_json(f, {}) or {}))
    return sorted(out, key=lambda x: x[0])


def etat(ws):
    ws = pathlib.Path(ws).resolve()
    if not (ws / 'WORKSPACE.txt').is_file():
        return {'indisponible': f'workspace introuvable : {ws}'}
    d = ws / DOCS
    st_dir = dossier_etat(ws)
    noeud = lire_json(st_dir / f'{NOEUD}.json', {}) or {}
    passages = noeud.get('passages') or []
    lanceur = lire_json(ws / 'state' / 'lanceur.json', {}) or {}
    av = lire_json(d / 'avancement.json')
    retours = tours_retours(ws)
    a_traiter = [n for n, j in retours if j.get('statut') == 'a-traiter']

    # ── jalons, phase, tour
    feuille = jalons_feuille(ws)
    if isinstance(av, dict) and isinstance(av.get('jalons'), list):
        source = 'avancement'
        jalons = [{'id': x.get('id'), 'titre': x.get('titre') or '', 'statut': x.get('statut')}
                  for x in av['jalons'] if isinstance(x, dict)]
        phase = av.get('phase')
        tour = av.get('tour') if isinstance(av.get('tour'), int) else 0
        jalon_courant = av.get('jalon_courant')
    else:
        source = 'repli'   # run sans avancement.json : la feuille de route et status.md
        try:
            faits = set(coches((d / 'status.md').read_text(encoding='utf-8', errors='replace')))
        except OSError:
            faits = set()
        jalons, jalon_courant = [], None
        for n, titre in feuille:
            statut = 'fait' if n in faits else 'a-faire'
            if statut == 'a-faire' and jalon_courant is None:
                jalon_courant = f'M{n}'
            jalons.append({'id': f'M{n}', 'titre': titre, 'statut': statut})
        tour = max([n for n, _ in retours], default=0)
        phase = None

    # ── vidéo
    vers = (lire_json(ws / 'video' / 'versions.json', {}) or {}).get('versions') or []
    derniere = vers[-1] if vers and isinstance(vers[-1], dict) else {}
    video = {'url': lire_ligne(ws / 'video' / 'video-url.txt'), 'version': derniere.get('version'),
             'versions': len(vers), 'tour': derniere.get('tour')}

    if phase is None:
        if a_traiter:
            phase = 'retours'
        elif any(j['statut'] != 'fait' for j in jalons) or not jalons:
            phase = 'jalons'
        elif not video['url'] and os.environ.get('WEBAPP_VIDEO', '1').strip() != '0':
            phase = 'tournage'
        else:
            phase = 'fini'

    # ── l'app
    app_url = lire_ligne(d / 'app-url.txt')
    if not app_url:
        cfg = lire_json(d / 'config.json', {}) or {}
        app_url = cfg.get('productionUrl') or (cfg.get('deployment') or {}).get('productionUrl')

    # ── en cours ?
    lanceur_vivant = lanceur.get('statut') == 'en-cours' and tmux_vivant(lanceur.get('tmux'))
    dernier = passages[-1] if passages else {}
    agent_vivant = bool(dernier) and not dernier.get('ended') and tmux_vivant(dernier.get('session') or noeud.get('tmux'))
    en_cours = bool(lanceur_vivant or agent_vivant)

    # ── bloqué ? (seulement quand rien ne tourne : une run qui tourne peut encore se débloquer)
    bloque = None
    if not en_cours:
        if lanceur.get('statut') == 'bloque':
            bloque = lanceur.get('raison') or 'bloqué (sans raison écrite)'
        elif lanceur.get('statut') == 'en-cours':
            bloque = "le lanceur s'est arrêté sans conclure — relancer"
        elif isinstance(av, dict) and av.get('bloque'):
            bloque = str(av['bloque'])
        elif noeud.get('statut') == 'bloque-entree':
            bloque = 'livrables amont manquants : ' + ', '.join(map(str, (noeud.get('manques_amont') or [])[:6]))
        elif noeud.get('statut') == 'panne' and noeud.get('rc') != 0:
            cause = ((dernier.get('panne') or {}).get('cause')) or '; '.join(map(str, (noeud.get('erreurs') or [])[:2]))
            bloque = f'panne du moteur : {cause or "inconnue"}'

    derniere_passe = None
    if dernier:
        derniere_passe = {
            'n': dernier.get('n'), 'debut': dernier.get('started'), 'fin': dernier.get('ended'),
            'duree_s': dernier.get('duree_s'), 'verdict': dernier.get('verdict'),
            'comment': dernier.get('fin'), 'compte': dernier.get('compte'), 'modele': dernier.get('modele'),
            'erreurs': (dernier.get('erreurs') or [])[:5],
            'panne': (dernier.get('panne') or {}).get('cause'),
        }

    rv = (lire_json(d / 'revue.json', {}) or {}).get('tours') or []
    return {
        'run': ws.name, 'workspace': str(ws), 'source': source,
        'en_cours': en_cours, 'phase': phase, 'tour': tour,
        'jalon_courant': jalon_courant, 'jalons': jalons,
        'app_url': app_url, 'video': video, 'bloque': bloque,
        'derniere_passe': derniere_passe, 'passes': len(passages),
        'retours_a_traiter': a_traiter,
        'revue': {'tours': len(rv), 'dernier': rv[-1] if rv else None},
        'lanceur': ({k: lanceur.get(k) for k in ('statut', 'mode', 'tmux', 'debut', 'fin', 'plafond', 'raison', 'moteur')}
                    | {'passes': len(lanceur.get('passes') or [])}) if lanceur else None,
    }


def main(argv):
    if len(argv) != 2 or argv[1].startswith('-'):
        print(json.dumps({'indisponible': 'usage : webapp-etat.py <workspace>'}, ensure_ascii=False))
        return 2
    try:
        r = etat(argv[1])
    except Exception as exc:  # le module ne doit jamais recevoir autre chose qu'une ligne JSON
        r = {'indisponible': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(r, ensure_ascii=False))
    return 0 if 'indisponible' not in r else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
