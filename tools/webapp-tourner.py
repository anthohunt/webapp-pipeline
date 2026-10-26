#!/usr/bin/env python3
"""Tournage automatique, sans humain, de la vidéo de démonstration d'une app web livrée par la pipeline `webapp`.

    python3 webapp-tourner.py <ws> [--tour N] [--sequences s1,s3] [--slug NOM] [--sans-publier] [--modele opus] [--compte ID]

Contrat : docs/2026-10-24-webapp-3-etapes-contrat.md (étape 2 : video/, video/video-url.txt, video/versions.json ;
étape 3 : mode retours, refilmer seulement les séquences touchées, figer V<N+1>).

OPTIONNEL : la vidéo exige un outil de tournage externe, non fourni par ce dépôt (mod « tournage » : TOURNAGE_MOD_HOME,
et ses scripts de tournage : TOURNAGE_SKILL_HOME ; voir le README). Sans eux, ce script s'arrête avec un message clair.

Ce qu'il fait, avec les outils de tournage :
1. lit docs/pipeline/parcours-utilisateur.json, les user stories, design/screens.json, docs/pipeline/app-url.txt ;
2. une séquence « · filmée » par parcours (P1 → s1, P2 → s2…). Pour chaque séquence à tourner, un agent `claude -p`
   écrit le texte (narrateur à la 3e personne) et les gestes, en relevant les cibles sur l'app en ligne et en répétant
   jusqu'à ce que chaque geste trouve sa cible. Un agent plutôt qu'un gabarit : un geste du parcours (« choisit son
   rayon ») ne se traduit en cible réelle qu'en regardant l'app, et le texte doit dire ce que l'écran montre
   vraiment ; un gabarit écrirait des cibles devinées et un texte creux ;
3. fusionne les fragments en un projet du mod (video/video.texte.md + video/video.yaml), génère la voix (Henri),
   rejoue une répétition de contrôle (sinon l'agent corrige, deux fois au plus), filme chaque séquence sans écran,
   contrôle le clip (durée, son, image non blanche), assemble video/video.mp4, fige la version (montage.py --figer),
   publie la table de montage (montage.py --publier --avec-code), écrit video/video-url.txt et video/versions.json ;
4. tour N > 0 : seulement les séquences de --sequences, ou à défaut celles dont un parcours traverse un écran ou une
   histoire de docs/pipeline/retours/tour-N.json ; fige V<N+1>.

Sortie : une ligne JSON sur stdout ({"ok", "version", "url", "sequences", "refilmees", "duree_s", …}) ; code ≠ 0 et
{"ok": false, "erreur": …} en cas d'échec. Idempotent et reprenable : une séquence déjà filmée pour ce tour n'est pas
refilmée, une version déjà figée n'est pas refigée ; un second lancement pendant le premier est refusé.
Le journal détaillé va sur stderr et dans video/.tournage/auto/journal.log.
"""
import argparse, datetime, fcntl, glob, hashlib, io, json, os, re, shutil, statistics, subprocess, sys, threading, time, unicodedata, uuid
import urllib.parse, urllib.request

import yaml

MOD = os.environ.get("TOURNAGE_MOD_HOME", "")       # outil de tournage externe (outils/etat.py, outils/montage.py)
SKILL = os.environ.get("TOURNAGE_SKILL_HOME", "")   # ses scripts de tournage (scripts/tournage.mjs, profils/)
TOURNAGE = os.path.join(SKILL, "scripts", "tournage.mjs")
PROFILS = os.path.join(SKILL, "profils")
ICI = os.path.dirname(os.path.abspath(__file__))
SONDE = os.path.join(ICI, "webapp-sonde.mjs")
CONSIGNE = os.path.join(ICI, "webapp-tourner-consigne.md")
DEPOT = os.path.dirname(ICI)
FLUX = os.environ.get("FLUX_HOME") or os.path.join(DEPOT, "vendor", "flux")
TAILLE = [1600, 900]
ZOOM = 1.5        # l'app filmée plus grande dans le cadre (une app étroite ne flotte plus au centre) ; même valeur que webapp-sonde.mjs
BANDEAU = 130     # px de bande noire sous l'image pour les sous-titres, qui ne masquent plus l'app
VOIX = "fr-FR-HenriNeural"
REPARATIONS = 2          # répétitions de contrôle ratées rendues à l'agent avant d'abandonner
AGENT_TIMEOUT = 45 * 60  # s
PARALLELE = 2            # agents d'écriture en même temps (leurs navigateurs partagent le CPU)
# Compte Claude des agents d'écriture : un id de moteurs.json (WEBAPP_MOTEUR, sinon « run » = le moteur de la run,
# state/moteur → moteurs.json). Explicite, jamais hérité de l'environnement du parent. --compte le change.
COMPTE_AGENTS = os.environ.get("WEBAPP_MOTEUR") or "run"


class Echec(Exception):
    pass


# ───────────────────────── journal ─────────────────────────
JOURNAL = None
verrou_log = threading.Lock()


def log(msg):
    ligne = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
    with verrou_log:
        print(ligne, file=sys.stderr, flush=True)
        if JOURNAL:
            with io.open(JOURNAL, "a", encoding="utf-8") as f: f.write(ligne + "\n")


def lire_json(p, defaut=None):
    try: return json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError): return defaut


def ecrire_json(p, x):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(json.dumps(x, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, p)


def maintenant():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if c.isalnum())


def lancer(cmd, cwd=None, env=None, timeout=None, lourd_nom=None):
    """Lance une commande ; préfixée par WEBAPP_LIMITEUR (limiteur de CPU facultatif, ex. « nice -n 10 ») si lourd_nom
    est donné et que le réglage existe. « {nom} » dans le réglage est remplacé par lourd_nom."""
    limiteur = os.environ.get("WEBAPP_LIMITEUR", "").strip()
    if lourd_nom and limiteur:
        cmd = [x.replace("{nom}", lourd_nom) for x in limiteur.split()] + cmd
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or ""), (r.stderr or "")


# ───────────────────────── entrées du workspace ─────────────────────────
def premier(ws, *rels):
    for r in rels:
        p = os.path.join(ws, r)
        if os.path.isfile(p): return p
    return None


def liste_de(x, cle):
    if isinstance(x, dict): x = x.get(cle) or []
    return x if isinstance(x, list) else []


def charger_entrees(ws):
    f_parcours = premier(ws, "docs/pipeline/parcours-utilisateur.json")
    if not f_parcours: raise Echec("docs/pipeline/parcours-utilisateur.json absent : le parcours utilisateur est écrit à l'étape 1")
    parcours = liste_de(lire_json(f_parcours, {}), "parcours")
    if not parcours: raise Echec("parcours-utilisateur.json ne contient aucun parcours")
    for p in parcours:
        if not p.get("id") or not p.get("etapes"): raise Echec(f"parcours mal formé (id et etapes obligatoires) : {json.dumps(p, ensure_ascii=False)[:200]}")
    f_url = premier(ws, "docs/pipeline/app-url.txt")
    if not f_url: raise Echec("docs/pipeline/app-url.txt absent : l'app n'est pas encore en ligne")
    app_url = io.open(f_url, encoding="utf-8").read().strip().split()[0]
    if not re.match(r"https?://", app_url): raise Echec(f"app-url.txt ne contient pas une URL : {app_url!r}")
    histoires = {}
    for rel in ("docs/pipeline/stories.json", "design/stories-v1.json", "docs/pipeline/design/stories-v1.json"):
        p = premier(ws, rel)
        if p:
            for s in liste_de(lire_json(p, []), "stories"):
                if isinstance(s, dict) and s.get("id"): histoires[s["id"]] = s  # les fichiers suivants (v1) l'emportent
    ecrans = {}
    p = premier(ws, "design/screens.json", "docs/pipeline/design/screens.json")
    if p:
        for e in liste_de(lire_json(p, {}), "screens"):
            if isinstance(e, dict) and e.get("id"): ecrans[e["id"]] = e
    return parcours, app_url, histoires, ecrans


def nom_app(ws, app_url):
    """Nom lisible de l'app (titre de la vidéo) : le <title> de l'app en ligne, sinon concept.md, sinon le nom d'hôte."""
    try:
        with urllib.request.urlopen(urllib.request.Request(app_url, headers={"User-Agent": "webapp-tourner"}), timeout=20) as r:
            m = re.search(r"<title[^>]*>([^<]{2,80})</title>", r.read(200000).decode("utf-8", "replace"), re.I)
            if m: return re.sub(r"\s+", " ", __import__("html").unescape(m.group(1))).strip()
    except Exception:
        pass
    for rel in ("docs/pipeline/concept.md", "docs/pipeline/cahier-des-charges.md"):
        p = premier(ws, rel)
        if p:
            m = re.match(r"#\s*(?:Concept|Cahier des charges)?\s*[—:-]?\s*(.+)", io.open(p, encoding="utf-8").readline())
            if m and m.group(1).strip(): return m.group(1).strip()
    return urllib.parse.urlparse(app_url).hostname.split(".")[0].replace("-", " ").capitalize()


def slug_de(ws, app_url, video, force=None):
    s = force or (lire_json(os.path.join(video, ".tournage", "en-ligne.json"), {}) or {}).get("slug")
    if not s:
        y = os.path.join(video, "video.yaml")
        if os.path.isfile(y): s = (yaml.safe_load(io.open(y, encoding="utf-8")) or {}).get("slug")
    if not s:
        w = os.path.join(ws, "WORKSPACE.txt")
        m = re.search(r"^projet:\s*(\S+)", io.open(w, encoding="utf-8").read(), re.M) if os.path.isfile(w) else None
        s = m.group(1) if m else urllib.parse.urlparse(app_url).hostname.split(".")[0]
    s = re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")[:60]
    if not s: raise Echec("impossible de déduire le nom en ligne de la démo : passe --slug")
    return s


# ───────────────────────── séquences ─────────────────────────
def carte_sequences(auto, parcours):
    """P1 → s1… ; la correspondance est gardée d'un tour à l'autre (un parcours ajouté prend le numéro suivant)."""
    f = os.path.join(auto, "sequences.json")
    carte = lire_json(f, {}) or {}
    for p in parcours:
        if p["id"] not in carte:
            n = max([int(v[1:]) for v in carte.values()] + [0]) + 1
            carte[p["id"]] = f"s{n}"
    ecrire_json(f, carte)
    par_id = {p["id"]: p for p in parcours}
    return [(carte[p["id"]], par_id[p["id"]]) for p in parcours]


def sequences_touchees(ws, tour, seqs):
    """Séquences dont un parcours traverse un écran ou une histoire d'un retour du tour ; un retour sans écran ni
    histoire (remarque générale) touche toutes les séquences."""
    f = os.path.join(ws, "docs", "pipeline", "retours", f"tour-{tour}.json")
    r = lire_json(f)
    if r is None: raise Echec(f"tour {tour} : {os.path.relpath(f, ws)} absent ou illisible, et --sequences non donné")
    retours = r.get("retours") or []
    touchees, raisons = set(), []
    for x in retours:
        ec, hi = x.get("ecran"), x.get("histoire")
        if not ec and not hi:
            raisons.append(f"{x.get('id')} : remarque générale → toutes les séquences")
            return [s for s, _ in seqs], raisons
        for s, p in seqs:
            for e in p.get("etapes") or []:
                if (ec and e.get("ecran") == ec) or (hi and hi in (e.get("stories") or [])):
                    touchees.add(s); raisons.append(f"{x.get('id')} → {s} ({p['id']}, étape {e.get('n')})"); break
    return [s for s, _ in seqs if s in touchees], raisons


# ───────────────────────── environnement des outils ─────────────────────────
def chromium():
    if os.environ.get("TOURNAGE_CHROMIUM"): return os.environ["TOURNAGE_CHROMIUM"]
    base = os.path.expanduser("~/.cache/ms-playwright")
    for d in sorted(glob.glob(os.path.join(base, "chromium-*")), key=lambda d: -int(d.rsplit("-", 1)[1]) if d.rsplit("-", 1)[1].isdigit() else 0):
        f = os.path.join(d, "chrome-linux64", "chrome")
        if os.path.isfile(f): return f
    raise Echec("Chromium de Playwright introuvable dans ~/.cache/ms-playwright")


def preparer_outils(auto):
    """Dépendances des scripts de tournage (node_modules, ignoré par git) et une commande `python` : tournage.mjs lance
    `python` (nom Windows), absent des serveurs où seul python3 existe. Le raccourci vit dans le dossier de la run."""
    if not MOD or not SKILL or not os.path.isfile(TOURNAGE):
        raise Echec("outil de tournage absent : la vidéo est optionnelle et exige TOURNAGE_MOD_HOME et "
                    "TOURNAGE_SKILL_HOME (voir le README)")
    if not os.path.isdir(os.path.join(SKILL, "node_modules", "playwright-core")):
        log("installation des dépendances node du skill tournage-demo")
        c, o, e = lancer(["npm", "install", "--no-audit", "--no-fund"], cwd=SKILL, timeout=600)
        if c: raise Echec(f"npm install dans {SKILL} : {e.strip()[-300:]}")
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise Echec("module Python edge_tts absent : pip install --user --break-system-packages edge-tts pyyaml")
    shim = os.path.join(auto, "bin")
    os.makedirs(shim, exist_ok=True)
    py = os.path.join(shim, "python")
    if not os.path.exists(py): os.symlink(sys.executable or "/usr/bin/python3", py)
    env = dict(os.environ)
    env["PATH"] = shim + os.pathsep + env.get("PATH", "")
    env["TOURNAGE_CHROMIUM"] = chromium()
    env.pop("TOURNAGE_URL", None)
    return env, shim


def env_moteur(ws, compte=COMPTE_AGENTS):
    """Le compte Claude des agents (moteurs.json) : dossier de config posé, jeton sourcé, comme run-node.py.
    compte = id d'un moteur de moteurs.json, ou « run » pour celui de la run (state/moteur)."""
    cfg = lire_json(os.path.join(FLUX, "moteurs.json"), {}) or {}
    table = {m["id"]: m for m in cfg.get("moteurs") or [] if m.get("id")}
    choix = compte
    if compte == "run":
        try: choix = io.open(os.path.join(ws, "state", "moteur"), encoding="utf-8").read().strip() or cfg.get("defaut")
        except OSError: choix = cfg.get("defaut")
    m = table.get(choix)
    if not m: raise Echec(f"compte des agents inconnu : {choix!r} (moteurs.json : {sorted(table)})")
    if not m.get("config_dir"): raise Echec(f"moteur {choix} sans config_dir dans moteurs.json")
    # rien du compte du parent ne doit passer : on efface ses identifiants avant de poser ceux du moteur
    env = {k: None for k in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    env["CLAUDE_CONFIG_DIR"] = m["config_dir"]
    if m.get("fichier_jeton"):
        if not os.path.isfile(m["fichier_jeton"]): raise Echec(f"jeton du moteur {choix} absent : {m['fichier_jeton']}")
        for l in io.open(m["fichier_jeton"], encoding="utf-8"):
            k, _, v = l.strip().removeprefix("export ").partition("=")
            if k and not k.startswith("#") and v: env[k.strip()] = v.strip().strip('"').strip("'")
    return env, m["id"]


# ───────────────────────── l'agent d'écriture ─────────────────────────
def remplir(gabarit, valeurs):
    return re.sub(r"\{([A-Z_]+)\}", lambda m: str(valeurs[m.group(1)]) if m.group(1) in valeurs else m.group(0), gabarit)


def amorce_fragment(frag, seq, slug, app_url, parcours):
    if os.path.isfile(frag): return
    d = {"titre": parcours.get("titre") or seq, "url": app_url, "profil": f"webapp-{slug}-{seq}", "taille": TAILLE, "zoom": ZOOM, "bandeau_sous_titres": BANDEAU,
         "voix": VOIX, "debit": "+0%", "sequences": {seq: parcours.get("titre") or seq},
         "ecrans": {seq: {"titre": parcours.get("titre") or seq, "support": "web"}}, "etapes": []}
    io.open(frag, "w", encoding="utf-8").write(yaml.safe_dump(d, allow_unicode=True, sort_keys=False, width=200))


def texte_histoires(p, histoires):
    ids = list(dict.fromkeys(h for e in p.get("etapes") or [] for h in e.get("stories") or []))
    out = []
    for i in ids:
        h = histoires.get(i)
        if not h: out.append(f"• {i} (introuvable dans les user stories)"); continue
        crit = h.get("acceptance_criteria") or []
        out.append(f"• {i} · {h.get('title', '')} — {h.get('story', '')}" + (f"\n  détail : {h['detail']}" if h.get("detail") else "")
                   + "".join(f"\n  critère : {c}" for c in crit[:3]))
    return "\n".join(out) or "(aucune)"


def texte_ecrans(p, ecrans):
    ids = list(dict.fromkeys(e.get("ecran") for e in p.get("etapes") or [] if e.get("ecran")))
    out = []
    for i in ids:
        e = ecrans.get(i) or {}
        out.append(f"• {i} · {e.get('name', '?')} — {e.get('view', '')}" + (f" ; éléments : {e['interactive_elements']}" if e.get("interactive_elements") else ""))
    return "\n".join(out) or "(aucun)"


def consigne(seq, p, ctx, tour, retours_txt):
    v = {"SEQ": seq, "SEQ_MAJ": seq.upper(), "APP": ctx["app"], "APP_URL": ctx["app_url"], "SLUG": ctx["slug"],
         "PARCOURS": json.dumps(p, ensure_ascii=False, indent=1), "HISTOIRES": texte_histoires(p, ctx["histoires"]),
         "ECRANS": texte_ecrans(p, ctx["ecrans"]), "RETOURS": retours_txt, "FRAG": os.path.join(ctx["auto"], seq, f"{seq}.yaml"),
         "DIR": os.path.join(ctx["auto"], seq), "SHIM": ctx["shim"], "CHROME": ctx["env"]["TOURNAGE_CHROMIUM"],
         "SONDE": SONDE, "TOURNAGE": TOURNAGE, "PROFIL_DIR": os.path.join(PROFILS, f"webapp-{ctx['slug']}-{seq}"), "TOUR": tour}
    return remplir(io.open(CONSIGNE, encoding="utf-8").read(), v)


def retours_pour(ws, tour, seq, p, frag_prec):
    """Mode retours : le texte du fragment précédent et les retours qui touchent ce parcours."""
    if tour == 0: return ""
    r = lire_json(os.path.join(ws, "docs", "pipeline", "retours", f"tour-{tour}.json"), {}) or {}
    ecr = {e.get("ecran") for e in p.get("etapes") or []}
    his = {h for e in p.get("etapes") or [] for h in e.get("stories") or []}
    lignes = [f"• {x.get('id')} : « {x.get('dit')} » (écran {x.get('ecran')}, histoire {x.get('histoire')}) — attendu : {x.get('attendu')}"
              for x in r.get("retours") or [] if (not x.get("ecran") and not x.get("histoire")) or x.get("ecran") in ecr or x.get("histoire") in his]
    prec = io.open(frag_prec, encoding="utf-8").read() if frag_prec and os.path.isfile(frag_prec) else "(introuvable)"
    return (f"\n## Tour de retours {tour} : la séquence est à refaire\n"
            f"Cette séquence a déjà été tournée (version précédente). Le client a fait des retours ; l'app a été corrigée et "
            f"redéployée. Retours qui touchent ce parcours :\n" + ("\n".join(lignes) or "• (aucun retour ne nomme ce parcours : refilmé à la demande)") +
            f"\n\nReprends le fragment précédent ci-dessous (déjà recopié dans le fichier à livrer). Ne change le texte que là où l'app a "
            f"changé ou là où un retour l'exige ; relève de nouveau les cibles des écrans touchés ; puis répète comme d'habitude.\n"
            f"```yaml\n{prec}\n```\n")


def lancer_agent(seq, prompt, ctx, reprise=None):
    d = os.path.join(ctx["auto"], seq)
    sid = reprise or str(uuid.uuid4())
    env = {**ctx["env"], **ctx["env_moteur"]}
    env = {k: v for k, v in env.items() if v is not None}
    cmd = ["claude", "-p", prompt, "--model", ctx["modele"], "--output-format", "json", "--dangerously-skip-permissions"]
    cmd += ["--resume", sid] if reprise else ["--session-id", sid]
    n = len(glob.glob(os.path.join(d, "agent-*.json"))) + 1
    log(f"{seq} : agent d'écriture lancé (compte {ctx['moteur']}, session {sid}{', reprise' if reprise else ''})")
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=d, env=env, capture_output=True, text=True, timeout=AGENT_TIMEOUT)
        sortie, code = r.stdout, r.returncode
    except subprocess.TimeoutExpired as e:
        sortie, code = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), -9
    io.open(os.path.join(d, f"agent-{n}.json"), "w", encoding="utf-8").write(sortie or "")
    res = (lire_json(os.path.join(d, f"agent-{n}.json"), {}) or {})
    log(f"{seq} : agent fini en {time.time() - t:.0f} s (code {code}) : {str(res.get('result', ''))[:300]}")
    return sid


def verifier_fragment(seq, frag, app_url, tour):
    """Ce que l'agent livre, vérifié sans le croire : forme, ids, ponctuation du dit, mot de chaque geste, fait.json."""
    d = os.path.dirname(frag)
    fait = lire_json(os.path.join(d, "fait.json"))
    if not fait: return "fait.json absent : l'agent n'a pas fini"
    if fait.get("tour") != tour: return f"fait.json est celui du tour {fait.get('tour')}, pas du tour {tour}"
    if not fait.get("ok"): raise Echec(f"{seq} bloquée par un défaut de l'app : {fait.get('bloque')}")
    try: y = yaml.safe_load(io.open(frag, encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e: return f"fragment illisible : {e}"
    et = y.get("etapes") or []
    if not et: return "aucun plan dans le fragment"
    if urllib.parse.urlparse(str(y.get("url", ""))).netloc != urllib.parse.urlparse(app_url).netloc:
        return f"url de départ hors de l'app : {y.get('url')}"
    for k, e in enumerate(et, 1):
        if e.get("id") != f"{seq}-{k}": return f"plan {k} : id {e.get('id')} au lieu de {seq}-{k}"
        dit = str(e.get("dit") or "")
        if not dit.strip(): return f"{e.get('id')} : dit vide"
        if ":" in dit: return f"{e.get('id')} : deux-points dans le dit (règle du mod)"
        mots = [norm(m) for m in re.split(r"[\s'’\-]+", dit)]
        for g in e.get("gestes") or []:
            if g.get("sur") is not None:
                c = norm(str(g["sur"]).split()[0])
                if not any(m == c or m.startswith(c) or c in m for m in mots if m): return f"{e.get('id')} : le mot « {g['sur']} » n'est pas dans le dit"
    return None


# ───────────────────────── le projet du mod (video/) ─────────────────────────
def fusionner(video, auto, seqs, ctx):
    """video/video.yaml + video/video.texte.md, depuis les fragments de toutes les séquences (dans l'ordre des parcours)."""
    etapes, sequences, ecr, departs, md = [], {}, {}, {}, [f"# {ctx['app']} · démonstration", ""]
    for seq, p in seqs:
        frag = os.path.join(auto, seq, f"{seq}.yaml")
        if not os.path.isfile(frag): continue
        y = yaml.safe_load(io.open(frag, encoding="utf-8")) or {}
        if not y.get("etapes"): continue
        titre = str(y.get("titre") or p.get("titre") or seq).strip().rstrip(".")
        sequences[seq] = titre
        ecr[seq] = {"titre": titre, "support": "web"}
        departs[seq] = y.get("url") or ctx["app_url"]
        md += [f"## {seq.upper()} · {titre} · filmée", ""]
        for e in y["etapes"]:
            e = {k: v for k, v in e.items() if v not in (None, [], "")}
            e["plan"] = [seq]
            # le mod attend montre = {écran du plan: ce qui est lisible} ; l'agent l'écrit en une phrase
            if isinstance(e.get("montre"), str): e["montre"] = {seq: e["montre"]}
            etapes.append(e)
            if e.get("ecran"): md.append(f"🎬 {e['ecran']}")
            md += [f"> {e['dit']}", ""]
    script = {"titre": f"{ctx['app']} · démonstration", "slug": ctx["slug"], "acces": "code", "url": ctx["app_url"],
              "profil": f"webapp-{ctx['slug']}", "taille": TAILLE, "zoom": ZOOM, "bandeau_sous_titres": BANDEAU, "voix": VOIX, "debit": "+0%",
              "sequences": sequences, "ecrans": ecr, "departs": departs, "etapes": etapes}
    io.open(os.path.join(video, "video.yaml"), "w", encoding="utf-8").write(yaml.safe_dump(script, allow_unicode=True, sort_keys=False, width=200))
    io.open(os.path.join(video, "video.texte.md"), "w", encoding="utf-8").write("\n".join(md).rstrip() + "\n")
    return script


def ids_de(script, seq):
    return [e["id"] for e in script["etapes"] if e["id"].split("-")[0] == seq]


def generer_voix(video, seq, env):
    c, o, e = lancer(["node", TOURNAGE, "voix", "video.yaml", "--seq", seq], cwd=video, env=env, timeout=600)
    if c: raise Echec(f"{seq} : voix non générée : {(e or o).strip()[-400:]}")
    m = lire_json(os.path.join(video, "video.voix", seq, "mots.json"), {}) or {}
    log(f"{seq} : voix {m.get('duree', 0):.1f} s" + (f", alertes : {m.get('alertes')}" if m.get("alertes") else ""))
    return float(m.get("duree") or 0)


def jouer(mode, video, seq, script, env, slug, extra=()):
    ids = ids_de(script, seq)
    shutil.rmtree(os.path.join(PROFILS, f"webapp-{slug}"), ignore_errors=True)  # l'app s'ouvre à neuf à chaque prise
    e2 = {**env, "TOURNAGE_URL": script["departs"].get(seq) or script["url"]}
    cmd = ["node", TOURNAGE, mode, "video.yaml", "--headless", "--depuis", ids[0], "--jusqua", ids[-1], *extra]
    return lancer(cmd, cwd=video, env=e2, timeout=40 * 60, lourd_nom=f"tournage-{slug}-{seq}")


def repetition_controle(video, seq, script, env, slug):
    """Répétition sur le projet fusionné, avec la voix finale : rend None si tout passe, sinon le motif."""
    c, o, e = jouer("repetition", video, seq, script, env, slug, ("--sans-voix", "--releve"))
    rep = os.path.join(video, "video.repetition")
    j = lire_json(os.path.join(rep, "journal.json"), {}) or {}
    garde = os.path.join(video, ".tournage", "auto", seq, "controle")
    shutil.rmtree(garde, ignore_errors=True)
    if os.path.isdir(rep): shutil.copytree(rep, garde)
    if j.get("echec"): return f"le plan {j['echec']['etape']} a échoué : {j['echec']['erreur']}"
    if c: return f"répétition interrompue (code {c}) : {(e or o).strip()[-300:]}"
    lents = [x for x in j.get("journal") or [] if abs(x.get("decalage_ms") or 0) > 600]
    if lents: return "gestes en retard sur leur mot de plus de 600 ms : " + ", ".join(f"{x['etape']}/{x['geste']} {x['decalage_ms']} ms" for x in lents)
    return None


def stats_image(clip, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", clip, "-frames:v", "1", "-vf", "scale=64:36,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, timeout=120)
    px = list(r.stdout)
    return statistics.pstdev(px) if len(px) > 100 else 0.0


def duree_media(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0


def controler_clip(clip, voix_s):
    """Le clip existe, dure au moins sa voix, a du son, et ses images ne sont pas blanches (écart-type des gris)."""
    if not os.path.isfile(clip): return "clip absent"
    d = duree_media(clip)
    if d < voix_s - 0.5: return f"clip de {d:.1f} s pour {voix_s:.1f} s de voix"
    r = subprocess.run(["ffmpeg", "-i", clip, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True, timeout=300)
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
    if not m or float(m.group(1)) < -35: return f"son absent ou trop faible ({m.group(1) if m else '?'} dB)"
    plats = [t for t in (d * 0.2, d * 0.5, d * 0.8) if stats_image(clip, t) < 4]
    if plats: return "image uniforme (écran blanc ?) à " + ", ".join(f"{t:.1f} s" for t in plats)
    return None


def filmer(video, seq, script, env, slug):
    c, o, e = jouer("video", video, seq, script, env, slug)
    src = os.path.join(video, "video.video", "demo.mp4")
    if c or not os.path.isfile(src): raise Echec(f"{seq} : tournage raté (code {c}) : {(o + e).strip()[-400:]}")
    os.makedirs(os.path.join(video, "clips"), exist_ok=True)
    clip = os.path.join(video, "clips", f"{seq}.mp4")
    shutil.copy2(src, clip)
    if os.path.isfile(os.path.join(video, "video.video", "demo.srt")):
        shutil.copy2(os.path.join(video, "video.video", "demo.srt"), os.path.join(video, "clips", f"{seq}.srt"))
    return clip


def etat_mod(video, *args):
    c, o, e = lancer([sys.executable, os.path.join(MOD, "outils", "etat.py"), video, *args], timeout=120)
    if c: raise Echec(f"etat.py {' '.join(args)} : {(e or o).strip()[-300:]}")


def assembler(video, seqs):
    clips = [os.path.join(video, "clips", f"{s}.mp4") for s, _ in seqs if os.path.isfile(os.path.join(video, "clips", f"{s}.mp4"))]
    liste = os.path.join(video, ".tournage", "auto", "assemblage.txt")
    io.open(liste, "w", encoding="utf-8").write("".join(f"file '{c}'\n" for c in clips))
    sortie = os.path.join(video, "video.mp4")
    c, o, e = lancer(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", liste, "-c", "copy",
                      "-movflags", "+faststart", sortie], timeout=1800, lourd_nom="tournage-assemblage")
    if c: raise Echec(f"assemblage : {e.strip()[-300:]}")
    return sortie, clips


def figer(video, nom_v):
    vs = lire_json(os.path.join(video, ".tournage", "versions.json"), []) or []
    if any(x.get("nom") == nom_v for x in vs):
        log(f"version {nom_v} déjà figée"); return
    c, o, e = lancer([sys.executable, os.path.join(MOD, "outils", "montage.py"), video, "--figer", nom_v], timeout=600)
    if c: raise Echec(f"montage.py --figer : {(e or o).strip()[-300:]}")
    log(o.strip())


def publier(video):
    c, o, e = lancer([sys.executable, os.path.join(MOD, "outils", "montage.py"), video, "--publier", "--avec-code", "--sans-ouvrir"], timeout=3600)
    if c: raise Echec(f"montage.py --publier : {(e or o).strip()[-400:]}")
    el = lire_json(os.path.join(video, ".tournage", "en-ligne.json"), {}) or {}
    url = el.get("url")
    if not url: raise Echec("publication sans lien (.tournage/en-ligne.json)")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "webapp-tourner"}), timeout=60) as r: code = r.status
    except Exception as x:
        raise Echec(f"le lien publié ne répond pas : {url} ({x})")
    if code != 200: raise Echec(f"le lien publié répond {code} : {url}")
    log(f"publié : {url} (HTTP {code})")
    return url


# ───────────────────────── une séquence, de l'écriture au clip ─────────────────────────
def ecrire_sequence(seq, p, ctx, tour):
    """L'agent écrit et répète la séquence (sauf si c'est déjà fait pour ce tour)."""
    d = os.path.join(ctx["auto"], seq)
    os.makedirs(d, exist_ok=True)
    frag = os.path.join(d, f"{seq}.yaml")
    fait = lire_json(os.path.join(d, "fait.json"), {}) or {}
    if fait.get("tour") == tour and fait.get("ok") and not verifier_fragment(seq, frag, ctx["app_url"], tour):
        log(f"{seq} : scénario du tour {tour} déjà écrit"); return
    prec = None
    if tour > 0 and os.path.isfile(frag):
        prec = os.path.join(d, f"{seq}.tour-{fait.get('tour', tour - 1)}.yaml")
        if not os.path.isfile(prec): shutil.copy2(frag, prec)
    amorce_fragment(frag, seq, ctx["slug"], ctx["app_url"], p)
    sid = lancer_agent(seq, consigne(seq, p, ctx, tour, retours_pour(ctx["ws"], tour, seq, p, prec)), ctx)
    ctx["sessions"][seq] = sid
    motif = verifier_fragment(seq, frag, ctx["app_url"], tour)
    if motif:
        log(f"{seq} : livraison incomplète ({motif}), l'agent reprend")
        lancer_agent(seq, f"Ta livraison n'est pas recevable : {motif}. Corrige {frag}, répète, puis réécris fait.json (tour {tour}).", ctx, reprise=sid)
        motif = verifier_fragment(seq, frag, ctx["app_url"], tour)
        if motif: raise Echec(f"{seq} : fragment non recevable après reprise : {motif}")


def tourner_sequence(seq, p, ctx, tour):
    """Voix, répétition de contrôle (réparée par l'agent au besoin), tournage, contrôle du clip."""
    video, env, slug = ctx["video"], ctx["env"], ctx["slug"]
    for essai in range(REPARATIONS + 1):
        script = fusionner(video, ctx["auto"], ctx["seqs"], ctx)
        voix_s = generer_voix(video, seq, env)
        motif = repetition_controle(video, seq, script, env, slug)
        if not motif: break
        log(f"{seq} : répétition de contrôle ratée ({motif})")
        if essai == REPARATIONS: raise Echec(f"{seq} : la répétition échoue encore après {REPARATIONS} corrections : {motif}")
        frag = os.path.join(ctx["auto"], seq, f"{seq}.yaml")
        try: os.remove(os.path.join(ctx["auto"], seq, "fait.json"))
        except FileNotFoundError: pass
        lancer_agent(seq, (f"La répétition de contrôle (projet fusionné, voix finale, app neuve) a échoué : {motif}. Captures, journal et "
                           f"arbres de page dans {ctx['auto']}/{seq}/controle/. Corrige {frag}, répète jusqu'à ce que tout passe, puis "
                           f"réécris fait.json (tour {tour})."), ctx, reprise=ctx["sessions"].get(seq))
        m2 = verifier_fragment(seq, frag, ctx["app_url"], tour)
        if m2: raise Echec(f"{seq} : fragment non recevable après correction : {m2}")
    log(f"{seq} : répétition de contrôle réussie, tournage")
    t = time.time()
    clip = filmer(video, seq, script, env, slug)
    motif = controler_clip(clip, voix_s)
    if motif:
        log(f"{seq} : clip refusé ({motif}), seconde prise")
        clip = filmer(video, seq, script, env, slug)
        motif = controler_clip(clip, voix_s)
        if motif: raise Echec(f"{seq} : clip refusé deux fois : {motif}")
    log(f"{seq} : clip {duree_media(clip):.1f} s filmé en {time.time() - t:.0f} s")
    etat_mod(video, "valider", "sequence", seq, "a_valider", f"clip={clip}", "agent=webapp-tourner")
    io.open(os.path.join(ctx["auto"], seq, f"tour-{tour}.ok"), "w").write(hashlib.sha1(open(clip, "rb").read()).hexdigest())


# ───────────────────────── programme ─────────────────────────
def principal(a):
    global JOURNAL
    debut = time.time()
    ws = os.path.abspath(a.ws)
    if not os.path.isdir(ws): raise Echec(f"workspace introuvable : {ws}")
    video = os.path.join(ws, "video")
    auto = os.path.join(video, ".tournage", "auto")
    os.makedirs(auto, exist_ok=True)
    JOURNAL = os.path.join(auto, "journal.log")
    verrou = open(os.path.join(auto, "verrou"), "w")
    try: fcntl.flock(verrou, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise Echec("un tournage tourne déjà sur ce workspace (video/.tournage/auto/verrou)")

    parcours, app_url, histoires, ecrans = charger_entrees(ws)
    seqs = carte_sequences(auto, parcours)
    toutes = [s for s, _ in seqs]
    tour = a.tour or 0
    nom_v = f"V{tour + 1}"
    log(f"tournage {ws} · tour {tour} · {len(seqs)} séquences ({', '.join(f'{s}={p['id']}' for s, p in seqs)})")

    # Déjà fait pour ce tour : la version est figée et publiée → on rend le résultat sans rien refaire.
    versions = lire_json(os.path.join(video, "versions.json"), {"versions": []}) or {"versions": []}
    deja = next((v for v in versions["versions"] if v.get("version") == nom_v), None)
    url_txt = os.path.join(video, "video-url.txt")
    if deja and os.path.isfile(url_txt) and not a.sans_publier:
        return {"ok": True, "deja_fait": True, "tour": tour, "version": nom_v, "url": io.open(url_txt).read().strip(),
                "sequences": deja.get("sequences"), "refilmees": deja.get("refilmees"), "duree_s": round(duree_media(os.path.join(video, "video.mp4")), 1)}

    if a.sequences:
        cibles = [s.strip().lower() for s in a.sequences.split(",") if s.strip()]
        inconnues = [s for s in cibles if s not in toutes]
        if inconnues: raise Echec(f"séquences inconnues : {inconnues} (connues : {toutes})")
        raisons = ["--sequences"]
    elif tour == 0:
        cibles, raisons = toutes, ["tour 0 : tout"]
    else:
        cibles, raisons = sequences_touchees(ws, tour, seqs)
    # une séquence jamais filmée (parcours ajouté) l'est d'office
    cibles = [s for s in toutes if s in cibles or not os.path.isfile(os.path.join(video, "clips", f"{s}.mp4"))]
    if not cibles: raise Echec(f"tour {tour} : aucun retour ne touche une séquence ({'; '.join(raisons)}) ; passe --sequences")
    log(f"à tourner : {cibles} ({'; '.join(raisons)})")

    env, shim = preparer_outils(auto)
    env_m, moteur = env_moteur(ws, a.compte)
    slug = slug_de(ws, app_url, video, a.slug)
    ctx = {"ws": ws, "video": video, "auto": auto, "app_url": app_url, "app": nom_app(ws, app_url), "slug": slug, "seqs": seqs,
           "histoires": histoires, "ecrans": ecrans, "env": env, "shim": shim, "env_moteur": env_m, "moteur": moteur,
           "modele": a.modele, "sessions": {}}
    sessions = lire_json(os.path.join(auto, "sessions.json"), {}) or {}
    ctx["sessions"].update(sessions)

    # 1. écriture : un agent par séquence à tourner, au plus PARALLELE à la fois
    a_ecrire = [(s, p) for s, p in seqs if s in cibles and not os.path.isfile(os.path.join(auto, s, f"tour-{tour}.ok"))]
    erreurs = []

    def ecrire(s, p):
        try: ecrire_sequence(s, p, ctx, tour)
        except Exception as x: erreurs.append(f"{s} : {x}")
    for i in range(0, len(a_ecrire), PARALLELE):
        fils = [threading.Thread(target=ecrire, args=sp) for sp in a_ecrire[i:i + PARALLELE]]
        for f in fils: f.start()
        for f in fils: f.join()
    ecrire_json(os.path.join(auto, "sessions.json"), ctx["sessions"])
    if erreurs: raise Echec(" ; ".join(erreurs))

    # 2. voix, contrôle, tournage : une séquence après l'autre (un seul navigateur filmé à la fois)
    for s, p in seqs:
        if s not in cibles: continue
        if os.path.isfile(os.path.join(auto, s, f"tour-{tour}.ok")) and os.path.isfile(os.path.join(video, "clips", f"{s}.mp4")):
            log(f"{s} : déjà filmée pour le tour {tour}"); continue
        tourner_sequence(s, p, ctx, tour)
    ecrire_json(os.path.join(auto, "sessions.json"), ctx["sessions"])

    # 3. assemblage, version, mise en ligne
    fusionner(video, auto, seqs, ctx)
    manquants = [s for s in toutes if not os.path.isfile(os.path.join(video, "clips", f"{s}.mp4"))]
    if manquants: raise Echec(f"clips manquants : {manquants}")
    sortie, clips = assembler(video, seqs)
    etat_mod(video, "valider", "final", "a_valider", f"video={sortie}")
    figer(video, nom_v)
    url = None
    if not a.sans_publier:
        url = publier(video)
        io.open(url_txt, "w", encoding="utf-8").write(url + "\n")
    if not deja:
        versions["versions"].append({"version": nom_v, "tour": tour, "date": maintenant(), "sequences": toutes, "refilmees": cibles})
        ecrire_json(os.path.join(video, "versions.json"), versions)
    duree = duree_media(sortie)
    log(f"fini : {nom_v}, {duree:.1f} s, en {time.time() - debut:.0f} s")
    return {"ok": True, "tour": tour, "version": nom_v, "url": url, "sequences": toutes, "refilmees": cibles,
            "duree_s": round(duree, 1), "video": sortie, "temps_s": round(time.time() - debut)}


def main():
    ap = argparse.ArgumentParser(description="Tournage automatique de la vidéo de démonstration d'une app web (pipeline webapp).")
    ap.add_argument("ws")
    ap.add_argument("--tour", type=int, default=0)
    ap.add_argument("--sequences", help="s1,s3 : seulement ces séquences")
    ap.add_argument("--slug", help="nom de la démo en ligne (sinon : projet de WORKSPACE.txt)")
    ap.add_argument("--sans-publier", action="store_true", help="ne pas mettre la table de montage en ligne")
    ap.add_argument("--modele", default="opus", help="modèle des agents d'écriture (défaut : opus)")
    ap.add_argument("--compte", default=COMPTE_AGENTS, help=f"moteur de moteurs.json des agents d'écriture (défaut : {COMPTE_AGENTS}) ; « run » = state/moteur de la run")
    a = ap.parse_args()
    try:
        r = principal(a)
        print(json.dumps(r, ensure_ascii=False)); sys.exit(0)
    except Echec as x:
        log(f"ÉCHEC : {x}")
        print(json.dumps({"ok": False, "erreur": str(x)}, ensure_ascii=False)); sys.exit(1)
    except Exception as x:  # imprévu : message clair, trace dans le journal
        import traceback
        log(traceback.format_exc())
        print(json.dumps({"ok": False, "erreur": f"{type(x).__name__}: {x}"}, ensure_ascii=False)); sys.exit(2)


if __name__ == "__main__":
    main()
