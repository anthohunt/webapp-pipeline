---
name: pipeline-step4.5
description: Le tournage de la vidéo de démonstration et ses versions (web app en 3 étapes) — une fois tous les jalons faits, le chef lance `tools/webapp-tourner.py` (une séquence filmée par parcours sur l'app en ligne, V1 figée, table de montage publiée avec son code), attend la fin, contrôle `video/`, puis passe l'avancement en `fini`. Sous-skill de pipeline-step4 ; le mode retours (4.3) s'en sert pour refilmer.
---

# Pipeline Step 4.5 — Tournage et versions

**Appelé par :** le chef (pipeline-step4 §1, cas 3) quand tous les jalons sont cochés et qu'aucune
vidéo n'existe pour le tour 0 ; par le mode retours (4.3 §4) pour refilmer.
**Sortie (contrat) :** `video/` (projet du mod tournage), `video/video-url.txt` (lien de la table
de montage, avec `?code=`), `video/versions.json` (`V1` au tour 0, puis une version par tour).

Le tournage est écrit sans humain : pas de validation du scénario, la revue du client (nœud
`revue`) juge la vidéo. Tu ne l'écris pas toi-même : le script s'en charge, séquence par
séquence, depuis `parcours-utilisateur.json`, les histoires et l'app en ligne.

---

## 1. Préconditions

• Tous les jalons `fait` dans `avancement.json` et cochés dans `status.md`.
• `docs/pipeline/app-url.txt` porte l'URL de production, qui répond (`curl -sI` → 2xx/3xx).
• `docs/pipeline/parcours-utilisateur.json` existe : une séquence par parcours (P1 → s1…).
Il en manque une : ce n'est pas un tournage, c'est un jalon ou une mise en production à finir —
retourne au mode jalon.

`avancement.json` : `phase: "tournage"`, `maj`.

## 2. Lancer le script — détaché, et l'attendre SANS rendre la main

**Ne rends jamais la main pendant le tournage.** Le moteur tmux prend une invite inactive pour
la fin de ta passe : il relance une passe neuve, tue ta session, et le tournage lancé depuis
elle meurt avec (constaté le 24/10 : deux passes perdues, deux séquences réécrites). Donc ni
`run_in_background` suivi d'une attente de notification, ni « j'attends la fin ».

1. Lance-le **détaché de ta session** (il survit à sa fermeture) :

```bash
W=<ws>; mkdir -p $W/video/.tournage/auto; : > $W/video/.tournage/auto/sortie-tour0.json
setsid nohup python3 $WEBAPP_PIPELINE_HOME/tools/webapp-tourner.py $W \
  > $W/video/.tournage/auto/sortie-tour0.json 2>> $W/video/.tournage/auto/console.log < /dev/null &
```

2. Attends-le **au premier plan**, par tranches de moins de 10 min (outil Bash, `timeout`
   600000), en répétant l'appel tant que la sortie est vide :

```bash
W=<ws>; for i in $(seq 55); do [ -s $W/video/.tournage/auto/sortie-tour0.json ] && break; sleep 10; done
tail -3 $W/video/.tournage/auto/journal.log; tail -1 $W/video/.tournage/auto/sortie-tour0.json
```

• Il dure de 15 min à plus d'une heure (un agent d'écriture par séquence, voix, répétition,
  prise, montage, publication). Ne le relance pas pendant qu'il tourne (il refuse un second
  lancement : verrou), ne le tue pas parce qu'il est long. Il applique lui-même `WEBAPP_LIMITEUR` : ne
  l'enveloppe pas.
• Une passe neuve qui trouve la phase `tournage` et un `webapp-tourner.py <ws>` vivant
  (`pgrep -f "webapp-tourner.py $W"`) ne relance rien : elle reprend l'attente du point 2.
• Mode retours : `--tour N` (et `--sequences s1,s3` seulement si tu dois forcer la liste), la
  sortie dans `sortie-tour<N>.json`.

## 3. Lire le résultat

La dernière ligne de la sortie est un JSON :
• `{"ok": true, "version": "V1", "url": "…", "sequences": [...], "refilmees": [...], …}` →
  contrôle `video/video-url.txt` (http(s), contient `code=`), `video/versions.json` (une entrée
  pour ce tour, versions consécutives), `video/video.mp4` présent.
• `{"ok": false, "erreur": "…"}` → lis `journal.log`. Une cause passagère (réseau, quota d'un
  agent d'écriture, délai) : relance UNE fois — le script reprend où il s'est arrêté (séquences
  déjà filmées gardées). Une cause qui tient à l'app (un geste du parcours ne trouve pas sa
  cible, écran blanc) : c'est un défaut de l'app — écris-le dans le journal, traite-le comme un
  écart (bâtisseur + vérificateur sur l'écran en cause, mise en production), puis relance.
  Deuxième échec : `avancement.json.bloque` = « tournage : <erreur> », rapport, sentinelle.

## 4. Clore

1. `avancement.json` : `phase: "fini"`, `jalon_courant: null`, `maj` (en mode retours, c'est
   4.3 §5 qui clôt).
2. `status.md` : une ligne `Vidéo V1 : <lien de video-url.txt>`.
3. Rapport de passe (version, séquences, durée, lien), sentinelle. Le contrôle du nœud passe
   au vert ; la revue se joue ensuite avec le client.

Ne recopie jamais le `code=` de la table de montage ailleurs que dans `video/video-url.txt` et
le rapport de passe : c'est la clé d'accès du client.
