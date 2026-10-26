#!/usr/bin/env python3
"""Lance l'étape 2 (« construire ») d'une run web app en détaché, et la RELANCE jusqu'au contrôle vert.

    python3 webapp-lancer.py <ws> [--dry-run] [--max-passes N] [--moteur ID]

Contrat : docs/2026-10-24-webapp-3-etapes-contrat.md (commandes). Une ligne JSON sur stdout :
{"ok": true, "tmux": "…", "mode": "construction"|"retours", …} ou {"ok": false, "refus": "…"}.

Le nœud `construire` traite UNE unité de travail par lancement (un jalon, le tournage, ou un tour de retours :
skill pipeline-step4). Ce script démarre, dans une session tmux, un SUPERVISEUR qui boucle sur le vrai moteur
(`runtime/run-node.py webapp construire --workspace <ws>`, synchrone) et s'arrête :
• au vert (code 0 du moteur) ;
• sur un blocage que relancer ne lèvera pas : livrables amont manquants (code 2), version de Claude Code
  refusée (code 3), panne du moteur deux fois de suite (quota, jeton expiré, session morte), `bloque` écrit
  par le nœud dans avancement.json, trois passes sans progrès, ou le plafond de passes ;
• si la revue a clos la run, ou si l'autopilote du séquenceur a été posé entre-temps.
Son état vit dans <ws>/state/lanceur.json (statut en-cours | fini | bloque, raison, passes), son journal dans
<ws>/state/lanceur.log ; webapp-etat.py le lit.

La boucle revue → construire passe par ici, pas par le graphe : un `revue.suivant: [construire]` ferait exiger
les livrables de la revue dès la première construction. Mode « retours » = un tour
docs/pipeline/retours/tour-N.json au statut a-traiter ; le nœud le traite de lui-même.

Le moteur des agents de construction (un id de moteurs.json du moteur flux) vient de WEBAPP_MOTEUR, sinon du
`defaut` de moteurs.json : le lanceur l'écrit dans <ws>/state/moteur, que run-node lit pour choisir le compte.
--moteur le remplace.

--dry-run : tous les contrôles, le mode, le plafond et la commande, SANS rien écrire ni lancer (n'appelle pas
`run-node --dry-run`, qui écrit run.json et un dossier de passe).
"""
import argparse, datetime, hashlib, importlib.util, json, os, pathlib, shlex, subprocess, sys, time

ICI = pathlib.Path(__file__).resolve().parent
DEPOT = ICI.parent    # racine du dépôt webapp-pipeline
# Le moteur flux est une dépendance : FLUX_HOME, sinon le clone conseillé par le README (vendor/flux).
FLUX = pathlib.Path(os.environ.get('FLUX_HOME') or DEPOT / 'vendor' / 'flux')
sys.path.insert(0, str(FLUX / 'runtime'))
import socle  # noqa: E402

WF = 'webapp'
NOEUD = 'construire'
DOCS = 'docs/pipeline'
MOTEUR_DEFAUT = os.environ.get('WEBAPP_MOTEUR') or ''   # vide = le `defaut` de moteurs.json
RUN_NODE = FLUX / 'runtime' / 'run-node.py'
# Les tests jouent le superviseur contre un faux moteur : WEBAPP_LANCER_RUN_NODE remplace le script EXÉCUTÉ
# (les contrôles, eux, lisent toujours le vrai run-node).
RUN_NODE_EXEC = pathlib.Path(os.environ.get('WEBAPP_LANCER_RUN_NODE') or RUN_NODE)
VALIDATEUR = DEPOT / 'validators' / 'webapp_construire.py'
SANS_PROGRES = 3          # passes consécutives sans aucun changement de l'état → bloqué
PANNES_DE_SUITE = 2       # pannes du moteur consécutives → bloqué
PLAFOND_RETOURS = 6


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def lire_json(p, defaut=None):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:
        return defaut


def ecrire_json(p, v):
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, p)


def tmux_vivant(sess):
    return bool(sess) and subprocess.call(['tmux', 'has-session', '-t', str(sess)],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def charger(nom, chemin):
    spec = importlib.util.spec_from_file_location(nom, str(chemin))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dossier_etat(ws):
    nom = pathlib.Path(ws).name
    if socle.run_confinee(ws):
        return socle.racine_runs_mesure() / 'state' / WF / nom
    return socle.dossier_state() / WF / nom


def nom_tmux(ws):
    return 'webapp-lanceur-' + hashlib.md5(pathlib.Path(ws).name.encode('utf-8')).hexdigest()[:6]


class Refus(Exception):
    pass


# ───────────────────────── ce que dit l'état de la run

def tours_a_traiter(ws):
    d = pathlib.Path(ws) / DOCS / 'retours'
    out = []
    for f in (sorted(d.glob('tour-*.json')) if d.is_dir() else []):
        n = f.stem.split('-', 1)[1]
        if n.isdigit() and (lire_json(f, {}) or {}).get('statut') == 'a-traiter':
            out.append(int(n))
    return sorted(out)


def revue_close(ws):
    tours = (lire_json(pathlib.Path(ws) / DOCS / 'revue.json', {}) or {}).get('tours') or []
    return bool(tours) and (tours[-1] or {}).get('verdict') == 'good'


def nb_jalons(ws):
    j = lire_json(pathlib.Path(ws) / DOCS / 'roadmap-approved.json', {}) or {}
    return len(j.get('milestones') or j.get('jalons') or [])


def gate_construire(ws):
    """Le validateur du nœud, importé et appelé directement : pur, il ne lit que des fichiers.
    (validate.py, lui, réécrit run-report-bundle/ : jamais en dry-run.)"""
    if not VALIDATEUR.exists():
        return None
    return charger('webapp_construire', VALIDATEUR).validate(str(ws))


def signature(ws):
    """Ce qui bouge quand une passe avance : sans aucun changement ici, la passe n'a rien produit."""
    ws = pathlib.Path(ws)
    d = ws / DOCS
    av = lire_json(d / 'avancement.json', {}) or {}
    tailles = []
    for f in sorted(list(d.glob('m*-journal.md')) + list((d / 'retours').glob('tour-*-journal.md'))):
        try:
            tailles.append((f.name, f.stat().st_size))
        except OSError:
            pass
    try:
        status = (d / 'status.md').read_text(encoding='utf-8', errors='replace').count('[x]')
    except OSError:
        status = 0
    vers = len((lire_json(ws / 'video' / 'versions.json', {}) or {}).get('versions') or [])
    traites = sum(1 for f in (d / 'retours').glob('tour-*.json')
                  if (lire_json(f, {}) or {}).get('statut') == 'traite') if (d / 'retours').is_dir() else 0
    faits = sum(1 for j in (av.get('jalons') or []) if isinstance(j, dict) and j.get('statut') == 'fait')
    return json.dumps([faits, av.get('phase'), av.get('jalon_courant'), status, vers, traites, tailles])


# ───────────────────────── contrôles avant de lancer

def controler(ws, moteur_id):
    ws = pathlib.Path(ws).resolve()
    if not (ws / 'WORKSPACE.txt').is_file():
        raise Refus(f'workspace introuvable : {ws}')
    champs = {}
    for l in (ws / 'WORKSPACE.txt').read_text(encoding='utf-8', errors='replace').splitlines():
        if ':' in l:
            k, v = l.split(':', 1)
            champs[k.strip()] = v.strip()
    if champs.get('workflow') not in (None, WF):
        raise Refus(f"cette run n'est pas une run {WF} (workflow: {champs.get('workflow')})")
    lanceur = lire_json(ws / 'state' / 'lanceur.json', {}) or {}
    if lanceur.get('statut') == 'en-cours' and tmux_vivant(lanceur.get('tmux')):
        raise Refus(f"la construction tourne déjà (session {lanceur.get('tmux')}, mode {lanceur.get('mode')})")
    noeud = lire_json(dossier_etat(ws) / f'{NOEUD}.json', {}) or {}
    dernier = (noeud.get('passages') or [{}])[-1]
    if dernier and not dernier.get('ended') and tmux_vivant(dernier.get('session') or noeud.get('tmux')):
        raise Refus(f"un agent de construction tourne déjà (session {dernier.get('session') or noeud.get('tmux')})")
    if (ws / 'state' / 'autopilote').exists():
        raise Refus("l'autopilote du séquenceur est posé sur cette run (state/autopilote) : il piloterait les nœuds "
                    "en double — retire-le, ou laisse-le faire")
    if revue_close(ws):
        raise Refus('la run est close : la revue a rendu « good »')

    # les livrables de l'étape 1, comme le moteur les exigera (sans écrire son état)
    rn = charger('run_node', RUN_NODE)
    wf = rn.load_wf(WF)
    node = rn.node_of(wf, NOEUD)
    manques = []
    for up in rn.upstream(wf, NOEUD):
        for liv in rn.livrables_exiges(up, str(ws))[0]:
            if not rn.present(str(ws), liv):
                manques.append(f'{up["id"]}:{liv}')
    if manques:
        raise Refus("l'étape 1 n'a pas livré : " + ', '.join(manques[:8]) + (' …' if len(manques) > 8 else ''))

    ok_v, msg_v = socle.verifier_version_claude()
    if not ok_v:
        raise Refus(msg_v)
    cfg_moteurs = socle.charger_moteurs()
    moteur_id = moteur_id or cfg_moteurs.get('defaut') or ''
    moteurs = {m.get('id'): m for m in cfg_moteurs.get('moteurs') or []}
    m = moteurs.get(moteur_id)
    if not m:
        raise Refus(f'moteur inconnu dans moteurs.json : {moteur_id}')
    jeton = m.get('fichier_jeton')
    if jeton and not os.access(jeton, os.R_OK):
        raise Refus(f'jeton du moteur {moteur_id} illisible : {jeton}')

    retours = tours_a_traiter(ws)
    mode = 'retours' if retours else 'construction'
    errs = gate_construire(ws)
    if mode == 'construction' and errs == []:
        raise Refus('rien à faire : la construction est finie (contrôle webapp-construire vert) — place à la revue')
    plafond = PLAFOND_RETOURS if mode == 'retours' else 2 * max(nb_jalons(ws), 1) + 4
    return {'ws': ws, 'mode': mode, 'tours': retours, 'plafond': plafond, 'moteur': moteur_id,
            'version': msg_v, 'gate': errs, 'node': node}


# ───────────────────────── le superviseur (dans la session tmux)

def journal(ws, msg):
    # stdout du superviseur part déjà dans lanceur.log (tee) : une seule écriture, à l'écran
    print(f'[{maintenant()}] {msg}', flush=True)


def superviser(ws, plafond):
    ws = pathlib.Path(ws).resolve()
    lp = ws / 'state' / 'lanceur.json'
    st = lire_json(lp, {}) or {}

    def poser(**kw):
        st.update(kw)
        st['maj'] = maintenant()
        ecrire_json(lp, st)

    def finir(statut, raison=None):
        poser(statut=statut, raison=raison, fin=maintenant())
        journal(ws, f'fin : {statut}' + (f' — {raison}' if raison else ''))
        return 0 if statut == 'fini' else 1

    sans_progres = pannes = 0
    for i in range(1, plafond + 1):
        if revue_close(ws):
            return finir('fini', 'la revue a clos la run')
        if (ws / 'state' / 'autopilote').exists():
            return finir('bloque', "l'autopilote du séquenceur a été posé : le lanceur s'efface")
        avant = signature(ws)
        journal(ws, f'passe {i}/{plafond} : run-node {WF} {NOEUD}')
        t0 = time.time()
        with open(ws / 'state' / 'lanceur.log', 'a', encoding='utf-8') as log:
            rc = subprocess.call([sys.executable, str(RUN_NODE_EXEC), WF, NOEUD, '--workspace', str(ws)],
                                 stdout=log, stderr=log, cwd=str(FLUX))
        noeud = lire_json(dossier_etat(ws) / f'{NOEUD}.json', {}) or {}
        dernier = (noeud.get('passages') or [{}])[-1]
        apres = signature(ws)
        progres = apres != avant
        st.setdefault('passes', []).append({'n': i, 'rc': rc, 'duree_s': int(time.time() - t0),
                                            'passe_moteur': dernier.get('n'), 'verdict': dernier.get('verdict'),
                                            'panne': (dernier.get('panne') or {}).get('cause'), 'progres': progres})
        poser()
        journal(ws, f'passe {i} : code {rc}, verdict {dernier.get("verdict")}, progrès {"oui" if progres else "non"}')
        if rc == 0:
            return finir('fini')
        if rc == 3:
            return finir('bloque', '; '.join(map(str, noeud.get('erreurs') or [])) or 'version de Claude Code refusée')
        if rc == 2 and noeud.get('statut') == 'bloque-entree':
            return finir('bloque', 'livrables amont manquants : ' + ', '.join(map(str, (noeud.get('manques_amont') or [])[:6])))
        if rc == 2:
            pannes += 1
            cause = (dernier.get('panne') or {}).get('cause') or 'panne'
            if cause in ('quota-atteint', 'jeton-expire') or pannes >= PANNES_DE_SUITE:
                return finir('bloque', f'panne du moteur : {cause}' + (f' ({pannes} de suite)' if pannes > 1 else ''))
            continue
        pannes = 0
        av = lire_json(ws / DOCS / 'avancement.json', {}) or {}
        if av.get('bloque'):
            return finir('bloque', str(av['bloque']))
        sans_progres = 0 if progres else sans_progres + 1
        if sans_progres >= SANS_PROGRES:
            return finir('bloque', f'{SANS_PROGRES} passes sans progrès (jalons, journaux, vidéo et tours inchangés) — '
                         'dernières erreurs du contrôle : ' + '; '.join(map(str, (dernier.get('erreurs') or [])[:3])))
    return finir('bloque', f'plafond de {plafond} passes atteint sans contrôle vert')


# ───────────────────────── lancer

def lancer(c, dry_run):
    ws = c['ws']
    sess = nom_tmux(ws)
    cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), str(ws), '--superviser',
           '--max-passes', str(c['plafond'])]
    rep = {'ok': True, 'tmux': sess, 'mode': c['mode'], 'plafond': c['plafond'], 'moteur': c['moteur'],
           'tours_a_traiter': c['tours'], 'version': c['version']}
    if dry_run:
        moteur_actuel = None
        try:
            moteur_actuel = (ws / 'state' / 'moteur').read_text(encoding='utf-8').strip()
        except OSError:
            pass
        rep.update({'dry_run': True, 'commande': ' '.join(shlex.quote(x) for x in cmd),
                    'moteur_actuel': moteur_actuel,
                    'controle': (c['gate'] or [])[:8] if c['gate'] is not None else 'validateur introuvable',
                    'taches': c['node'].get('taches')})
        return rep
    (ws / 'state').mkdir(parents=True, exist_ok=True)
    mp = ws / 'state' / 'moteur'
    precedent = mp.read_text(encoding='utf-8').strip() if mp.exists() else None
    if precedent != c['moteur']:
        mp.write_text(c['moteur'] + '\n', encoding='utf-8')
    ecrire_json(ws / 'state' / 'lanceur.json', {
        'statut': 'en-cours', 'mode': c['mode'], 'tmux': sess, 'debut': maintenant(), 'fin': None,
        'plafond': c['plafond'], 'raison': None, 'moteur': c['moteur'], 'moteur_precedent': precedent,
        'tours_a_traiter': c['tours'], 'passes': [], 'maj': maintenant()})
    env = {k: v for k, v in os.environ.items()
           if k.startswith(('FLUX_', 'WEBAPP_')) or k in ('PATH', 'HOME', 'LANG')}
    env.setdefault('PATH', '/usr/local/bin:/usr/bin:/bin')
    script = ' '.join(shlex.quote(x) for x in cmd)
    envs = ' '.join(f'{k}={shlex.quote(v)}' for k, v in env.items())
    log = shlex.quote(str(ws / 'state' / 'lanceur.log'))
    subprocess.check_call(['tmux', 'new-session', '-d', '-s', sess, '-x', '160', '-y', '45',
                           f'cd {shlex.quote(str(FLUX))} && env {envs} {script} 2>&1 | tee -a {log}'])
    time.sleep(1)
    if not tmux_vivant(sess):
        st = lire_json(ws / 'state' / 'lanceur.json', {}) or {}
        if st.get('statut') in ('fini', 'bloque'):     # déjà conclu (passe très courte) : pas une mort
            return rep | {'statut': st['statut'], 'raison': st.get('raison')}
        st.update(statut='bloque', raison='le superviseur est mort au démarrage (voir state/lanceur.log)', fin=maintenant())
        ecrire_json(ws / 'state' / 'lanceur.json', st)
        return {'ok': False, 'refus': st['raison']}
    return rep


def main():
    ap = argparse.ArgumentParser(description="Lance et relance l'étape 2 (construire) d'une run web app.")
    ap.add_argument('ws')
    ap.add_argument('--dry-run', action='store_true', help='contrôles et plan, sans rien écrire ni lancer')
    ap.add_argument('--max-passes', type=int, default=None, help='plafond de passes (défaut : 2×jalons+4, 6 en retours)')
    ap.add_argument('--moteur', default=MOTEUR_DEFAUT, help="moteur des agents (id de moteurs.json ; défaut : WEBAPP_MOTEUR, sinon le `defaut` de moteurs.json)")
    ap.add_argument('--superviser', action='store_true', help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.superviser:
        return superviser(a.ws, a.max_passes or 10)
    try:
        c = controler(a.ws, a.moteur)
        if a.max_passes:
            c['plafond'] = a.max_passes
        rep = lancer(c, a.dry_run)
    except Refus as r:
        rep = {'ok': False, 'refus': str(r)}
    except Exception as exc:
        rep = {'ok': False, 'refus': f'erreur du lanceur : {type(exc).__name__}: {exc}'}
    print(json.dumps(rep, ensure_ascii=False))
    return 0 if rep.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main())
