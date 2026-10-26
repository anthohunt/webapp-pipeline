"""tools/webapp-lancer.py et tools/webapp-etat.py — au contrat de docs/2026-10-24-webapp-3-etapes-contrat.md.

Aucun agent n'est lancé : le superviseur joue contre un FAUX moteur (WEBAPP_LANCER_RUN_NODE), les états vivent
dans un dossier temporaire (FLUX_STATE_DIR), les workspaces aussi (jamais sous webapp-runs, où ils deviendraient
la run active). Les réglages du moteur (moteurs.json) sont un faux, dans une racine flux temporaire (FLUX_RACINE) ;
le code du moteur vient de FLUX_HOME (sinon vendor/flux).

    python3 -m unittest tests.test_webapp_lancer_etat
"""
import importlib.util, json, os, pathlib, shutil, subprocess, sys, tempfile, time, unittest

DEPOT = pathlib.Path(__file__).resolve().parent.parent
LANCER = DEPOT / 'tools' / 'webapp-lancer.py'
ETAT = DEPOT / 'tools' / 'webapp-etat.py'

FAUX_MOTEUR = r'''
import json, os, pathlib, sys
ws = pathlib.Path(sys.argv[sys.argv.index('--workspace') + 1])
plan = json.loads((ws / 'plan-faux-moteur.json').read_text())
compteur = ws / 'compteur'
i = int(compteur.read_text()) if compteur.exists() else 0
compteur.write_text(str(i + 1))
pas = plan[min(i, len(plan) - 1)]
d = pathlib.Path(os.environ['FLUX_STATE_DIR']) / 'webapp' / ws.name
d.mkdir(parents=True, exist_ok=True)
st = json.loads((d / 'construire.json').read_text()) if (d / 'construire.json').exists() else {'passages': []}
p = {'n': len(st['passages']) + 1, 'started': '2026-10-24T10:00:00Z', 'ended': '2026-10-24T10:05:00Z',
     'verdict': {0: 'vert', 1: 'rouge', 2: 'panne'}[pas['rc']], 'compte': 'essai', 'session': 'aucune'}
if pas.get('panne'):
    p['panne'] = {'cause': pas['panne']}
st['passages'].append(p); st['rc'] = pas['rc']
st['statut'] = pas.get('statut', 'panne' if pas['rc'] == 2 else 'en-cours')
(d / 'construire.json').write_text(json.dumps(st))
if pas.get('progres'):
    with open(ws / 'docs/pipeline/m1-journal.md', 'a') as f:
        f.write('\n## Bâtisseur — passe %d\n' % (i + 1))
if pas.get('bloque'):
    av = json.loads((ws / 'docs/pipeline/avancement.json').read_text()); av['bloque'] = pas['bloque']
    (ws / 'docs/pipeline/avancement.json').write_text(json.dumps(av))
sys.exit(pas['rc'])
'''


def ecrire(ws, chemin, contenu):
    p = ws / chemin
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(contenu, (dict, list)):
        contenu = json.dumps(contenu, ensure_ascii=False)
    p.write_text(contenu, encoding='utf-8')


def fabriquer(ws):
    """Une run à la sortie de l'étape 1 : tous les livrables de `concevoir`, deux jalons à construire."""
    g = json.loads((DEPOT / 'workflows' / 'webapp.json').read_text(encoding='utf-8'))
    concevoir = next(n for n in g['nodes'] if n['id'] == 'concevoir')
    for liv in concevoir['livrables']:
        ecrire(ws, liv, '{}' if liv.endswith('.json') else 'x\n')
    ecrire(ws, 'WORKSPACE.txt', 'workflow: webapp\nprojet: test-lanceur\nouvert: 2026-10-24T10:00:00\nmode: production\n')
    ecrire(ws, 'docs/pipeline/roadmap-approved.json', {'milestones': [{'n': 1, 'titre': 'Les prix'},
                                                                      {'n': 2, 'titre': 'Le trajet'}]})
    ecrire(ws, 'docs/pipeline/status.md', '# Status\n- [ ] Milestone 1 — Les prix\n- [ ] Milestone 2 — Le trajet\n')
    ecrire(ws, 'docs/pipeline/m1-journal.md', '# Jalon 1\n')
    ecrire(ws, 'docs/pipeline/config.json', {'productionUrl': 'https://app.example.org'})


def charger_lanceur():
    spec = importlib.util.spec_from_file_location('webapp_lancer', LANCER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='webapp-lanceur-'))
        self.ws = self.tmp / f'test-lanceur-{os.getpid()}-{time.time_ns() % 10**8}'
        self.ws.mkdir()
        fabriquer(self.ws)
        self.state = self.tmp / 'state'
        self.state.mkdir()
        self.faux = self.tmp / 'faux-run-node.py'
        self.faux.write_text(FAUX_MOTEUR, encoding='utf-8')
        self.racine = self.tmp / 'racine-flux'
        ecrire(self.racine, 'moteurs.json', {'defaut': 'essai', 'moteurs': [{'id': 'essai', 'config_dir': str(self.tmp)}]})
        self.reglages = dict(FLUX_STATE_DIR=str(self.state), WEBAPP_LANCER_RUN_NODE=str(self.faux),
                             FLUX_RACINE=str(self.racine), FLUX_WORKFLOWS_DIR=str(DEPOT / 'workflows'))
        self.env = dict(os.environ, **self.reglages)
        self.env.pop('WEBAPP_MOTEUR', None)
        self.env.pop('FLUX_IGNORER_VERSION', None)
        self.sessions = []

    def tearDown(self):
        for s in self.sessions:   # une session de test, par son nom exact
            subprocess.call(['tmux', 'kill-session', '-t', s], stderr=subprocess.DEVNULL)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def json_de(self, outil, *args):
        r = subprocess.run([sys.executable, str(outil), str(self.ws), *args], capture_output=True, text=True,
                           env=self.env, timeout=60)
        lignes = r.stdout.strip().splitlines()
        self.assertTrue(lignes, f'aucune sortie ; stderr : {r.stderr[-500:]}')
        self.assertEqual(len(lignes), 1, f'une seule ligne JSON attendue : {r.stdout!r}')
        return json.loads(lignes[0])

    def plan(self, pas):
        ecrire(self.ws, 'plan-faux-moteur.json', pas)


class Etat(Base):
    def test_run_neuve(self):
        e = self.json_de(ETAT)
        for k in ('en_cours', 'phase', 'tour', 'jalons', 'app_url', 'video', 'bloque', 'derniere_passe'):
            self.assertIn(k, e)
        self.assertFalse(e['en_cours'])
        self.assertEqual(e['phase'], 'jalons')
        self.assertEqual(e['tour'], 0)
        self.assertEqual([j['statut'] for j in e['jalons']], ['a-faire', 'a-faire'])
        self.assertEqual(e['app_url'], 'https://app.example.org')   # repli config.json
        self.assertEqual(e['video'], {'url': None, 'version': None, 'versions': 0, 'tour': None})
        self.assertIsNone(e['bloque'])

    def test_avancement_et_video(self):
        ecrire(self.ws, 'docs/pipeline/avancement.json', {'phase': 'fini', 'tour': 1, 'jalon_courant': None,
            'jalons': [{'id': 'M1', 'titre': 'Les prix', 'statut': 'fait'}, {'id': 'M2', 'titre': 'Le trajet', 'statut': 'fait'}],
            'maj': '2026-10-24T10:00:00Z'})
        ecrire(self.ws, 'docs/pipeline/app-url.txt', 'https://prod.example.org\n')
        ecrire(self.ws, 'video/video-url.txt', 'https://montage.example.org/a/?code=k\n')
        ecrire(self.ws, 'video/versions.json', {'versions': [{'version': 'V1', 'tour': 0}, {'version': 'V2', 'tour': 1}]})
        e = self.json_de(ETAT)
        self.assertEqual((e['phase'], e['tour'], e['source']), ('fini', 1, 'avancement'))
        self.assertEqual(e['app_url'], 'https://prod.example.org')
        self.assertEqual(e['video']['version'], 'V2')
        self.assertTrue(e['video']['url'].endswith('code=k'))

    def test_bloque_lu_dans_le_lanceur(self):
        ecrire(self.ws, 'state/lanceur.json', {'statut': 'bloque', 'raison': 'panne du moteur : quota-atteint',
                                               'tmux': 'inexistante-xyz', 'passes': []})
        self.assertEqual(self.json_de(ETAT)['bloque'], 'panne du moteur : quota-atteint')

    def test_lanceur_disparu(self):
        ecrire(self.ws, 'state/lanceur.json', {'statut': 'en-cours', 'tmux': 'inexistante-xyz', 'passes': []})
        e = self.json_de(ETAT)
        self.assertFalse(e['en_cours'])
        self.assertIn('sans conclure', e['bloque'])

    def test_lecture_pure(self):
        avant = {p: p.stat().st_mtime_ns for p in self.tmp.rglob('*')}
        self.json_de(ETAT)
        apres = {p: p.stat().st_mtime_ns for p in self.tmp.rglob('*')}
        self.assertEqual(avant, apres)

    def test_workspace_absent(self):
        r = subprocess.run([sys.executable, str(ETAT), str(self.tmp / 'nulle-part')], capture_output=True, text=True)
        self.assertIn('indisponible', json.loads(r.stdout))


class DryRun(Base):
    def test_construction(self):
        avant = {p: p.stat().st_mtime_ns for p in self.tmp.rglob('*')}
        r = self.json_de(LANCER, '--dry-run')
        self.assertTrue(r['ok'], r)
        self.assertEqual((r['mode'], r['plafond'], r['moteur']), ('construction', 8, 'essai'))
        self.assertTrue(r['dry_run'])
        self.assertTrue(r['tmux'].startswith('webapp-lanceur-'))
        self.assertEqual(avant, {p: p.stat().st_mtime_ns for p in self.tmp.rglob('*')}, 'le dry-run a écrit')

    def test_retours(self):
        ecrire(self.ws, 'docs/pipeline/retours/tour-1.json', {'tour': 1, 'statut': 'a-traiter', 'retours': []})
        r = self.json_de(LANCER, '--dry-run')
        self.assertEqual((r['mode'], r['plafond'], r['tours_a_traiter']), ('retours', 6, [1]))

    def test_refus_etape_1_incomplete(self):
        (self.ws / 'docs/pipeline/parcours-utilisateur.json').unlink()
        r = self.json_de(LANCER, '--dry-run')
        self.assertFalse(r['ok'])
        self.assertIn('parcours-utilisateur.json', r['refus'])

    def test_refus_autopilote(self):
        ecrire(self.ws, 'state/autopilote', '')
        self.assertIn('autopilote', self.json_de(LANCER, '--dry-run')['refus'])

    def test_refus_run_close(self):
        ecrire(self.ws, 'docs/pipeline/revue.json', {'tours': [{'tour': 1, 'verdict': 'good'}]})
        self.assertIn('close', self.json_de(LANCER, '--dry-run')['refus'])

    def test_refus_deja_en_cours(self):
        s = f'test-webapp-occupe-{os.getpid()}'
        subprocess.check_call(['tmux', 'new-session', '-d', '-s', s, 'sleep 60'])
        self.sessions.append(s)
        ecrire(self.ws, 'state/lanceur.json', {'statut': 'en-cours', 'tmux': s, 'mode': 'construction'})
        self.assertIn('tourne déjà', self.json_de(LANCER, '--dry-run')['refus'])
        self.assertTrue(self.json_de(ETAT)['en_cours'])

    def test_refus_moteur_inconnu(self):
        self.assertIn('moteur inconnu', self.json_de(LANCER, '--dry-run', '--moteur', 'nimporte')['refus'])


class Superviseur(Base):
    def superviser(self, plafond=8):
        old = dict(os.environ)
        os.environ.update(self.reglages)
        try:
            m = charger_lanceur()
            ecrire(self.ws, 'state/lanceur.json', {'statut': 'en-cours', 'passes': []})
            rc = m.superviser(self.ws, plafond)
        finally:
            os.environ.clear(); os.environ.update(old)
        return rc, json.loads((self.ws / 'state/lanceur.json').read_text())

    def test_relance_jusqu_au_vert(self):
        self.plan([{'rc': 1, 'progres': True}, {'rc': 1, 'progres': True}, {'rc': 0, 'progres': True}])
        rc, st = self.superviser()
        self.assertEqual((rc, st['statut'], len(st['passes'])), (0, 'fini', 3))

    def test_sans_progres(self):
        self.plan([{'rc': 1}])
        rc, st = self.superviser()
        self.assertEqual((st['statut'], len(st['passes'])), ('bloque', 3))
        self.assertIn('sans progrès', st['raison'])

    def test_quota(self):
        self.plan([{'rc': 2, 'panne': 'quota-atteint'}])
        rc, st = self.superviser()
        self.assertEqual((st['statut'], len(st['passes'])), ('bloque', 1))
        self.assertIn('quota-atteint', st['raison'])

    def test_session_morte_deux_fois(self):
        self.plan([{'rc': 2, 'panne': 'session-morte'}])
        rc, st = self.superviser()
        self.assertEqual((st['statut'], len(st['passes'])), ('bloque', 2))

    def test_entree_bloquee(self):
        self.plan([{'rc': 2, 'statut': 'bloque-entree'}])
        rc, st = self.superviser()
        self.assertIn('amont', st['raison'])

    def test_bloque_ecrit_par_le_noeud(self):
        self.plan([{'rc': 1, 'progres': True, 'bloque': 'm1 : 3 cycles refusés'}])
        ecrire(self.ws, 'docs/pipeline/avancement.json', {'phase': 'jalons', 'tour': 0, 'jalons': []})
        rc, st = self.superviser()
        self.assertEqual(st['raison'], 'm1 : 3 cycles refusés')

    def test_plafond(self):
        self.plan([{'rc': 1, 'progres': True}])
        rc, st = self.superviser(plafond=4)
        self.assertEqual((st['statut'], len(st['passes'])), ('bloque', 4))
        self.assertIn('plafond', st['raison'])


class Lancement(Base):
    def test_detache_pose_le_moteur_et_finit(self):
        self.plan([{'rc': 1, 'progres': True}, {'rc': 0, 'progres': True}])
        r = self.json_de(LANCER)
        self.assertTrue(r['ok'], r)
        self.sessions.append(r['tmux'])
        self.assertEqual((self.ws / 'state/moteur').read_text().strip(), 'essai')
        for _ in range(60):
            st = json.loads((self.ws / 'state/lanceur.json').read_text())
            if st['statut'] != 'en-cours':
                break
            time.sleep(0.5)
        self.assertEqual((st['statut'], len(st['passes'])), ('fini', 2))
        self.assertFalse(self.json_de(ETAT)['en_cours'])


if __name__ == '__main__':
    unittest.main()
