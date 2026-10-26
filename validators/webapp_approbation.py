"""
Validateur webapp — PRÉ-VOL (nœud autonome).

Gate de sortie du nœud « approuver » : le kit tient-il debout, et le pré-vol
a-t-il été acté PENDANT cette run ? Ce nœud ne fait relire personne — il contrôle
sur pièces et corrige. Le piège reste l'acte fantôme : un fichier traîné d'un
projet précédent qui laisserait démarrer un build sur un kit jamais vérifié.

Contrats :
1. `roadmap-approved.json` présent, JSON valide, `approuve: true`.
2. Il a été écrit PENDANT cette run (plus récent que WORKSPACE.txt).
3. Il liste les jalons approuvés, et chaque jalon a son plan de cas d'usage.
4. config.json porte les décisions du pré-vol : gitRemoteUrl, pushOnEpic,
   deployment, skippedFeatures.
5. Toute fusion de jalons est motivée (un jalon non démontrable ne survit pas).
6. `status.md` déclare le pré-vol franchi (le fait, pas un numéro d'étape).
7. La feuille de route DÉRIVE du mockup : chaque jalon dit quels écrans il porte,
   chaque écran du mockup appartient à exactement un jalon, chaque story est placée
   dans un jalon ou déclarée transverse.
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
    ap = d / 'roadmap-approved.json'

    if not ap.exists() or ap.stat().st_size == 0:
        errs.append(f"C1: `{DOCS}/roadmap-approved.json` absent/vide — le pré-vol n'a pas été "
                    "acté ; le build ne démarre pas sur un kit non vérifié")
        return errs

    try:
        j = json.loads(_txt(ap))
    except json.JSONDecodeError as e:
        errs.append(f"C1: `roadmap-approved.json` JSON invalide: {e}")
        return errs

    if j.get('approuve') is not True and j.get('approved') is not True:
        errs.append("C1: `roadmap-approved.json` sans `approuve: true` — le pré-vol n'est pas acté")

    wsf = ws / 'WORKSPACE.txt'
    if wsf.exists() and ap.stat().st_mtime < wsf.stat().st_mtime:
        errs.append("C2: `roadmap-approved.json` est plus ancien que `WORKSPACE.txt` — acte hérité "
                    "d'un projet précédent, pas le pré-vol de cette feuille de route")

    jalons = j.get('milestones') or j.get('jalons') or []
    if not jalons:
        errs.append("C3: aucun jalon approuvé listé — on ne saurait pas quoi construire")
    nums = []
    for m in jalons:
        if isinstance(m, dict):
            v = m.get('n') or m.get('id') or m.get('numero')
        else:
            v = m
        mm = re.search(r'\d+', str(v or ''))
        if mm:
            nums.append(int(mm.group()))
    manquants = [n for n in nums
                 if not (ws / 'tests' / 'e2e' / 'use-cases' / f'm{n}-use-case.md').exists()]
    if manquants:
        errs.append("C3: jalon(s) approuvé(s) sans plan de cas d'usage : " +
                    ', '.join(f'm{n}' for n in manquants) +
                    " — un jalon dont personne ne sait comment le vérifier ne passe pas le pré-vol")

    cfg = d / 'config.json'
    if not cfg.exists():
        errs.append("C4: `config.json` absent — décisions d'infrastructure non enregistrées")
    else:
        try:
            c = json.loads(_txt(cfg))
            for k in ('gitRemoteUrl', 'pushOnEpic', 'deployment', 'skippedFeatures'):
                if k not in c:
                    errs.append(f"C4: `config.json` sans `{k}` — décision de pré-vol non tranchée")
        except json.JSONDecodeError as e:
            errs.append(f"C4: `config.json` JSON invalide: {e}")

    fusions = j.get('fusions') or j.get('merges') or []
    for f in fusions:
        motif = (f.get('raison') or f.get('reason') or '') if isinstance(f, dict) else ''
        if not str(motif).strip():
            errs.append("C5: une fusion de jalons est déclarée sans motif — dis ce qui a été "
                        "fusionné et pourquoi, sinon la feuille de route ment sur son découpage")
            break

    stt = d / 'status.md'
    # On juge le FAIT (le pré-vol est acté), jamais un numéro d'étape : le découpage
    # des nœuds peut changer, ce que la run a réellement franchi ne change pas.
    if stt.exists() and not re.search(r'(pr[ée].?vol|complete|termin|franchi)', _txt(stt), re.I):
        errs.append("C6: `status.md` ne déclare pas le pré-vol franchi — l'état de la run est en "
                    "retard sur la réalité")

    # --- C7 : la roadmap derive-t-elle du mockup ? ---
    # Le mockup est ce que l'utilisateur a valide, ecran par ecran. Une feuille de route qui
    # ne nomme pas ses ecrans est un decoupage PARALLELE : on ne peut plus dire ce qu'un jalon
    # doit satisfaire pour etre fini, ni voir qu'une story est tombee entre deux jalons.
    ecrans_def = d / 'design' / 'screens.json'
    stories_f = d / 'stories.json'
    if ecrans_def.exists() and jalons:
        try:
            sc = json.loads(_txt(ecrans_def))
            tous = {e['id'] for e in (sc['screens'] if isinstance(sc, dict) else sc)}
        except (json.JSONDecodeError, KeyError, TypeError):
            tous = set()

        possedes = []
        for m in jalons:
            if isinstance(m, dict):
                for e in (m.get('ecrans') or m.get('screens') or []):
                    possedes.append(e.get('id') if isinstance(e, dict) else e)

        if not possedes:
            errs.append("C7: aucun jalon ne dit quels écrans du mockup il porte — la feuille de "
                        "route est un découpage parallèle au mockup, pas sa lecture ; ajoute "
                        "`ecrans` à chaque jalon")
        elif tous:
            deux = sorted({e for e in possedes if possedes.count(e) > 1})
            orphelins = sorted(tous - set(possedes), key=lambda x: (len(x), x))
            if deux:
                errs.append("C7: écran(s) revendiqué(s) par deux jalons : " + ', '.join(deux) +
                            " — un écran se construit une fois ; l'autre jalon le liste en "
                            "`ecrans_traverses`")
            if orphelins:
                errs.append("C7: écran(s) du mockup dans aucun jalon : " + ', '.join(orphelins) +
                            " — validé avec l'utilisateur puis jamais construit")

    if stories_f.exists() and jalons:
        try:
            toutes = {x['id'] for x in json.loads(_txt(stories_f))}
        except (json.JSONDecodeError, KeyError, TypeError):
            toutes = set()
        placees = set()
        for m in jalons:
            if isinstance(m, dict):
                placees |= set(m.get('stories') or [])
        tr = j.get('stories_transverses') or {}
        placees |= set(tr.get('ids') or tr if isinstance(tr, list) else tr.get('ids') or [])
        perdues = sorted(toutes - placees)
        if toutes and not placees:
            errs.append("C7: aucun jalon ne liste ses histoires — impossible de dire ce qu'un "
                        "jalon doit satisfaire pour être fini")
        elif perdues:
            errs.append(f"C7: {len(perdues)} histoire(s) dans aucun jalon : " +
                        ', '.join(perdues[:8]) + ('…' if len(perdues) > 8 else '') +
                        " — place-les avec leur écran, ou déclare-les transverses")

    return errs
