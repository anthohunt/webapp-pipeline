"""
Validateur webapp — TON DESIGN VALIDÉ (barrière humaine).

Gate de sortie du nœud « valider-design » : l'opérateur a-t-il vu et validé LA
version courante du canvas ? Le piège est la validation périmée : un accord donné
sur une version, puis un canvas re-publié derrière — la spécification partirait
alors d'un design que personne n'a approuvé.

Contrats :
1. `design/validation.md` présent, non vide, daté.
2. Il est plus récent que `screens.json` ET que `stories-v1.json` : tu as validé la
   version courante du mockup ET de ses histoires, pas un état antérieur.
3. Il porte une décision explicite (validé / à revoir + ce qui a changé).
4. Il a été écrit pendant cette run.
"""
import pathlib, re

D = 'docs/pipeline/design'
DECISION = r'(valid[ée]|approuv[ée]|ok pour la suite|bon pour|go\b)'


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / D
    v = d / 'validation.md'

    if not v.exists() or v.stat().st_size == 0:
        errs.append(f"C1: `{D}/validation.md` absent/vide — le canvas n'a pas été validé ; la "
                    "spécification partirait d'un design que personne n'a regardé")
        return errs

    t = _txt(v)
    if not re.search(r'\d{4}-\d{2}-\d{2}', t):
        errs.append("C1: `validation.md` sans date — une validation sans date ne dit pas sur "
                    "quelle version elle porte")

    for f, quoi in (('screens.json', 'le canvas a bougé'), ('stories-v1.json', 'les histoires ont bougé')):
        ref = d / f
        if ref.exists() and v.stat().st_mtime < ref.stat().st_mtime:
            errs.append(f"C2: `validation.md` est plus ancien que `{f}` — {quoi} après ta "
                        "validation ; revalide l'état courant")

    if not re.search(DECISION, t, re.I):
        errs.append("C3: `validation.md` ne porte aucune décision explicite (validé / à revoir) — "
                    "dis ce que tu approuves, sinon rien ne distingue une note d'un accord")

    if len(t) < 120:
        errs.append(f"C3: `validation.md` fait {len(t)} car — note au moins ce que tu as changé "
                    "sur le canvas et ce que tu valides")

    wsf = ws / 'WORKSPACE.txt'
    if wsf.exists() and v.stat().st_mtime < wsf.stat().st_mtime:
        errs.append("C4: `validation.md` est plus ancien que `WORKSPACE.txt` — validation héritée "
                    "d'un projet précédent")

    return errs
