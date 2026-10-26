#!/usr/bin/env python3
"""Régénère webapp-design.json depuis le nœud « concevoir » de webapp.json.

webapp-design est le MÊME nœud, joué seul, sur un espace de runs séparé : un
collègue y conçoit SON application sans que sa run ne devienne la
run active de webapp, et sans voir la construction ni la revue, qui ne le concernent
pas.

Rien n'est recopié à la main : toute retouche du nœud « concevoir » se propage en
relançant ce script. Un contenu dupliqué à la main finirait par diverger.
"""
import json, pathlib, sys

W = pathlib.Path(__file__).resolve().parent.parent / 'workflows'
NOEUD = 'concevoir'
src = json.loads((W / 'webapp.json').read_text(encoding='utf-8'))
noeud = next(n for n in src['nodes'] if n['id'] == NOEUD)

noeud = dict(noeud)
noeud['n'] = 1
noeud['suivant'] = []
noeud['note_locale'] = (
    "Étape jouée seule : à la banderole de fin, le design est livré. "
    "Il n'y a pas de nœud suivant dans ce flux — la construction se mène ailleurs."
)

dst = {
    '$schema': src.get('$schema'),
    'id': 'webapp-design',
    'name': 'Design web app — concevoir avec le client, dessiner, spécifier',
    'description': (
        "Le nœud interactif de la pipeline web app, joué seul et sur ses propres runs. "
        "Du pitch au mockup testé et au kit de projet vérifié, en une session de conversation."
    ),
    'workspace_root': '~/webapp-design-runs',
    'nodes': [noeud],
}
(W / 'webapp-design.json').write_text(json.dumps(dst, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('webapp-design.json régénéré depuis le nœud « %s » de webapp.json' % NOEUD)
