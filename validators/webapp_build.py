"""
Validateur webapp 5 — CONSTRUIRE.

Gate de sortie du nœud « construire » : les jalons cochés ont-ils VRAIMENT été
construits sous le cycle complet, ou cochés à la main ? Le contrat central est
la traçabilité : un jalon coché sans journal, ou dont le journal ne porte pas le
verdict PASS de l'auditeur ET de la contre-évaluation, est un jalon auto-déclaré.

Contrats :
1. status.md présent et déclare au moins un jalon coché.
2. TOUS les jalons approuvés sont cochés (le nœud se relance jalon par jalon ; le
   gate ne passe au vert qu'une fois la feuille de route épuisée).
3. Chaque jalon coché a son `docs/pipeline/m{N}-journal.md` non vide.
4. Chaque journal porte le double verdict : auditeur PASS et contre-évaluation PASS.
5. Les journaux ont été écrits pendant cette run (plus récents que WORKSPACE.txt).
6. Chaque jalon coché a laissé des captures d'exploration (preuve que l'app a été
   ouverte, pas seulement compilée).
7. project-memory.md tenu à jour, ≤ 2000 caractères.
"""
import json, pathlib, re

DOCS = 'docs/pipeline'


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def _coches(status_txt):
    return sorted({int(m.group(1)) for m in
                   re.finditer(r'\[x\][^\n]*?(?:milestone|jalon)\s*#?\s*(\d+)', status_txt, re.I)} |
                  {int(m.group(1)) for m in
                   re.finditer(r'(?:milestone|jalon)\s*#?\s*(\d+)[^\n]*?\[x\]', status_txt, re.I)})


def _approuves(ws):
    p = ws / DOCS / 'roadmap-approved.json'
    if not p.exists():
        return []
    try:
        j = json.loads(_txt(p))
    except json.JSONDecodeError:
        return []
    out = []
    for m in (j.get('milestones') or j.get('jalons') or []):
        v = m.get('n') or m.get('id') or m.get('numero') if isinstance(m, dict) else m
        mm = re.search(r'\d+', str(v or ''))
        if mm:
            out.append(int(mm.group()))
    return sorted(set(out))


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    stt = d / 'status.md'
    if not stt.exists() or stt.stat().st_size == 0:
        errs.append(f"C1: `{DOCS}/status.md` absent/vide — l'état du build est introuvable")
        return errs

    coches = _coches(_txt(stt))
    if not coches:
        errs.append("C1: aucun jalon coché dans `status.md` — rien n'a été construit, ou l'état "
                    "n'a pas été tenu")

    attendus = _approuves(ws)
    restants = [n for n in attendus if n not in coches]
    if restants:
        errs.append("C2: jalon(s) approuvé(s) non construit(s) : " +
                    ', '.join(f'm{n}' for n in restants) +
                    " — relance ce nœud jusqu'à épuisement de la feuille de route")

    ref = (ws / 'WORKSPACE.txt').stat().st_mtime if (ws / 'WORKSPACE.txt').exists() else 0

    for n in coches:
        j = d / f'm{n}-journal.md'
        if not j.exists() or j.stat().st_size == 0:
            errs.append(f"C3: jalon m{n} coché mais `{DOCS}/m{n}-journal.md` absent/vide — "
                        "un jalon sans journal est auto-déclaré")
            continue
        t = _txt(j)
        if not re.search(r'audit(eur|or)[^\n]{0,80}\bPASS\b', t, re.I):
            errs.append(f"C4: journal m{n} sans verdict PASS de l'auditeur — le cycle n'est pas "
                        "allé au bout")
        if not re.search(r'(contre-?[ée]valuation|evaluator\s*r?2)[^\n]{0,80}\bPASS\b', t, re.I):
            errs.append(f"C4: journal m{n} sans PASS de la contre-évaluation — l'honnêteté de "
                        "l'audit n'a pas été contrôlée")
        if ref and j.stat().st_mtime < ref:
            errs.append(f"C5: journal m{n} plus ancien que `WORKSPACE.txt` — il vient d'une run "
                        "précédente")

    expl = ws / 'tests' / 'e2e' / 'exploration'
    if coches and (not expl.exists() or not any(expl.rglob('*.png'))):
        errs.append("C6: aucune capture dans `tests/e2e/exploration/` — rien ne prouve que l'app "
                    "a été ouverte et regardée pendant le build")

    pm = d / 'project-memory.md'
    if not pm.exists():
        errs.append("C7: `project-memory.md` absent — la mémoire roulante du projet n'est pas tenue")
    elif len(_txt(pm)) > 2000:
        errs.append(f"C7: `project-memory.md` fait {len(_txt(pm))} car (> 2000)")

    return errs
