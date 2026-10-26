"""
Validateur webapp 7 — LIVRER.

Gate de sortie du nœud « livrer » : la livraison dit-elle la vérité sur l'écart
entre ce qui était promis et ce qui existe ? Le contrat central : CHAQUE histoire
du kit initial doit être classée dans la spec finale (inchangée / modifiée /
nouvelle / retirée). Une histoire qui disparaît sans être déclarée retirée, c'est
une promesse effacée en silence.

Contrats :
1. Les livrables de livraison sont présents et non vides.
2. Chaque histoire de stories.json est classée dans spec-final.md.
3. spec-final.md est un fichier NOUVEAU (spec.md reste le témoin du plan initial).
4. La passe de captures finale existe et est distincte de l'exploration du build.
5. Le parcours illustré est autonome (captures embarquées, pas de lien local mort).
6. L'audit de livraison porte une note et une liste de trous (même vide, déclarée).
7. Les livrables datent de cette run.
"""
import json, pathlib, re

DOCS = 'docs/pipeline'
DEL = 'docs/delivery'
ATTENDUS = ('reconciliation-report.md', 'spec-final.md', 'decisions-log.md',
            'final-verification.md', 'final-audit.md')
CLASSES = r'(UNCHANGED|MODIFIED|NEW|REMOVED|INCHANG|MODIFI|NOUVELLE|RETIR)'


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    for f in ATTENDUS:
        p = d / f
        if not p.exists() or p.stat().st_size == 0:
            errs.append(f"C1: `{DOCS}/{f}` absent/vide — la livraison est incomplète")

    wj = ws / DEL / 'user-journey-walkthrough.html'
    if not wj.exists() or wj.stat().st_size == 0:
        errs.append(f"C1: `{DEL}/user-journey-walkthrough.html` absent/vide — rien à remettre à "
                    "un lecteur humain")

    # C2 — chaque histoire promise est classée
    sf = d / 'spec-final.md'
    stj = d / 'stories.json'
    if sf.exists() and stj.exists():
        final = _txt(sf)
        try:
            j = json.loads(_txt(stj))
            stories = j if isinstance(j, list) else (j.get('stories') or j.get('user_stories') or [])
            non_classees = []
            for s in stories:
                if not isinstance(s, dict):
                    continue
                sid = str(s.get('id') or '').strip()
                if not sid:
                    continue
                m = re.search(re.escape(sid) + r'[^\n]{0,200}', final)
                if not m or not re.search(CLASSES, m.group(), re.I):
                    non_classees.append(sid)
            if non_classees:
                errs.append(f"C2: {len(non_classees)} histoire(s) non classée(s) dans "
                            "`spec-final.md` (" + ', '.join(non_classees[:6]) +
                            ") — une promesse qui disparaît sans être déclarée retirée est une "
                            "promesse effacée en silence")
        except json.JSONDecodeError as e:
            errs.append(f"C2: `stories.json` illisible pour la réconciliation: {e}")

    # C3 — spec.md n'a pas été écrasée par la spec finale
    sp = d / 'spec.md'
    if sp.exists() and sf.exists() and _txt(sp).strip() == _txt(sf).strip():
        errs.append("C3: `spec.md` et `spec-final.md` sont identiques — le plan initial a été "
                    "écrasé ; on perd la trace de ce qui avait été promis")

    # C4 — passe de captures finale, distincte de l'exploration du build
    fin = ws / 'tests' / 'e2e' / 'final'
    shots_fin = list(fin.rglob('*.png')) if fin.exists() else []
    if not shots_fin:
        errs.append("C4: aucune capture dans `tests/e2e/final/` — la vérification finale n'a pas "
                    "eu lieu (les captures d'exploration du build ne comptent pas)")
    liv = ws / DEL / 'screenshots'
    if not liv.exists() or not any(liv.rglob('*.png')):
        errs.append(f"C4: `{DEL}/screenshots/` vide — le paquet de livraison n'embarque pas ses "
                    "captures")

    # C5 — parcours autonome
    if wj.exists():
        t = _txt(wj)
        if 'data:image' not in t and re.search(r'src\s*=\s*["\'](?!https?:|data:)', t):
            errs.append("C5: le parcours illustré référence des images par chemin local — hors du "
                        "workspace, la page se vide ; embarque les captures en base64")

    # C6 — audit de livraison exploitable
    fa = d / 'final-audit.md'
    if fa.exists():
        t = _txt(fa)
        if not re.search(r'\b(\d{1,3})\s*/\s*(5|10|100)\b|\b(PASS|FAIL|ÉCHEC|RÉUSSI)\b', t, re.I):
            errs.append("C6: `final-audit.md` sans note ni verdict — un audit qui ne conclut pas "
                        "ne sert à rien")

    ref = (ws / 'WORKSPACE.txt').stat().st_mtime if (ws / 'WORKSPACE.txt').exists() else 0
    if ref:
        vieux = [f for f in ATTENDUS if (d / f).exists() and (d / f).stat().st_mtime < ref]
        if vieux:
            errs.append("C7: " + ', '.join(f'`{v}`' for v in vieux) + " plus ancien(s) que "
                        "`WORKSPACE.txt` — livrable(s) hérité(s) d'une run précédente")

    return errs
