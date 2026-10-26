"""Tests du programme du module webapp : un faux moteur flux (new-run, run-node, webapp-lancer, webapp-etat) dans un
dossier temporaire, le vrai programme appelé comme le mod l'appelle (JSON sur l'entrée standard)."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

PROG = pathlib.Path(__file__).resolve().parents[1] / 'webapp.py'

FAUX_NEW_RUN = '''
import sys, os, pathlib, datetime
root = pathlib.Path(os.environ['WEBAPP_RUNS']); root.mkdir(parents=True, exist_ok=True)
ws = root / (sys.argv[2] + '-2026-10-27-090000'); ws.mkdir()
(ws / 'WORKSPACE.txt').write_text('workflow: webapp\\nprojet: %s\\nouvert: 2026-10-27T09:00:00\\nmode: production\\n' % sys.argv[2])
'''

# Le faux run-node : --brief-only écrit le brief ; sinon le gate est vert si le fichier GATE_VERT existe dans la run.
FAUX_RUN_NODE = '''
import sys, os, json, pathlib
wf, node = sys.argv[1], sys.argv[2]
ws = pathlib.Path(sys.argv[sys.argv.index('--workspace') + 1])
d = pathlib.Path(os.environ['FLUX_HOME']) / 'state' / wf / ws.name; (d / node).mkdir(parents=True, exist_ok=True)
if '--brief-only' in sys.argv:
    (d / node / 'brief.md').write_text('brief'); (d / node / 'sys.md').write_text('sys'); print(d / node / 'brief.md'); sys.exit(0)
vert = (ws / 'GATE_VERT').exists()
(d / (node + '.json')).write_text(json.dumps({'statut': 'vert' if vert else 'rouge', 'erreurs': [] if vert else ['C12 : parcours sans écran']}))
sys.exit(0 if vert else 1)
'''

FAUX_LANCER = '''
import sys, json, pathlib
ws = pathlib.Path(sys.argv[1])
(ws / 'LANCE').write_text(str(int((ws / 'LANCE').read_text()) + 1) if (ws / 'LANCE').exists() else '1')
print(json.dumps({'ok': True, 'tmux': 'flux-webapp-x-construire-p1', 'mode': 'retours' if list((ws / 'docs/pipeline/retours').glob('*.json')) else 'construction'}))
'''

FAUX_ETAT = '''
import sys, json, pathlib
ws = pathlib.Path(sys.argv[1])
f = ws / 'ETAT_CONSTRUCTION.json'
print(f.read_text() if f.exists() else json.dumps({'en_cours': True, 'phase': 'jalons', 'tour': 0, 'jalons': [], 'bloque': None}))
'''


class Banc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = pathlib.Path(self.tmp.name)
        self.runs, self.flux = t / 'runs', t / 'flux'
        for rel, src in [('runtime/new-run.py', FAUX_NEW_RUN), ('runtime/run-node.py', FAUX_RUN_NODE),
                         ('tools/webapp-lancer.py', FAUX_LANCER), ('tools/webapp-etat.py', FAUX_ETAT)]:
            p = self.flux / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(textwrap.dedent(src))
        (self.flux / 'workflows').mkdir()
        (self.flux / 'workflows/webapp.json').write_text(json.dumps({'nodes': [
            {'id': 'concevoir', 'n': 1}, {'id': 'construire', 'n': 2}, {'id': 'revue', 'n': 3}]}))

    def tearDown(self):
        self.tmp.cleanup()

    def appel(self, commande, **args):
        env = dict(os.environ, WEBAPP_RUNS=str(self.runs), FLUX_HOME=str(self.flux),
                   WEBAPP_OUTILS=str(self.flux / 'tools'), WEBAPP_GRAPHES=str(self.flux / 'workflows'))
        r = subprocess.run([sys.executable, '-B', str(PROG), commande], input=json.dumps(args),
                           capture_output=True, text=True, env=env, timeout=60)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def ok(self, commande, **args):
        r = self.appel(commande, **args)
        self.assertTrue(r['ok'], r)
        return r['resultat']

    def refus(self, commande, **args):
        r = self.appel(commande, **args)
        self.assertFalse(r['ok'], r)
        return r['refus']

    def ecrire(self, ws, rel, contenu='x'):
        p = pathlib.Path(ws) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenu if isinstance(contenu, str) else json.dumps(contenu))

    def etape1_jusqua(self, run, ws, jusqua='E1.7'):
        sorties = {
            'E1.2': ['docs/pipeline/concept.md'], 'E1.3': ['docs/pipeline/cahier-des-charges.md'],
            'E1.4': ['docs/pipeline/parcours-utilisateur.json', 'docs/pipeline/parcours-utilisateur.md'],
            'E1.5': ['docs/pipeline/design/stories-v1.json'],
            'E1.6': ['docs/pipeline/design/mockup.html', 'docs/pipeline/design/mockup-public-url.txt', 'docs/pipeline/design/screens.json'],
            'E1.7': ['docs/pipeline/design/validation.md'],
        }
        self.ok('pitch', run=run, citation='Une app pour partager les frais de trajet')
        for sid, fichiers in sorties.items():
            for f in fichiers:
                self.ecrire(ws, f, 'https://maquettes.example.org/design/x/' if f.endswith('url.txt') else 'x')
            if sid != 'E1.7':
                self.ok('avancer', run=run, sous_etape=sid, etat='a_valider')
            self.ok('avancer', run=run, sous_etape=sid, etat='validee', citation='oui')
            if sid == jusqua:
                return


class TestEtape1(Banc):
    def test_ouvrir_cree_la_run_puis_la_reprend(self):
        v = self.ok('ouvrir', projet='Covoiturage Facile', session='s1')
        self.assertTrue(v['neuf'])
        self.assertTrue(v['run'].startswith('covoiturage-facile-'))
        self.assertEqual(v['attend']['sous_etape'], 'E1.1')
        self.assertTrue(pathlib.Path(v['brief']['sys']).exists(), 'le brief du nœud 1 est préparé')
        v2 = self.ok('ouvrir', projet='covoiturage-facile', session='s2')
        self.assertFalse(v2['neuf'])
        self.assertEqual(v2['run'], v['run'])

    def test_pitch_mot_pour_mot_puis_e12(self):
        v = self.ok('ouvrir', projet='essai')
        self.ok('pitch', run=v['run'], citation='Je veux une appli de covoiturage')
        v = self.ok('etat', run=v['run'])
        e = {s['id']: s for s in v['etapes'][0]['sous_etapes']}
        self.assertEqual(e['E1.1']['etat'], 'validee')
        self.assertEqual(e['E1.1']['citation'], 'Je veux une appli de covoiturage')
        self.assertEqual(e['E1.2']['etat'], 'en_cours')
        self.assertIn('covoiturage', (pathlib.Path(v['workspace']) / 'docs/pipeline/pitch.md').read_text())
        self.assertTrue(self.ok('pitch', run=v['run'], citation='autre')['deja'])

    def test_valider_exige_sorties_citation_et_ordre(self):
        v = self.ok('ouvrir', projet='essai')
        run, ws = v['run'], v['workspace']
        self.assertIn('pas encore validée', self.refus('avancer', run=run, sous_etape='E1.3', etat='a_valider'))
        self.ok('pitch', run=run, citation='pitch')
        self.assertIn('concept.md', self.refus('avancer', run=run, sous_etape='E1.2', etat='a_valider'))
        self.ecrire(ws, 'docs/pipeline/concept.md')
        self.ok('avancer', run=run, sous_etape='E1.2', etat='a_valider')
        self.assertEqual(self.ok('etat', run=run)['attend']['quoi'], "valider les questions d'usage")
        self.assertIn('citation', self.refus('avancer', run=run, sous_etape='E1.2', etat='validee'))
        self.ok('avancer', run=run, sous_etape='E1.2', etat='validee', citation='A')
        self.assertIn('cloturer', self.refus('avancer', run=run, sous_etape='E1.8', etat='validee', citation='x'))

    def test_decision_et_rouvrir(self):
        v = self.ok('ouvrir', projet='essai')
        run = v['run']
        self.ok('decision', run=run, sous_etape='E1.2', resume='Usage en voiture', citation='en voiture surtout', option='A')
        self.etape1_jusqua(run, v['workspace'], 'E1.4')
        self.ok('rouvrir', run=run, sous_etape='E1.3', raison='le client veut ajouter les péages')
        e = {s['id']: s for s in self.ok('etat', run=run)['etapes'][0]['sous_etapes']}
        self.assertEqual(e['E1.3']['etat'], 'en_cours')
        self.assertEqual(e['E1.4']['etat'], 'validee', 'une sous-étape validée après reste validée')
        self.assertEqual(e['E1.5']['etat'], 'a_faire')
        self.assertEqual(e['E1.2']['decisions'][0]['citation'], 'en voiture surtout')

    def test_cloturer_passe_le_gate_du_moteur(self):
        v = self.ok('ouvrir', projet='essai')
        run, ws = v['run'], v['workspace']
        self.assertIn('E1.7', self.refus('cloturer', run=run))
        self.etape1_jusqua(run, ws)
        self.assertIn('parcours sans écran', self.refus('cloturer', run=run))
        self.ecrire(ws, 'GATE_VERT')
        self.assertEqual(self.ok('cloturer', run=run)['gate'], 'vert')
        v = self.ok('etat', run=run)
        self.assertEqual(v['etapes'][0]['etat'], 'faite')
        self.assertEqual(v['attend'], {'quoi': 'lancer la construction', 'action': 'lancer'})
        self.assertEqual(v['etape_courante'], 2)


class TestEtapes2et3(Banc):
    def prete(self):
        v = self.ok('ouvrir', projet='essai')
        run, ws = v['run'], v['workspace']
        self.etape1_jusqua(run, ws)
        self.ecrire(ws, 'GATE_VERT')
        self.ok('cloturer', run=run)
        return run, ws

    def finir(self, ws, tour, version):
        self.ecrire(ws, 'ETAT_CONSTRUCTION.json', {
            'en_cours': False, 'phase': 'fini', 'tour': tour, 'bloque': None,
            'jalons': [{'id': 'M1', 'titre': 'Prix', 'statut': 'fait'}], 'app_url': 'https://app.example',
            'video': {'url': 'https://montage.example.org/essai/?code=abc', 'version': version}})

    def test_lancer_suivre_finir_puis_good(self):
        v = self.ok('ouvrir', projet='autre')
        self.assertIn('étape 1', self.refus('lancer', run=v['run']))
        run, ws = self.prete()
        self.assertEqual(self.ok('lancer', run=run)['mode'], 'construction')
        v = self.ok('etat', run=run)
        e2 = {s['id']: s['etat'] for s in v['etapes'][1]['sous_etapes']}
        self.assertEqual(e2, {'E2.1': 'en_cours', 'E2.2': 'a_faire'})
        self.assertIsNone(v['attend'])
        self.assertIn('pas de revue', self.refus('revue', run=run, verdict='good', citation='top'))
        self.finir(ws, 0, 'V1')
        v = self.ok('etat', run=run)
        self.assertEqual(v['etape_courante'], 3)
        self.assertEqual(v['attend']['sous_etape'], 'E3.1')
        self.assertEqual(v['liens']['video'], 'https://montage.example.org/essai/?code=abc')
        self.ok('revue', run=run, verdict='good', citation="c'est parfait")
        v = self.ok('etat', run=run)
        self.assertTrue(v['close'])
        self.assertIsNone(v['attend'])
        self.assertEqual(json.loads((pathlib.Path(ws) / 'docs/pipeline/revue.json').read_text())['tours'][0]['verdict'], 'good')

    def test_bloque_se_relance(self):
        run, ws = self.prete()
        self.ok('lancer', run=run)
        self.ecrire(ws, 'ETAT_CONSTRUCTION.json', {'en_cours': False, 'phase': 'jalons', 'tour': 0, 'bloque': 'relances épuisées sur M2'})
        v = self.ok('etat', run=run)
        self.assertEqual(v['attend']['action'], 'lancer')
        self.assertIn('M2', v['attend']['quoi'])
        self.assertEqual(v['etapes'][1]['sous_etapes'][0]['etat'], 'bloquee')

    def test_retours_relancent_un_tour_puis_v2(self):
        run, ws = self.prete()
        self.ok('lancer', run=run)
        self.finir(ws, 0, 'V1')
        self.assertIn('retours du tour 1', self.refus('revue', run=run, verdict='retours', citation='pas bon'))
        self.assertIn('attendu', self.refus('retours', run=run, citation='x', retours=[{'dit': 'la carte est vide'}]))
        r = self.ok('retours', run=run, citation='il dit que la carte est vide', retours=[
            {'dit': 'la carte est vide', 'ecran': 'S1', 'attendu': 'la carte montre les magasins à moins de 5 km'}])
        self.assertEqual(r['tour'], 1)
        t = json.loads((pathlib.Path(ws) / 'docs/pipeline/retours/tour-1.json').read_text())
        self.assertEqual((t['statut'], t['retours'][0]['id']), ('a-traiter', 'R1'))
        rv = self.ok('revue', run=run, verdict='retours', citation='il veut la carte')
        self.assertEqual(rv['relance']['mode'], 'retours')
        self.assertEqual((pathlib.Path(ws) / 'LANCE').read_text(), '2')
        v = self.ok('etat', run=run)
        self.assertEqual((v['tour'], v['etape_courante']), (1, 2))
        self.assertEqual(v['etapes'][2]['sous_etapes'][0]['etat'], 'a_faire', 'la construction du tour 1 n’est pas finie')
        self.ecrire(ws, 'ETAT_CONSTRUCTION.json', {'en_cours': True, 'phase': 'retours', 'tour': 1, 'bloque': None})
        v = self.ok('etat', run=run)
        self.assertEqual([x['etat'] for x in v['etapes'][1]['sous_etapes']], ['en_cours', 'a_faire'], 'le tour de retours se voit en cours')
        self.finir(ws, 1, 'V2')
        v = self.ok('etat', run=run)
        self.assertEqual((v['etape_courante'], v['version_video']), (3, 'V2'))
        self.ok('revue', run=run, verdict='good', citation='ok cette fois')
        self.assertEqual([t['verdict'] for t in self.ok('etat', run=run)['tours']], ['retours', 'good'])

    def test_lire_reste_dans_la_run(self):
        run, ws = self.prete()
        self.assertEqual(self.ok('lire', run=run, chemin='docs/pipeline/concept.md')['contenu'], 'x')
        self.assertIn('hors de la run', self.refus('lire', run=run, chemin='../../etc/passwd'))

    def test_liste(self):
        run, _ = self.prete()
        self.assertEqual([r['run'] for r in self.ok('liste')['runs']], [run])


if __name__ == '__main__':
    unittest.main()
