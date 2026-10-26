"""
Validateur webapp — CADRER, DESSINER, SPÉCIFIER (l'étape interactive, jouée d'une traite).

Ce nœud couvre tout le trajet du pitch au kit vérifié. Son gate ne réécrit aucun
contrat : il APPELLE les cinq validateurs de moments, dans l'ordre du travail, et
préfixe chaque finding par le moment concerné. Une règle continue de vivre à un
seul endroit — le validateur du moment qui la porte.

Moments et validateurs appelés :
  cadrage         → webapp_concept        (concept tranché, hors-périmètre, squelette)
  mockup          → webapp_canvas         (tokens, écrans, histoires v1, deux couches)
  ton test        → webapp_design_valide  (validation datée, postérieure au travail)
  spécification   → webapp_kit            (pile justifiée, histoires complétées, couverture UI)
  pré-vol         → webapp_approbation    (jalons démontrables, cas d'usage, acte de pré-vol)

Le nœud n'est vert que si les cinq passent : le travail n'est pas découpé, son
jugement non plus.
"""
import importlib.util, pathlib

MOMENTS = [
    ('cadrage', 'webapp_concept'),
    ('mockup', 'webapp_canvas'),
    ('ton test', 'webapp_design_valide'),
    ('spécification', 'webapp_kit'),
    ('pré-vol', 'webapp_approbation'),
]


def _charger(nom):
    f = pathlib.Path(__file__).parent / f'{nom}.py'
    if not f.exists():
        return None
    spec = importlib.util.spec_from_file_location(nom, f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate(workspace):
    errs = []
    for moment, nom in MOMENTS:
        mod = _charger(nom)
        if mod is None:
            errs.append(f"[{moment}] validateur `{nom}` introuvable — contrat non vérifié")
            continue
        try:
            for e in mod.validate(workspace):
                errs.append(f"[{moment}] {e}")
        except Exception as exc:  # un validateur qui casse ne doit pas laisser passer le nœud
            errs.append(f"[{moment}] le validateur `{nom}` a échoué : {type(exc).__name__}: {exc}")
    return errs
