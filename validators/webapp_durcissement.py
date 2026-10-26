"""
Validateur webapp 6 — DURCIR.

Gate de sortie du nœud « durcir » : les quatre audits ont-ils été menés sur
l'application EN PRODUCTION, avec des mesures, et relus par un évaluateur
d'honnêteté ? Le trou classique est l'audit de complaisance : un rapport qui
conclut « tout va bien » sans une seule mesure, produit contre un serveur de
développement.

Contrats (sur la passe la plus récente r{N}) :
1. Les quatre rapports du round r{N} existent : perf, stabilité, accessibilité, sécurité.
2. Le journal r{N} existe et nomme l'URL de PRODUCTION auditée + le commit.
3. Aucun rapport n'audite localhost / un serveur de dev.
4. Chaque rapport porte des mesures chiffrées (un audit sans nombre n'est pas un audit).
5. Chaque rapport a son évaluation d'honnêteté r{N}-{domaine}-eval.md.
6. Le rapport consolidé r{N} existe et classe les défauts par priorité.
7. Les rapports datent de cette run (plus récents que WORKSPACE.txt).
8. La non-régression r{N} a tourné.
"""
import pathlib, re

DOCS = 'docs/pipeline'
DOMAINES = (('perf', 'performance'), ('stability', 'stabilité'),
            ('a11y', 'accessibilité'), ('security', 'sécurité'))


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def _round(d):
    """Numéro de la passe de durcissement la plus récente."""
    ns = {int(m.group(1)) for f in d.glob('hardening-r*-*.md')
          for m in [re.search(r'hardening-r(\d+)-', f.name)] if m}
    return max(ns) if ns else None


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    n = _round(d)
    if n is None:
        errs.append(f"C1: aucun rapport `{DOCS}/hardening-r*-*.md` — le durcissement n'a pas eu lieu")
        return errs

    ref = (ws / 'WORKSPACE.txt').stat().st_mtime if (ws / 'WORKSPACE.txt').exists() else 0
    prod_url = None

    jr = d / f'hardening-r{n}-journal.md'
    if not jr.exists():
        errs.append(f"C2: `hardening-r{n}-journal.md` absent — la cible d'audit et le commit "
                    "audité ne sont consignés nulle part")
    else:
        t = _txt(jr)
        m = re.search(r'https?://[^\s)\]]+', t)
        prod_url = m.group() if m else None
        if not prod_url:
            errs.append(f"C2: le journal r{n} ne porte aucune URL — la cible d'audit n'est pas "
                        "vérifiée")
        if not re.search(r'\b[0-9a-f]{7,40}\b', t):
            errs.append(f"C2: le journal r{n} ne porte pas le commit audité — impossible de savoir "
                        "ce qui a été mesuré")

    for suff, nom in DOMAINES:
        r = d / f'hardening-r{n}-{suff}-report.md'
        if not r.exists() or r.stat().st_size == 0:
            errs.append(f"C1: rapport {nom} absent (`hardening-r{n}-{suff}-report.md`) — "
                        "les quatre audits sont obligatoires")
            continue
        t = _txt(r)

        if re.search(r'localhost|127\.0\.0\.1|:5199|:5173|vite\s+dev', t, re.I):
            errs.append(f"C3: le rapport {nom} audite un serveur de développement — ni la "
                        "compilation, ni le cache, ni les en-têtes ne sont ceux de la production")

        chiffres = re.findall(r'\d+(?:[.,]\d+)?\s*(?:ms|s|kb|ko|mb|mo|%|fps|req|px)', t, re.I)
        if len(chiffres) < 3:
            errs.append(f"C4: le rapport {nom} ne contient presque aucune mesure chiffrée "
                        f"({len(chiffres)}) — mesurer d'abord, diagnostiquer ensuite")

        ev = d / f'hardening-r{n}-{suff}-eval.md'
        if not ev.exists() or ev.stat().st_size == 0:
            errs.append(f"C5: aucune évaluation d'honnêteté pour le rapport {nom} "
                        f"(`hardening-r{n}-{suff}-eval.md`) — un auditeur ne se relit pas seul")

        if ref and r.stat().st_mtime < ref:
            errs.append(f"C7: le rapport {nom} est plus ancien que `WORKSPACE.txt` — il vient "
                        "d'une run précédente")

    cons = d / f'hardening-r{n}-consolidated.md'
    if not cons.exists() or cons.stat().st_size == 0:
        errs.append(f"C6: `hardening-r{n}-consolidated.md` absent — les défauts ne sont ni "
                    "dédoublonnés ni priorisés")
    elif not re.search(r'(priorit|P0|P1|critique|majeur|mineur)', _txt(cons), re.I):
        errs.append(f"C6: le rapport consolidé r{n} ne classe pas les défauts par priorité — "
                    "sans priorité, la correction se fait au hasard")

    reg = d / f'hardening-r{n}-regression.md'
    if not reg.exists() or reg.stat().st_size == 0:
        errs.append(f"C8: `hardening-r{n}-regression.md` absent — rien ne dit que les corrections "
                    "n'ont pas cassé les jalons précédents")

    return errs
