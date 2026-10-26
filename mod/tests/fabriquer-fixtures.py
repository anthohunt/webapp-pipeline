#!/usr/bin/env python3
"""Fabrique tests/fixtures.ts : des vues rendues par le VRAI programme (programme/webapp.py), sur le faux moteur flux
des tests du programme. Relancer après tout changement de la vue : python3 tests/fabriquer-fixtures.py"""
import json
import pathlib
import sys

ICI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / 'programme' / 'tests'))
import test_webapp  # noqa: E402


class Fab(test_webapp.TestEtapes2et3):
    def runTest(self):
        pass


def main():
    f = Fab()
    f.setUp()
    try:
        vues = {}
        v = f.ok('ouvrir', projet='Covoiturage Facile', session='s1')
        vues['VUE_NEUF'] = v
        run, ws = v['run'], v['workspace']
        f.ok('pitch', run=run, citation='Une app pour partager les frais de trajet')
        f.ecrire(ws, 'docs/pipeline/concept.md', '# Concept\n\nPartager les frais.')
        f.ok('decision', run=run, sous_etape='E1.2', resume='Usage en voiture, à plusieurs', citation='en voiture, à 3 ou 4', option='A')
        f.ok('avancer', run=run, sous_etape='E1.2', etat='a_valider')
        vues['VUE_A_VALIDER'] = f.ok('etat', run=run)
        f.ok('avancer', run=run, sous_etape='E1.2', etat='validee', citation='A')
        for sid, fichiers in [('E1.3', ['docs/pipeline/cahier-des-charges.md']),
                              ('E1.4', ['docs/pipeline/parcours-utilisateur.json', 'docs/pipeline/parcours-utilisateur.md']),
                              ('E1.5', ['docs/pipeline/design/stories-v1.json']),
                              ('E1.6', ['docs/pipeline/design/mockup.html', 'docs/pipeline/design/mockup-public-url.txt', 'docs/pipeline/design/screens.json'])]:
            for x in fichiers:
                f.ecrire(ws, x, 'https://maquettes.example.org/design/covoiturage-facile/' if x.endswith('url.txt') else 'x')
            f.ok('avancer', run=run, sous_etape=sid, etat='a_valider')
            f.ok('avancer', run=run, sous_etape=sid, etat='validee', citation='oui')
        vues['VUE_TEST_MAQUETTE'] = f.ok('etat', run=run)
        f.ecrire(ws, 'docs/pipeline/design/validation.md', 'ok')
        f.ok('avancer', run=run, sous_etape='E1.7', etat='validee', citation="c'est bon pour lui")
        f.ecrire(ws, 'GATE_VERT')
        f.ok('cloturer', run=run)
        vues['VUE_A_LANCER'] = f.ok('etat', run=run)
        f.ok('lancer', run=run)
        f.ecrire(ws, 'ETAT_CONSTRUCTION.json', {'en_cours': True, 'phase': 'jalons', 'tour': 0, 'bloque': None, 'jalon_courant': 'M2',
                                                'jalons': [{'id': 'M1', 'titre': 'Prix', 'statut': 'fait'}, {'id': 'M2', 'titre': 'Trajet', 'statut': 'en-cours'}]})
        vues['VUE_CONSTRUCTION'] = f.ok('etat', run=run)
        f.ecrire(ws, 'ETAT_CONSTRUCTION.json', {'en_cours': False, 'phase': 'jalons', 'tour': 0, 'bloque': 'relances épuisées sur M2',
                                                'jalons': [{'id': 'M1', 'titre': 'Prix', 'statut': 'fait'}, {'id': 'M2', 'titre': 'Trajet', 'statut': 'en-cours'}]})
        vues['VUE_BLOQUEE'] = f.ok('etat', run=run)
        f.finir(ws, 0, 'V1')
        vues['VUE_REVUE'] = f.ok('etat', run=run)
        f.ok('revue', run=run, verdict='good', citation="c'est parfait")
        vues['VUE_CLOSE'] = f.ok('etat', run=run)
        racine = str(pathlib.Path(ws).parent)
        sortie = ['// Fabriqué par tests/fabriquer-fixtures.py depuis le vrai programme. Ne pas éditer à la main.',
                  "import type { Vue } from '../types'", '']
        for nom, val in vues.items():
            texte = json.dumps(val, ensure_ascii=False, indent=1).replace(racine, '/var/lib/webapp-runs')
            sortie.append(f'export const {nom}: Vue = {texte} as Vue\n')
        (ICI / 'fixtures.ts').write_text('\n'.join(sortie), encoding='utf-8')
        print('fixtures.ts :', ', '.join(vues))
    finally:
        f.tearDown()


if __name__ == '__main__':
    main()
