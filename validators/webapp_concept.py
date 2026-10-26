"""
Validateur webapp 1 — CONCEVOIR.

Gate de sortie du nœud « concevoir » : le concept est-il TRANCHÉ, ou seulement
raconté ? Un concept qui n'a pas de hors-périmètre n'a pas été décidé, il a été
esquivé — et c'est exactement ce qui fait déraper le build trois nœuds plus loin.

Contrats :
1. WORKSPACE.txt présent (la run est identifiée).
2. concept.md, seed-prompt.md, config.json, status.md, project-memory.md présents.
3. concept.md fait au moins 800 caractères ET nomme le problème, l'utilisateur et
   la boucle cœur.
4. concept.md porte un HORS-PÉRIMÈTRE d'au moins 3 refus explicites.
5. config.json est un JSON valide portant `language` et `design_source`.
6. seed-prompt.md fait au moins 600 caractères — c'est le seul objet qui traverse
   vers Claude Design ; un prompt maigre = un design qui invente.
7. project-memory.md ne dépasse pas 2000 caractères (c'est un résumé roulant, pas
   une archive).
9. Le cadrage n'a PAS tranché la construction : `concept.md` ne nomme ni framework, ni
   base de données, ni support d'exécution. Ces choix appartiennent à la spécification,
   qui les prend avec l'architecture en main ; pris ici, ils gèlent une décision prise
   sans le contexte qui la justifie.
8. Le SQUELETTE a été publié : `skeleton-url.txt` porte une URL d'artifact. Le cadrage
   se fait devant un dessin — une question sur quelque chose de visible posée en texte
   seul fait arbitrer à l'aveugle.
"""
import json, pathlib, re

DOCS = 'docs/pipeline'


def _txt(p):
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    d = ws / DOCS

    if not (ws / 'WORKSPACE.txt').exists():
        errs.append("C1: `WORKSPACE.txt` absent — la run n'est pas identifiée")

    for f in ('concept.md', 'seed-prompt.md', 'config.json', 'status.md', 'project-memory.md'):
        p = d / f
        if not p.exists() or p.stat().st_size == 0:
            errs.append(f"C2: `{DOCS}/{f}` absent/vide — cadrage incomplet")

    c = d / 'concept.md'
    if c.exists():
        t = _txt(c)
        if len(t) < 800:
            errs.append(f"C3: `concept.md` fait {len(t)} car (< 800) — un concept tenu en trois "
                        "lignes n'a pas été creusé : problème, utilisateur, boucle cœur")
        manquants = [nom for nom, rx in (
            ('problème', r'probl[eè]me'),
            ('utilisateur', r'utilisateur|persona|public'),
            ('boucle cœur', r'boucle\s+c(?:œ|oe)ur|core\s+loop'),
        ) if not re.search(rx, t, re.I)]
        if manquants:
            errs.append("C3: `concept.md` ne traite pas : " + ', '.join(manquants) +
                        " — ce sont les trois questions auxquelles le design doit répondre")

        # C4 — le hors-périmètre, le vrai contrat du cadrage
        m = re.search(r'(hors[- ]p[eé]rim[eè]tre|hors[- ]scope|out of scope|ce qu\'?on ne fait pas)',
                      t, re.I)
        if not m:
            errs.append("C4: `concept.md` n'a pas de section HORS-PÉRIMÈTRE — un périmètre sans "
                        "refus explicite n'a pas été tranché ; le build dérivera dessus")
        else:
            bloc = t[m.start():]
            nxt = re.search(r'\n#{1,3} ', bloc[10:])
            if nxt:
                bloc = bloc[:10 + nxt.start()]
            refus = [l for l in bloc.splitlines()
                     if re.match(r'\s*(?:[-*•]|\d+[.)])\s+\S', l)]
            if len(refus) < 3:
                errs.append(f"C4: HORS-PÉRIMÈTRE ne liste que {len(refus)} refus (< 3) — "
                            "trancher, c'est nommer ce qu'on abandonne")

    cfg = d / 'config.json'
    if cfg.exists() and cfg.stat().st_size:
        try:
            j = json.loads(_txt(cfg))
            for k in ('language', 'design_source'):
                if not j.get(k):
                    errs.append(f"C5: `config.json` sans `{k}` — l'état de la run est incomplet")
        except json.JSONDecodeError as e:
            errs.append(f"C5: `config.json` JSON invalide: {e}")

    sp = d / 'seed-prompt.md'
    if sp.exists():
        n = len(_txt(sp))
        if n < 600:
            errs.append(f"C6: `seed-prompt.md` fait {n} car (< 600) — c'est le seul objet qui "
                        "part dans Claude Design : ce qu'il ne dit pas, le design l'inventera")

    pm = d / 'project-memory.md'
    if pm.exists():
        n = len(_txt(pm))
        if n > 2000:
            errs.append(f"C7: `project-memory.md` fait {n} car (> 2000) — c'est un résumé roulant, "
                        "il doit rester relisible d'un coup d'œil")

    PILE = re.compile(r'\b(react|vue|angular|svelte|next\.?js|nuxt|vite|tailwind|postgres|'
                      r'mysql|mongodb|firebase|supabase|pwa|react native|flutter|electron|'
                      r'node\.?js|django|rails|vercel|netlify|aws|docker)\b', re.I)
    if c.exists():
        trouves = sorted({m.group().lower() for m in PILE.finditer(_txt(c))})
        if trouves:
            errs.append("C9: `concept.md` tranche la construction (" + ', '.join(trouves[:6]) +
                        ") — le cadrage décrit l'usage ; la pile se décide à la spécification, "
                        "avec l'architecture en main. Déplace ça dans `questions-techniques.md`.")

    sk = d / 'skeleton-url.txt'
    if not sk.exists() or sk.stat().st_size == 0:
        errs.append("C8: `docs/pipeline/skeleton-url.txt` absent — le squelette vivant n'a pas été "
                    "publié ; les choix visuels ont été arbitrés à l'aveugle")
    elif not re.search(r'https?://\S+', _txt(sk)):
        errs.append("C8: `skeleton-url.txt` ne contient pas d'URL — mets l'adresse de l'artifact")

    return errs
