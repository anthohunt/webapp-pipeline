#!/usr/bin/env python3
"""Tests par mutation des contrôles de la pipeline web app en 3 étapes.

    python3 -m unittest pipeline-runtime/tests/test_webapp_3_etapes.py   (depuis le monorepo)
    python3 pipeline-runtime/tests/test_webapp_3_etapes.py

Un workspace minimal mais complet est fabriqué dans un dossier temporaire ; il doit
passer les trois contrôles (parcours, construire, revue). Chaque test lui applique UNE
mutation — un fichier qui manque, un écran inconnu, un tour non traité… — et exige que
le contrôle la refuse avec le bon contrat. Un contrôle qui laisse passer une mutation
est un contrôle qui ne contrôle rien.
"""
import importlib.util, json, os, pathlib, shutil, sys, tempfile, time, unittest

ICI = pathlib.Path(__file__).resolve().parent
VAL = ICI.parent / 'validators'


def charger(nom):
    spec = importlib.util.spec_from_file_location(nom, VAL / f'{nom}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PARCOURS = charger('webapp_parcours')
CONSTRUIRE = charger('webapp_construire')
REVUE = charger('webapp_revue')
CONCEVOIR = charger('webapp_concevoir')

CDC = """# Cahier des charges
## But
Partager les frais d'un trajet en covoiturage.
## Utilisateurs
Conducteurs et passagers.
## Périmètre V1
Coût du trajet et part de chacun.
## Hors périmètre
Paiement.
## Contraintes
Mobile d'abord.
## Sources de données
Saisie de l'utilisateur (aucune API externe).
"""


def ecrire(ws, chemin, contenu):
    p = ws / chemin
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(contenu, (dict, list)):
        contenu = json.dumps(contenu, ensure_ascii=False, indent=1)
    p.write_text(contenu, encoding='utf-8')
    return p


def fabriquer(ws):
    """Un workspace qui passe les trois contrôles."""
    w = ecrire(ws, 'WORKSPACE.txt', 'run: test\n')
    os.utime(w, (time.time() - 3600, time.time() - 3600))
    ecrire(ws, 'docs/pipeline/design/screens.json', {'screens': [
        {'id': 'S1', 'name': 'Prix', 'interactive_elements': ['liste']},
        {'id': 'S2', 'name': 'Trajet', 'interactive_elements': ['calculer']}]})
    ecrire(ws, 'docs/pipeline/stories.json', [
        {'id': 'US-1.1', 'story': 'voir les prix', 'screen': 'S1'},
        {'id': 'US-2.1', 'story': 'calculer un trajet', 'screen': 'S2'}])
    ecrire(ws, 'docs/pipeline/design/stories-v1.json', [{'id': 'US-1.1'}, {'id': 'US-2.1'}])
    ecrire(ws, 'docs/pipeline/cahier-des-charges.md', CDC)
    ecrire(ws, 'docs/pipeline/parcours-utilisateur.json', {'parcours': [
        {'id': 'P1', 'titre': 'Je calcule un trajet', 'qui': 'un conducteur', 'but': 'savoir le coût',
         'etapes': [{'n': 1, 'ecran': 'S1', 'geste': 'je regarde les prix', 'stories': ['US-1.1']},
                    {'n': 2, 'ecran': 'S2', 'geste': 'je calcule', 'stories': ['US-2.1']}]}]})
    ecrire(ws, 'docs/pipeline/parcours-utilisateur.md', '# Parcours\n## P1 — Je calcule un trajet\n…\n')
    ecrire(ws, 'docs/pipeline/roadmap-approved.json', {'approuve': True, 'milestones': [
        {'n': 1, 'titre': 'Les prix'}, {'n': 2, 'titre': 'Le trajet'}]})
    ecrire(ws, 'docs/pipeline/status.md', '# Status\n- [x] Milestone 1 — Les prix\n'
                                          '- [x] Milestone 2 — Le trajet\n')
    for n in (1, 2):
        ecrire(ws, f'docs/pipeline/m{n}-journal.md', f'# M{n}\n## Vérificateur — cycle 1\nVerdict : PASS\n')
        ecrire(ws, f'tests/e2e/verification/m{n}/US-{n}.1-01.png', 'png')
    ecrire(ws, 'docs/pipeline/avancement.json', {
        'phase': 'fini', 'tour': 0, 'jalon_courant': None,
        'jalons': [{'id': 'M1', 'titre': 'Les prix', 'statut': 'fait'},
                   {'id': 'M2', 'titre': 'Le trajet', 'statut': 'fait'}],
        'maj': '2026-10-24T10:00:00Z'})
    ecrire(ws, 'docs/pipeline/app-url.txt', 'https://app.example.org\n')
    ecrire(ws, 'video/video-url.txt', 'https://montage.example.org/app/?code=abc\n')
    ecrire(ws, 'video/versions.json', {'versions': [
        {'version': 'V1', 'tour': 0, 'date': '2026-10-24T11:00:00Z', 'sequences': ['s1'], 'refilmees': ['s1']}]})
    ecrire(ws, 'docs/pipeline/revue.json', {'tours': [
        {'tour': 1, 'verdict': 'good', 'date': '2026-10-27T10:00:00Z', 'citation': "c'est bon"}]})


def ajouter_tour_retours(ws, statut='traite', avec_version=True):
    """La revue 1 a rendu des retours, traités au tour 1 (V2), puis la revue 2 dit good."""
    ecrire(ws, 'docs/pipeline/revue.json', {'tours': [
        {'tour': 1, 'verdict': 'retours', 'date': '2026-10-27T10:00:00Z', 'citation': 'le bouton est trop petit'},
        {'tour': 2, 'verdict': 'good', 'date': '2026-10-28T10:00:00Z', 'citation': 'good'}]})
    ecrire(ws, 'docs/pipeline/retours/tour-1.json', {'tour': 1, 'date': '2026-10-27T10:05:00Z', 'statut': statut,
        'retours': [{'id': 'R1', 'dit': 'le bouton est trop petit', 'histoire': 'US-2.1', 'ecran': 'S2',
                     'attendu': 'le bouton Calculer fait au moins 44 px de haut'}]})
    ecrire(ws, 'docs/pipeline/retours/tour-1.md', '# Tour 1\n- R1 — le bouton est trop petit\n')
    v = {'versions': [
        {'version': 'V1', 'tour': 0, 'date': '2026-10-24T11:00:00Z', 'sequences': ['s1'], 'refilmees': ['s1']}]}
    if avec_version:
        v['versions'].append({'version': 'V2', 'tour': 1, 'date': '2026-10-27T15:00:00Z',
                              'sequences': ['s1'], 'refilmees': ['s1']})
    ecrire(ws, 'video/versions.json', v)
    av = json.loads((ws / 'docs/pipeline/avancement.json').read_text())
    av['tour'] = 1
    ecrire(ws, 'docs/pipeline/avancement.json', av)


class Base(unittest.TestCase):
    def setUp(self):
        self.ws = pathlib.Path(tempfile.mkdtemp(prefix='webapp3-'))
        fabriquer(self.ws)

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def refuse(self, mod, code, motif=''):
        errs = mod.validate(str(self.ws))
        self.assertTrue(any(e.startswith(code) and motif in e for e in errs),
                        f'{mod.__name__} aurait dû refuser par {code} {motif!r} ; il a rendu {errs}')

    def json(self, chemin):
        return json.loads((self.ws / chemin).read_text())


class TemoinVert(Base):
    def test_le_workspace_temoin_passe_les_trois_controles(self):
        for mod in (PARCOURS, CONSTRUIRE, REVUE):
            self.assertEqual(mod.validate(str(self.ws)), [], mod.__name__)

    def test_un_tour_de_retours_traite_passe(self):
        ajouter_tour_retours(self.ws)
        for mod in (CONSTRUIRE, REVUE):
            self.assertEqual(mod.validate(str(self.ws)), [], mod.__name__)

    def test_le_composite_appelle_le_moment_parcours(self):
        (self.ws / 'docs/pipeline/parcours-utilisateur.json').unlink()
        errs = CONCEVOIR.validate(str(self.ws))
        self.assertTrue(any(e.startswith('[parcours] C2') for e in errs), errs)


class MutationsParcours(Base):
    def test_cahier_des_charges_manquant(self):
        (self.ws / 'docs/pipeline/cahier-des-charges.md').unlink()
        self.refuse(PARCOURS, 'C1', 'absent')

    def test_cahier_sans_hors_perimetre(self):
        ecrire(self.ws, 'docs/pipeline/cahier-des-charges.md', CDC.replace('## Hors périmètre\nPaiement.\n', ''))
        self.refuse(PARCOURS, 'C1', 'hors périmètre')

    def test_cahier_sans_sources(self):
        ecrire(self.ws, 'docs/pipeline/cahier-des-charges.md', CDC.split('## Sources')[0])
        self.refuse(PARCOURS, 'C1', 'sources de données')

    def test_parcours_manquant(self):
        (self.ws / 'docs/pipeline/parcours-utilisateur.json').unlink()
        self.refuse(PARCOURS, 'C2', 'absent')

    def test_parcours_json_invalide(self):
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', '{"parcours": [')
        self.refuse(PARCOURS, 'C2', 'JSON invalide')

    def test_parcours_vide(self):
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', {'parcours': []})
        self.refuse(PARCOURS, 'C2')

    def test_parcours_sans_but(self):
        j = self.json('docs/pipeline/parcours-utilisateur.json'); del j['parcours'][0]['but']
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', j)
        self.refuse(PARCOURS, 'C2', '`but`')

    def test_etapes_mal_numerotees(self):
        j = self.json('docs/pipeline/parcours-utilisateur.json'); j['parcours'][0]['etapes'][1]['n'] = 3
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', j)
        self.refuse(PARCOURS, 'C2', 'position 2')

    def test_ecran_inconnu(self):
        j = self.json('docs/pipeline/parcours-utilisateur.json'); j['parcours'][0]['etapes'][0]['ecran'] = 'S9'
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', j)
        self.refuse(PARCOURS, 'C3', 'S9')

    def test_histoire_inconnue(self):
        j = self.json('docs/pipeline/parcours-utilisateur.json'); j['parcours'][0]['etapes'][0]['stories'] = ['US-7.7']
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', j)
        self.refuse(PARCOURS, 'C4', 'US-7.7')

    def test_etape_sans_histoire(self):
        j = self.json('docs/pipeline/parcours-utilisateur.json'); j['parcours'][0]['etapes'][1]['stories'] = []
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.json', j)
        self.refuse(PARCOURS, 'C4', 'aucune histoire')

    def test_lecture_humaine_manquante(self):
        (self.ws / 'docs/pipeline/parcours-utilisateur.md').unlink()
        self.refuse(PARCOURS, 'C5')

    def test_lecture_humaine_qui_oublie_un_parcours(self):
        ecrire(self.ws, 'docs/pipeline/parcours-utilisateur.md', '# Parcours\nrien\n')
        self.refuse(PARCOURS, 'C5', 'P1')


class MutationsConstruire(Base):
    def test_jalon_non_coche(self):
        ecrire(self.ws, 'docs/pipeline/status.md', '- [x] Milestone 1\n- [ ] Milestone 2\n')
        self.refuse(CONSTRUIRE, 'C2', 'm2')

    def test_journal_sans_pass_du_verificateur(self):
        ecrire(self.ws, 'docs/pipeline/m2-journal.md', '# M2\n## Auditor\nPASS\n')
        self.refuse(CONSTRUIRE, 'C3', 'vérificateur')

    def test_journal_dont_le_dernier_verdict_est_fail(self):
        ecrire(self.ws, 'docs/pipeline/m1-journal.md', '# M1\n## Vérificateur — cycle 1\nPASS\n'
                                                      '## Vérificateur — cycle 2\nVerdict : FAIL\n')
        self.refuse(CONSTRUIRE, 'C3', 'FAIL')

    def test_journal_herite(self):
        j = self.ws / 'docs/pipeline/m1-journal.md'
        os.utime(j, (time.time() - 7200, time.time() - 7200))
        self.refuse(CONSTRUIRE, 'C4', 'm1')

    def test_pas_de_captures_du_verificateur(self):
        shutil.rmtree(self.ws / 'tests/e2e/verification/m2')
        self.refuse(CONSTRUIRE, 'C5', 'm2')

    def test_avancement_manquant(self):
        (self.ws / 'docs/pipeline/avancement.json').unlink()
        self.refuse(CONSTRUIRE, 'C6', 'absent')

    def test_avancement_pas_fini(self):
        j = self.json('docs/pipeline/avancement.json'); j['phase'] = 'tournage'
        ecrire(self.ws, 'docs/pipeline/avancement.json', j)
        self.refuse(CONSTRUIRE, 'C6', 'tournage')

    def test_avancement_phase_inconnue(self):
        j = self.json('docs/pipeline/avancement.json'); j['phase'] = 'livre'
        ecrire(self.ws, 'docs/pipeline/avancement.json', j)
        self.refuse(CONSTRUIRE, 'C6', 'hors de')

    def test_avancement_jalon_pas_fait(self):
        j = self.json('docs/pipeline/avancement.json'); j['jalons'][1]['statut'] = 'en-cours'
        ecrire(self.ws, 'docs/pipeline/avancement.json', j)
        self.refuse(CONSTRUIRE, 'C6', 'M2')

    def test_url_de_production_manquante(self):
        (self.ws / 'docs/pipeline/app-url.txt').unlink()
        self.refuse(CONSTRUIRE, 'C7')

    def test_lien_video_sans_code(self):
        ecrire(self.ws, 'video/video-url.txt', 'https://montage.example.org/app/\n')
        self.refuse(CONSTRUIRE, 'C8', 'code=')

    def test_sans_outil_de_tournage_la_video_nest_pas_demandee(self):
        shutil.rmtree(self.ws / 'video')
        os.environ['WEBAPP_VIDEO'] = '0'
        try:
            self.assertEqual(CONSTRUIRE.validate(str(self.ws)), [])
        finally:
            os.environ.pop('WEBAPP_VIDEO')

    def test_versions_manquantes(self):
        (self.ws / 'video/versions.json').unlink()
        self.refuse(CONSTRUIRE, 'C9')

    def test_versions_non_consecutives(self):
        j = self.json('video/versions.json'); j['versions'][0]['version'] = 'V2'
        ecrire(self.ws, 'video/versions.json', j)
        self.refuse(CONSTRUIRE, 'C9', 'attendu V1')

    def test_refilmee_hors_des_sequences(self):
        j = self.json('video/versions.json'); j['versions'][0]['refilmees'] = ['s4']
        ecrire(self.ws, 'video/versions.json', j)
        self.refuse(CONSTRUIRE, 'C9', 's4')

    def test_tour_de_retours_a_traiter(self):
        ajouter_tour_retours(self.ws, statut='a-traiter', avec_version=False)
        self.refuse(CONSTRUIRE, 'C10', 'a-traiter')

    def test_tour_traite_sans_nouvelle_version(self):
        ajouter_tour_retours(self.ws, statut='traite', avec_version=False)
        self.refuse(CONSTRUIRE, 'C10', 'sans version')

    def test_avancement_en_retard_sur_le_tour(self):
        ajouter_tour_retours(self.ws)
        j = self.json('docs/pipeline/avancement.json'); j['tour'] = 0
        ecrire(self.ws, 'docs/pipeline/avancement.json', j)
        self.refuse(CONSTRUIRE, 'C10', 'dernier tour')


class MutationsRevue(Base):
    def test_revue_manquante(self):
        (self.ws / 'docs/pipeline/revue.json').unlink()
        self.refuse(REVUE, 'C1', 'absent')

    def test_verdict_inconnu(self):
        ecrire(self.ws, 'docs/pipeline/revue.json', {'tours': [
            {'tour': 1, 'verdict': 'bof', 'date': '2026-10-27', 'citation': 'bof'}]})
        self.refuse(REVUE, 'C1', 'bof')

    def test_citation_vide(self):
        ecrire(self.ws, 'docs/pipeline/revue.json', {'tours': [
            {'tour': 1, 'verdict': 'good', 'date': '2026-10-27', 'citation': ' '}]})
        self.refuse(REVUE, 'C1', 'citation')

    def test_revue_sans_video(self):
        (self.ws / 'video/versions.json').unlink()
        self.refuse(REVUE, 'C2', 'tour 0')

    def test_revue_sans_video_permise_sans_outil_de_tournage(self):
        (self.ws / 'video/versions.json').unlink()
        os.environ['WEBAPP_VIDEO'] = '0'
        try:
            self.assertFalse([e for e in REVUE.validate(str(self.ws)) if e.startswith('C2')])
        finally:
            os.environ.pop('WEBAPP_VIDEO')

    def test_good_suivi_dun_autre_tour(self):
        ajouter_tour_retours(self.ws)
        j = self.json('docs/pipeline/revue.json'); j['tours'][0]['verdict'] = 'good'
        ecrire(self.ws, 'docs/pipeline/revue.json', j)
        self.refuse(REVUE, 'C3')

    def test_retours_sans_fichier(self):
        ajouter_tour_retours(self.ws)
        (self.ws / 'docs/pipeline/retours/tour-1.json').unlink()
        self.refuse(REVUE, 'C4', 'tour-1.json')

    def test_retour_sans_attendu(self):
        ajouter_tour_retours(self.ws)
        j = self.json('docs/pipeline/retours/tour-1.json'); j['retours'][0]['attendu'] = ''
        ecrire(self.ws, 'docs/pipeline/retours/tour-1.json', j)
        self.refuse(REVUE, 'C4', '`attendu`')

    def test_retour_sur_ecran_inconnu(self):
        ajouter_tour_retours(self.ws)
        j = self.json('docs/pipeline/retours/tour-1.json'); j['retours'][0]['ecran'] = 'S9'
        ecrire(self.ws, 'docs/pipeline/retours/tour-1.json', j)
        self.refuse(REVUE, 'C4', 'S9')

    def test_retour_sur_histoire_inconnue(self):
        ajouter_tour_retours(self.ws)
        j = self.json('docs/pipeline/retours/tour-1.json'); j['retours'][0]['histoire'] = 'US-9.9'
        ecrire(self.ws, 'docs/pipeline/retours/tour-1.json', j)
        self.refuse(REVUE, 'C4', 'US-9.9')

    def test_good_avec_fichier_de_retours(self):
        ecrire(self.ws, 'docs/pipeline/retours/tour-1.json', {'tour': 1, 'statut': 'a-traiter', 'retours': []})
        self.refuse(REVUE, 'C5')


if __name__ == '__main__':
    unittest.main(verbosity=1)
